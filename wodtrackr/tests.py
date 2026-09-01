from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserProfile
from .models import Exercise, ExerciseProgram, ExerciseProgramItem


class ExerciseApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='password123',
        )
        UserProfile.objects.create(user=self.user, role='user')

        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@example.com',
            password='password123',
        )
        UserProfile.objects.create(user=self.user2, role='user')

        self.admin = User.objects.create_user(
            username='admin1',
            email='admin1@example.com',
            password='password123',
            is_staff=True,
        )
        UserProfile.objects.create(user=self.admin, role='admin')

        self.public_exercise = Exercise.objects.create(
            name='Back Squat',
            category='upper legs',
            body_part='upper legs',
            equipment='barbell',
            muscle_group='quadriceps',
            target_muscle='quadriceps',
            image_url='/media/exercise_dataset/images/0001-2gPfomN.jpg',
            gif_url='/media/exercise_dataset/videos/0001-2gPfomN.gif',
            is_public=True,
            created_by=self.user,
        )
        self.private_exercise = Exercise.objects.create(
            name='Strict Press',
            category='shoulders',
            body_part='shoulders',
            equipment='barbell',
            muscle_group='deltoids',
            target_muscle='deltoids',
            is_public=False,
            created_by=self.user,
        )
        self.other_public = Exercise.objects.create(
            name='Double Unders',
            category='cardio',
            body_part='cardio',
            equipment='jump rope',
            muscle_group='cardiovascular system',
            target_muscle='calves',
            is_public=True,
            created_by=self.user2,
        )

    def _authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_list_requires_auth_or_guest_session(self):
        response = self.client.get('/api/wodtrackr/exercises/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_includes_public_and_own_for_authenticated_user(self):
        self._authenticate(self.user)
        response = self.client.get('/api/wodtrackr/exercises/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        names = {item['name'] for item in response.data['data']}
        self.assertIn('Back Squat', names)
        self.assertIn('Strict Press', names)
        self.assertIn('Double Unders', names)

    def test_create_supports_legacy_title_alias(self):
        self._authenticate(self.user)
        payload = {
            'title': 'Handstand Push-up',
            'category': 'shoulders',
            'body_part': 'shoulders',
            'equipment': 'body weight',
            'primary_muscle_group': 'deltoids',
            'target': 'deltoids',
            'is_public': True,
        }
        response = self.client.post('/api/wodtrackr/exercises/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['name'], 'Handstand Push-up')
        self.assertEqual(response.data['data']['title'], 'Handstand Push-up')
        self.assertEqual(response.data['data']['muscle_group'], 'deltoids')

    def test_detail_includes_absolute_media_urls(self):
        self._authenticate(self.user)
        response = self.client.get(f'/api/wodtrackr/exercises/{self.public_exercise.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['image_url'], '/media/exercise_dataset/images/0001-2gPfomN.jpg')
        self.assertTrue(response.data['data']['resolved_image_url'].startswith('http://testserver/media/'))
        self.assertTrue(response.data['data']['gif_absolute_url'].startswith('http://testserver/media/'))

    def test_detail_private_not_owned_forbidden(self):
        self._authenticate(self.user2)
        response = self.client.get(f'/api/wodtrackr/exercises/{self.private_exercise.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_with_seeded_image_url_returns_resolved_image_url(self):
        self._authenticate(self.user)

        payload = {
            'name': 'Rower Sprint',
            'category': 'cardio',
            'body_part': 'full body',
            'equipment': 'rower',
            'muscle_group': 'cardiovascular system',
            'target_muscle': 'cardiovascular system',
            'image_url': 'https://cdn.example.com/rower.jpg',
            'gif_url': 'https://cdn.example.com/rower.gif',
            'is_public': True,
        }

        response = self.client.post('/api/wodtrackr/exercises/', payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['image_url'], 'https://cdn.example.com/rower.jpg')
        self.assertEqual(response.data['data']['resolved_image_url'], 'https://cdn.example.com/rower.jpg')
        self.assertEqual(response.data['data']['gif_absolute_url'], 'https://cdn.example.com/rower.gif')

    def test_create_with_uploaded_image_prefers_upload_for_resolved_image_url(self):
        self._authenticate(self.user)

        image_file = SimpleUploadedFile(
            'rower.png',
            (
                b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde'
                b'\x00\x00\x00\x0cIDATx\x9cc\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef\x00\x00\x00\x00IEND\xaeB`\x82'
            ),
            content_type='image/png',
        )

        payload = {
            'name': 'Rower Sprint Upload',
            'category': 'cardio',
            'body_part': 'full body',
            'equipment': 'rower',
            'muscle_group': 'cardiovascular system',
            'target_muscle': 'cardiovascular system',
            'image_url': 'https://cdn.example.com/seeded.jpg',
            'image_upload': image_file,
            'is_public': True,
        }

        response = self.client.post('/api/wodtrackr/exercises/', payload, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['image_url'], 'https://cdn.example.com/seeded.jpg')
        self.assertTrue(response.data['data']['image_upload'].startswith('http://testserver/media/exercise_dataset/images/'))
        self.assertTrue(response.data['data']['resolved_image_url'].startswith('http://testserver/media/exercise_dataset/images/'))

    def test_admin_can_delete_private_exercise(self):
        self._authenticate(self.admin)
        response = self.client.delete(f'/api/wodtrackr/exercises/{self.private_exercise.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ExerciseProgramApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='program_owner',
            email='program_owner@example.com',
            password='password123',
        )
        UserProfile.objects.create(user=self.user, role='user')

        self.user2 = User.objects.create_user(
            username='program_other',
            email='program_other@example.com',
            password='password123',
        )
        UserProfile.objects.create(user=self.user2, role='user')

        self.exercise_1 = Exercise.objects.create(
            name='Bench Press',
            category='chest',
            body_part='chest',
            equipment='barbell',
            muscle_group='pectorals',
            target_muscle='pectorals',
            is_public=True,
            created_by=self.user,
        )
        self.exercise_2 = Exercise.objects.create(
            name='Romanian Deadlift',
            category='upper legs',
            body_part='upper legs',
            equipment='barbell',
            muscle_group='hamstrings',
            target_muscle='hamstrings',
            is_public=True,
            created_by=self.user,
        )

    def _authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

    def test_create_program_with_items_syncs_exercise_relation(self):
        self._authenticate(self.user)
        payload = {
            'name': 'Upper Body Strength',
            'description': 'Simple upper body progression.',
            'difficulty': 'beginner',
            'duration_weeks': 4,
            'is_public': False,
            'items': [
                {'exercise': self.exercise_1.id, 'position': 1, 'sets': 4, 'reps': '6-8'},
                {'exercise': self.exercise_2.id, 'position': 2, 'sets': 3, 'reps': '8-10'},
            ],
        }

        response = self.client.post('/api/wodtrackr/exercise-programs/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        program_id = response.data['data']['id']
        program = ExerciseProgram.objects.get(id=program_id)
        related_ids = set(program.exercises.values_list('id', flat=True))

        self.assertEqual(related_ids, {self.exercise_1.id, self.exercise_2.id})
        self.assertEqual(program.items.count(), 2)

    def test_program_visibility_enforced(self):
        program = ExerciseProgram.objects.create(
            created_by=self.user,
            name='Private Program',
            description='Hidden',
            difficulty='beginner',
            duration_weeks=4,
            is_public=False,
            program_image='exercise_program_images/test.jpg',
        )
        ExerciseProgramItem.objects.create(program=program, exercise=self.exercise_1, position=1)

        self._authenticate(self.user2)
        response = self.client.get(f'/api/wodtrackr/exercise-programs/{program.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
