from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserProfile
from .models import Exercise, CustomExercise, ExerciseNote


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


class GuestExerciseAccessTest(TestCase):
	"""Guest token access tests for exercise endpoints."""

	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username='guest_owner',
			email='guest_owner@example.com',
			password='password123'
		)
		UserProfile.objects.create(user=self.user, role='user')

		self.public_exercise = Exercise.objects.create(
			name='Burpee',
			category='gymnastics',
			equipment='bodyweight',
			primary_muscle_group='full_body',
			is_public=True,
			created_by=self.user
		)
		self.private_exercise = Exercise.objects.create(
			name='Secret Lift',
			category='weightlifting',
			equipment='barbell',
			primary_muscle_group='legs',
			is_public=False,
			created_by=self.user
		)

	def _guest_token(self):
		response = self.client.post('/api/users/auth/guest/', {}, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		return response.data['data']['access_token']

	def test_guest_list_public_only(self):
		token = self._guest_token()
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
		response = self.client.get('/api/wodtrackr/exercises/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		names = {item['name'] for item in response.data['data']}
		self.assertIn('Burpee', names)
		self.assertNotIn('Secret Lift', names)

	def test_guest_detail_public_ok(self):
		token = self._guest_token()
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
		response = self.client.get(f'/api/wodtrackr/exercises/{self.public_exercise.id}/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['data']['name'], 'Burpee')

	def test_guest_detail_private_forbidden(self):
		token = self._guest_token()
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
		response = self.client.get(f'/api/wodtrackr/exercises/{self.private_exercise.id}/')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_guest_cannot_create_exercise(self):
		token = self._guest_token()
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
		payload = {
			'name': 'Guest Created',
			'category': 'gymnastics',
			'equipment': 'bodyweight',
			'primary_muscle_group': 'full_body',
			'is_public': True
		}
		response = self.client.post('/api/wodtrackr/exercises/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_guest_invalid_token_rejected(self):
		self.client.credentials(HTTP_AUTHORIZATION='Bearer guest_invalid')
		response = self.client.get('/api/wodtrackr/exercises/')
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_guest_custom_exercises_forbidden(self):
		token = self._guest_token()
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
		response = self.client.get('/api/wodtrackr/custom-exercises/')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_guest_exercise_notes_forbidden(self):
		token = self._guest_token()
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
		response = self.client.get('/api/wodtrackr/exercise-notes/')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CustomExerciseAPITest(TestCase):
	"""Integration tests for custom exercise API endpoints."""

	def setUp(self):
		self.client = APIClient()

		self.user = User.objects.create_user(
			username='custom_user',
			email='custom_user@example.com',
			password='password123'
		)
		UserProfile.objects.create(user=self.user, role='user')

		self.user2 = User.objects.create_user(
			username='custom_user2',
			email='custom_user2@example.com',
			password='password123'
		)
		UserProfile.objects.create(user=self.user2, role='user')

		self.admin = User.objects.create_user(
			username='custom_admin',
			email='custom_admin@example.com',
			password='password123',
			is_staff=True
		)
		UserProfile.objects.create(user=self.admin, role='admin')

		self.custom_1 = CustomExercise.objects.create(
			created_by=self.user,
			title='Tempo Front Squat',
			category='weightlifting',
			equipment='barbell',
			primary_muscle_group='legs'
		)
		self.custom_2 = CustomExercise.objects.create(
			created_by=self.user2,
			title='Ring Rows - Pause',
			category='gymnastics',
			equipment='rings',
			primary_muscle_group='back'
		)

	def authenticate(self, user):
		refresh = RefreshToken.for_user(user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

	def test_list_requires_auth(self):
		response = self.client.get('/api/wodtrackr/custom-exercises/')
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_list_returns_only_owned_for_user(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/custom-exercises/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		titles = {item['title'] for item in response.data['data']}
		self.assertIn('Tempo Front Squat', titles)
		self.assertNotIn('Ring Rows - Pause', titles)

	def test_list_returns_all_for_admin(self):
		self.authenticate(self.admin)
		response = self.client.get('/api/wodtrackr/custom-exercises/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		titles = {item['title'] for item in response.data['data']}
		self.assertIn('Tempo Front Squat', titles)
		self.assertIn('Ring Rows - Pause', titles)

	def test_list_search_filter(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/custom-exercises/?search=tempo')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		titles = {item['title'] for item in response.data['data']}
		self.assertIn('Tempo Front Squat', titles)

	def test_create_custom_exercise_success(self):
		self.authenticate(self.user)
		payload = {
			'title': 'Paused Back Squat',
			'category': 'weightlifting',
			'equipment': 'barbell',
			'primary_muscle_group': 'legs',
			'description': 'Pause 2s at bottom'
		}
		response = self.client.post('/api/wodtrackr/custom-exercises/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['data']['title'], 'Paused Back Squat')

	def test_create_custom_exercise_invalid_title(self):
		self.authenticate(self.user)
		payload = {
			'title': 'A',
			'category': 'weightlifting',
			'equipment': 'barbell'
		}
		response = self.client.post('/api/wodtrackr/custom-exercises/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('title', response.data['detail'])

	def test_create_custom_exercise_duplicate_title_for_user(self):
		self.authenticate(self.user)
		payload = {
			'title': 'Tempo Front Squat',
			'category': 'weightlifting',
			'equipment': 'barbell'
		}
		response = self.client.post('/api/wodtrackr/custom-exercises/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_retrieve_not_owned_forbidden(self):
		self.authenticate(self.user)
		response = self.client.get(f'/api/wodtrackr/custom-exercises/{self.custom_2.id}/')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_update_owned_custom_exercise(self):
		self.authenticate(self.user)
		payload = {'description': 'Updated description'}
		response = self.client.put(f'/api/wodtrackr/custom-exercises/{self.custom_1.id}/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['data']['description'], 'Updated description')

	def test_delete_not_owned_forbidden(self):
		self.authenticate(self.user)
		response = self.client.delete(f'/api/wodtrackr/custom-exercises/{self.custom_2.id}/')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_admin_can_delete_any_custom_exercise(self):
		self.authenticate(self.admin)
		response = self.client.delete(f'/api/wodtrackr/custom-exercises/{self.custom_2.id}/')
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

	def test_invalid_category_filter(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/custom-exercises/?category=invalid')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_invalid_created_by_filter_for_non_admin(self):
		self.authenticate(self.user)
		response = self.client.get(f'/api/wodtrackr/custom-exercises/?created_by={self.user2.id}')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ExerciseNoteAPITest(TestCase):
	"""Integration tests for exercise note API endpoints."""

	def setUp(self):
		self.client = APIClient()

		self.user = User.objects.create_user(
			username='note_user',
			email='note_user@example.com',
			password='password123'
		)
		UserProfile.objects.create(user=self.user, role='user')

		self.user2 = User.objects.create_user(
			username='note_user2',
			email='note_user2@example.com',
			password='password123'
		)
		UserProfile.objects.create(user=self.user2, role='user')

		self.admin = User.objects.create_user(
			username='note_admin',
			email='note_admin@example.com',
			password='password123',
			is_staff=True
		)
		UserProfile.objects.create(user=self.admin, role='admin')

		self.public_exercise = Exercise.objects.create(
			name='Snatch',
			category='weightlifting',
			equipment='barbell',
			primary_muscle_group='legs',
			is_public=True,
			created_by=self.user
		)

		self.custom = CustomExercise.objects.create(
			created_by=self.user,
			title='Tempo Snatch Pull',
			category='weightlifting',
			equipment='barbell',
			primary_muscle_group='legs'
		)

		self.public_exercise_2 = Exercise.objects.create(
			name='Clean',
			category='weightlifting',
			equipment='barbell',
			primary_muscle_group='legs',
			is_public=True,
			created_by=self.user
		)

		self.custom_2 = CustomExercise.objects.create(
			created_by=self.user,
			title='Deficit Snatch Pull',
			category='weightlifting',
			equipment='barbell',
			primary_muscle_group='legs'
		)

		self.note_public = ExerciseNote.objects.create(
			user=self.user,
			exercise=self.public_exercise,
			notes='Keep bar close'
		)
		self.note_custom = ExerciseNote.objects.create(
			user=self.user,
			custom_exercise=self.custom,
			notes='3s tempo'
		)

	def authenticate(self, user):
		refresh = RefreshToken.for_user(user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

	def test_list_requires_auth(self):
		response = self.client.get('/api/wodtrackr/exercise-notes/')
		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_list_returns_only_owned_for_user(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/exercise-notes/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		ids = {item['id'] for item in response.data['data']}
		self.assertIn(self.note_public.id, ids)
		self.assertIn(self.note_custom.id, ids)

	def test_list_returns_all_for_admin(self):
		ExerciseNote.objects.create(
			user=self.user2,
			exercise=self.public_exercise,
			notes='Different note'
		)
		self.authenticate(self.admin)
		response = self.client.get('/api/wodtrackr/exercise-notes/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertGreaterEqual(len(response.data['data']), 3)

	def test_list_filter_target_custom(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/exercise-notes/?target=custom_exercise')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data['data']), 1)
		self.assertEqual(response.data['data'][0]['id'], self.note_custom.id)

	def test_list_filter_search(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/exercise-notes/?search=tempo')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		ids = {item['id'] for item in response.data['data']}
		self.assertIn(self.note_custom.id, ids)

	def test_create_note_for_exercise(self):
		self.authenticate(self.user)
		payload = {'exercise': self.public_exercise_2.id, 'notes': 'Fast turnover'}
		response = self.client.post('/api/wodtrackr/exercise-notes/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

	def test_create_note_for_custom_exercise(self):
		self.authenticate(self.user)
		payload = {'custom_exercise': self.custom_2.id, 'notes': 'Keep tempo'}
		response = self.client.post('/api/wodtrackr/exercise-notes/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)

	def test_create_note_invalid_missing_target(self):
		self.authenticate(self.user)
		payload = {'notes': 'No target'}
		response = self.client.post('/api/wodtrackr/exercise-notes/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_create_note_invalid_both_targets(self):
		self.authenticate(self.user)
		payload = {
			'exercise': self.public_exercise.id,
			'custom_exercise': self.custom.id,
			'notes': 'Both targets'
		}
		response = self.client.post('/api/wodtrackr/exercise-notes/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_create_note_duplicate(self):
		self.authenticate(self.user)
		payload = {'exercise': self.public_exercise.id, 'notes': 'Duplicate'}
		response = self.client.post('/api/wodtrackr/exercise-notes/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_update_note_owned(self):
		self.authenticate(self.user)
		payload = {'notes': 'Updated note'}
		response = self.client.put(f'/api/wodtrackr/exercise-notes/{self.note_public.id}/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['data']['notes'], 'Updated note')

	def test_update_note_not_owned_forbidden(self):
		self.authenticate(self.user2)
		payload = {'notes': 'Attempt update'}
		response = self.client.put(f'/api/wodtrackr/exercise-notes/{self.note_public.id}/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_delete_note_not_owned_forbidden(self):
		self.authenticate(self.user2)
		response = self.client.delete(f'/api/wodtrackr/exercise-notes/{self.note_public.id}/')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_admin_can_delete_any_note(self):
		self.authenticate(self.admin)
		response = self.client.delete(f'/api/wodtrackr/exercise-notes/{self.note_public.id}/')
		self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

	def test_invalid_filter_combination(self):
		self.authenticate(self.user)
		response = self.client.get(
			f'/api/wodtrackr/exercise-notes/?exercise_id={self.public_exercise.id}&custom_exercise_id={self.custom.id}'
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_invalid_target_filter(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/exercise-notes/?target=invalid')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_invalid_date_filter(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/exercise-notes/?created_from=bad-date')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
