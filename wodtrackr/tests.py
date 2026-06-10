import tempfile

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserProfile
from .models import Exercise, CustomExercise, ExerciseNote, ExerciseProgram, ExerciseProgramItem, Equipment


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


class ExerciseProgramModelTest(TestCase):
	"""Model tests for exercise programs."""

	def setUp(self):
		self.user = User.objects.create_user(
			username='program_user',
			email='program_user@example.com',
			password='password123'
		)
		self.exercise = Exercise.objects.create(
			name='Thruster',
			category='weightlifting',
			equipment='barbell',
			primary_muscle_group='legs',
			is_public=True,
			created_by=self.user
		)
		self.custom_exercise = CustomExercise.objects.create(
			created_by=self.user,
			name='Paused Thruster',
			category='weightlifting',
			equipment='barbell',
			primary_muscle_group='legs'
		)

	def test_program_can_be_created_and_shared(self):
		program = ExerciseProgram.objects.create(
			created_by=self.user,
			name='Strength Cycle',
			description='Four-week barbell progression.',
			is_public=True
		)

		self.assertEqual(program.created_by, self.user)
		self.assertTrue(program.is_public)

	def test_program_item_requires_single_target(self):
		program = ExerciseProgram.objects.create(created_by=self.user, name='Open Prep')

		with transaction.atomic():
			with self.assertRaises(IntegrityError):
				ExerciseProgramItem.objects.create(program=program, position=1)

		with transaction.atomic():
			with self.assertRaises(IntegrityError):
				ExerciseProgramItem.objects.create(
					program=program,
					position=1,
					exercise=self.exercise,
					custom_exercise=self.custom_exercise
				)

	def test_program_item_position_must_be_unique_per_program(self):
		program = ExerciseProgram.objects.create(created_by=self.user, name='Competition Prep')
		ExerciseProgramItem.objects.create(program=program, position=1, exercise=self.exercise)

		with transaction.atomic():
			with self.assertRaises(IntegrityError):
				ExerciseProgramItem.objects.create(program=program, position=1, custom_exercise=self.custom_exercise)


