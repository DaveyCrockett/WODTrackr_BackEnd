from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserProfile
from .models import Exercise


class ExerciseAPITest(TestCase):
	"""Integration tests for exercise API endpoints."""

	def setUp(self):
		self.client = APIClient()

		self.user = User.objects.create_user(
			username='user1',
			email='user1@example.com',
			password='password123'
		)
		UserProfile.objects.create(user=self.user, role='user')

		self.user2 = User.objects.create_user(
			username='user2',
			email='user2@example.com',
			password='password123'
		)
		UserProfile.objects.create(user=self.user2, role='user')

		self.admin = User.objects.create_user(
			username='adminuser',
			email='admin@example.com',
			password='password123',
			is_staff=True
		)
		UserProfile.objects.create(user=self.admin, role='admin')

		self.public_exercise = Exercise.objects.create(
			name='Back Squat',
			category='weightlifting',
			equipment='barbell',
			primary_muscle_group='legs',
			is_public=True,
			created_by=self.user
		)
		self.private_exercise = Exercise.objects.create(
			name='Strict Press',
			category='weightlifting',
			equipment='barbell',
			primary_muscle_group='shoulders',
			is_public=False,
			created_by=self.user
		)
		self.other_public = Exercise.objects.create(
			name='Double Unders',
			category='monostructural',
			equipment='jump_rope',
			primary_muscle_group='cardio',
			is_public=True,
			created_by=self.user2
		)

	def authenticate(self, user):
		refresh = RefreshToken.for_user(user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

	def test_list_requires_auth(self):
		response = self.client.get('/api/wodtrackr/exercises/')
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_list_includes_public_and_own(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/exercises/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		names = {item['name'] for item in response.data['data']}
		self.assertIn('Back Squat', names)
		self.assertIn('Strict Press', names)
		self.assertIn('Double Unders', names)

	def test_list_filters_mine(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/exercises/?mine=true')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		names = {item['name'] for item in response.data['data']}
		self.assertIn('Back Squat', names)
		self.assertIn('Strict Press', names)
		self.assertNotIn('Double Unders', names)

	def test_list_search_filter(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/exercises/?search=unders')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		names = {item['name'] for item in response.data['data']}
		self.assertIn('Double Unders', names)
		self.assertNotIn('Back Squat', names)

	def test_create_exercise_success(self):
		self.authenticate(self.user)
		payload = {
			'name': 'Handstand Push-up',
			'category': 'gymnastics',
			'equipment': 'bodyweight',
			'primary_muscle_group': 'shoulders',
			'is_public': True
		}
		response = self.client.post('/api/wodtrackr/exercises/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['data']['name'], 'Handstand Push-up')

	def test_create_exercise_invalid_name(self):
		self.authenticate(self.user)
		payload = {
			'name': 'A',
			'category': 'gymnastics',
			'equipment': 'bodyweight'
		}
		response = self.client.post('/api/wodtrackr/exercises/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('name', response.data['detail'])

	def test_create_exercise_duplicate_name(self):
		self.authenticate(self.user)
		payload = {
			'name': 'Back Squat',
			'category': 'weightlifting',
			'equipment': 'barbell'
		}
		response = self.client.post('/api/wodtrackr/exercises/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_retrieve_private_not_owned_forbidden(self):
		self.authenticate(self.user2)
		response = self.client.get(f'/api/wodtrackr/exercises/{self.private_exercise.id}/')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_update_owned_exercise(self):
		self.authenticate(self.user)
		payload = {'description': 'Updated description'}
		response = self.client.put(f'/api/wodtrackr/exercises/{self.public_exercise.id}/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['data']['description'], 'Updated description')

	def test_update_not_owned_forbidden(self):
		self.authenticate(self.user2)
		payload = {'description': 'Attempt update'}
		response = self.client.put(f'/api/wodtrackr/exercises/{self.public_exercise.id}/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_delete_not_owned_forbidden(self):
		self.authenticate(self.user2)
		response = self.client.delete(f'/api/wodtrackr/exercises/{self.public_exercise.id}/')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_admin_can_delete_any(self):
		self.authenticate(self.admin)
		response = self.client.delete(f'/api/wodtrackr/exercises/{self.private_exercise.id}/')
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