class ExerciseProgramAPITest(TestCase):
	"""Integration tests for exercise program endpoints."""

	def setUp(self):
		self.client = APIClient()

		self.user = User.objects.create_user(
			username='program_api_user',
			email='program_api_user@example.com',
			password='password123'
		)
		UserProfile.objects.create(user=self.user, role='user')

		self.user2 = User.objects.create_user(
			username='program_api_user2',
			email='program_api_user2@example.com',
			password='password123'
		)
		UserProfile.objects.create(user=self.user2, role='user')

		self.admin = User.objects.create_user(
			username='program_api_admin',
			email='program_api_admin@example.com',
			password='password123',
			is_staff=True
		)
		UserProfile.objects.create(user=self.admin, role='admin')

		self.public_exercise = Exercise.objects.create(
			name='Deadlift',
			category='powerlifting',
			equipment='barbell',
			primary_muscle_group='back',
			is_public=True,
			created_by=self.user
		)

		self.private_exercise = Exercise.objects.create(
			name='Tempo Deadlift',
			category='powerlifting',
			equipment='barbell',
			primary_muscle_group='back',
			is_public=False,
			created_by=self.user2
		)

		self.custom_exercise = CustomExercise.objects.create(
			created_by=self.user,
			name='Deficit Deadlift',
			category='powerlifting',
			equipment='barbell',
			primary_muscle_group='back'
		)

		self.eq_barbell, _ = Equipment.objects.get_or_create(equipment='barbell')
		self.eq_dumbbell, _ = Equipment.objects.get_or_create(equipment='dumbbell')

		self.other_custom_exercise = CustomExercise.objects.create(
			created_by=self.user2,
			name='Paused Deadlift',
			category='powerlifting',
			equipment='barbell',
			primary_muscle_group='back'
		)

		self.public_program = ExerciseProgram.objects.create(
			created_by=self.user2,
			name='Back Builder',
			description='Posterior chain program.',
			is_public=True
		)
		ExerciseProgramItem.objects.create(program=self.public_program, exercise=self.public_exercise, position=1)

		self.private_program = ExerciseProgram.objects.create(
			created_by=self.user2,
			name='Private Builder',
			description='Private work.',
			is_public=False
		)
		ExerciseProgramItem.objects.create(program=self.private_program, exercise=self.private_exercise, position=1)

		self.owned_program = ExerciseProgram.objects.create(
			created_by=self.user,
			name='My Pull Cycle',
			description='My own cycle.',
			is_public=False
		)
		ExerciseProgramItem.objects.create(program=self.owned_program, custom_exercise=self.custom_exercise, position=1)

	def authenticate(self, user):
		refresh = RefreshToken.for_user(user)
		self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

	def test_list_includes_public_and_owned_programs(self):
		self.authenticate(self.user)
		response = self.client.get('/api/wodtrackr/exercise-programs/')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		names = {item['name'] for item in response.data['data']}
		self.assertIn('Back Builder', names)
		self.assertIn('My Pull Cycle', names)
		self.assertNotIn('Private Builder', names)

	def test_create_program_with_items_success(self):
		self.authenticate(self.user)
		payload = {
			'name': 'Open Prep',
			'description': 'Competition prep block.',
			'is_public': True,
			'items': [
				{'exercise': self.public_exercise.id, 'position': 1, 'week': 1, 'day': 1, 'sets': 5, 'reps': '3', 'load': '80%', 'rest_seconds': 120, 'notes': 'Heavy triples'},
				{'custom_exercise': self.custom_exercise.id, 'position': 2, 'week': 1, 'day': 2, 'sets': 4, 'reps': '8', 'load': 'RPE 7', 'rest_seconds': 90, 'notes': 'Accessory volume'}
			]
		}
		response = self.client.post('/api/wodtrackr/exercise-programs/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(len(response.data['data']['items']), 2)
		self.assertEqual(response.data['data']['created_by'], self.user.id)
		self.assertEqual(response.data['data']['items'][0]['week'], 1)
		self.assertEqual(response.data['data']['items'][0]['day'], 1)
		self.assertEqual(response.data['data']['items'][0]['sets'], 5)
		self.assertEqual(response.data['data']['items'][0]['reps'], '3')
		self.assertEqual(response.data['data']['items'][0]['load'], '80%')
		self.assertEqual(response.data['data']['items'][0]['rest_seconds'], 120)

	def test_create_program_rejects_inaccessible_targets(self):
		self.authenticate(self.user)
		payload = {
			'name': 'Invalid Program',
			'items': [
				{'exercise': self.private_exercise.id, 'position': 1},
				{'custom_exercise': self.other_custom_exercise.id, 'position': 2}
			]
		}
		response = self.client.post('/api/wodtrackr/exercise-programs/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('items', response.data['detail'])

	def test_update_owned_program_replaces_items(self):
		self.authenticate(self.user)
		payload = {
			'name': 'My Pull Cycle Updated',
			'items': [
				{'exercise': self.public_exercise.id, 'position': 1, 'week': 2, 'day': 3, 'sets': 1, 'reps': '1+', 'load': '90%', 'rest_seconds': 180, 'notes': 'Top set'}
			]
		}
		response = self.client.put(f'/api/wodtrackr/exercise-programs/{self.owned_program.id}/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['data']['name'], 'My Pull Cycle Updated')
		self.assertEqual(len(response.data['data']['items']), 1)
		self.assertEqual(response.data['data']['items'][0]['exercise'], self.public_exercise.id)
		self.assertEqual(response.data['data']['items'][0]['week'], 2)
		self.assertEqual(response.data['data']['items'][0]['day'], 3)
		self.assertEqual(response.data['data']['items'][0]['sets'], 1)
		self.assertEqual(response.data['data']['items'][0]['reps'], '1+')
		self.assertEqual(response.data['data']['items'][0]['load'], '90%')
		self.assertEqual(response.data['data']['items'][0]['rest_seconds'], 180)

	def test_update_owned_program_accepts_equipment_and_item_aliases(self):
		self.authenticate(self.user)
		payload = {
			'equipment': [self.eq_barbell.id, self.eq_dumbbell.id],
			'item': [
				{'exercise': self.public_exercise.id, 'position': 1, 'week': 2, 'day': 4, 'sets': 3, 'reps': '5'}
			]
		}
		response = self.client.put(f'/api/wodtrackr/exercise-programs/{self.owned_program.id}/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['data']['equipment'], ['barbell', 'dumbbell'])
		self.assertEqual(len(response.data['data']['items']), 1)
		self.assertEqual(response.data['data']['items'][0]['exercise'], self.public_exercise.id)
		self.assertEqual(response.data['data']['items'][0]['week'], 2)
		self.assertEqual(response.data['data']['items'][0]['day'], 4)

	def test_patch_owned_program_partially_updates_without_replacing_items(self):
		self.authenticate(self.user)
		payload = {
			'description': 'Updated description via PATCH'
		}
		response = self.client.patch(f'/api/wodtrackr/exercise-programs/{self.owned_program.id}/', payload, format='json')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['data']['description'], 'Updated description via PATCH')
		self.assertEqual(response.data['data']['name'], 'My Pull Cycle')
		self.assertEqual(len(response.data['data']['items']), 1)
		self.assertEqual(response.data['data']['items'][0]['custom_exercise'], self.custom_exercise.id)

	def test_patch_owned_program_accepts_program_image(self):
		self.authenticate(self.user)
		image_bytes = (
			b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,'
			b'\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
		)
		upload = SimpleUploadedFile('program.gif', image_bytes, content_type='image/gif')

		with tempfile.TemporaryDirectory() as temp_media_root:
			with override_settings(MEDIA_ROOT=temp_media_root):
				response = self.client.patch(
					f'/api/wodtrackr/exercise-programs/{self.owned_program.id}/',
					{'program_image': upload},
					format='multipart'
				)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('exercise_program_images/', response.data['data']['program_image'])
		self.owned_program.refresh_from_db()
		self.assertTrue(self.owned_program.program_image.name.startswith('exercise_program_images/'))

	def test_list_filters_by_exercise_id(self):
		self.authenticate(self.user)
		response = self.client.get(f'/api/wodtrackr/exercise-programs/?exercise_id={self.public_exercise.id}')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		names = {item['name'] for item in response.data['data']}
		self.assertIn('Back Builder', names)
		self.assertNotIn('My Pull Cycle', names)

	def test_list_filters_by_custom_exercise_id(self):
		self.authenticate(self.user)
		response = self.client.get(f'/api/wodtrackr/exercise-programs/?custom_exercise_id={self.custom_exercise.id}')
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		names = {item['name'] for item in response.data['data']}
		self.assertIn('My Pull Cycle', names)
		self.assertNotIn('Back Builder', names)

	def test_list_rejects_both_program_target_filters(self):
		self.authenticate(self.user)
		response = self.client.get(
			f'/api/wodtrackr/exercise-programs/?exercise_id={self.public_exercise.id}&custom_exercise_id={self.custom_exercise.id}'
		)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_reuse_public_program_success(self):
		self.authenticate(self.user)
		response = self.client.post(f'/api/wodtrackr/exercise-programs/{self.public_program.id}/reuse/', {}, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data['data']['created_by'], self.user.id)
		self.assertFalse(response.data['data']['is_public'])
		self.assertEqual(len(response.data['data']['items']), 1)
		self.assertEqual(response.data['data']['items'][0]['exercise'], self.public_exercise.id)

	def test_reuse_private_program_forbidden(self):
		self.authenticate(self.user)
		response = self.client.post(f'/api/wodtrackr/exercise-programs/{self.private_program.id}/reuse/', {}, format='json')
		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
