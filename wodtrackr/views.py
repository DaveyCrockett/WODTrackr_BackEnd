from datetime import datetime

from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Exercise, CustomExercise, ExerciseNote, ExerciseProgram, ExerciseProgramItem
from .permissions import ExercisePermission, CustomExercisePermission, ExerciseNotePermission, ExerciseProgramPermission
from .serializers import ExerciseSerializer, CustomExerciseSerializer, ExerciseNoteSerializer, ExerciseProgramSerializer


def _can_manage_exercise(user, exercise):
	return user.is_staff or exercise.created_by == user


def _can_manage_program(user, program):
	return user.is_staff or program.created_by == user


def _can_view_program(user, program):
	return user.is_staff or program.is_public or program.created_by == user


def _build_reused_program_name(user, base_name):
	candidate = f'{base_name} Copy'
	suffix = 2
	while ExerciseProgram.objects.filter(created_by=user, name__iexact=candidate).exists():
		candidate = f'{base_name} Copy {suffix}'
		suffix += 1
	return candidate


def _validate_choice_param(value, allowed_values, field_name):
	if value and value not in allowed_values:
		return Response(
			{
				'error': 'Invalid query parameter',
				'detail': {field_name: [f"Invalid value '{value}'."]}
			},
			status=status.HTTP_400_BAD_REQUEST
		)
	return None


def _validate_date_param(value, field_name):
	if not value:
		return None
	try:
		return datetime.fromisoformat(value.replace('Z', '+00:00'))
	except ValueError:
		return Response(
			{
				'error': 'Invalid query parameter',
				'detail': {field_name: ['Must be an ISO 8601 datetime.']}
			},
			status=status.HTTP_400_BAD_REQUEST
		)


@api_view(['GET'])
@permission_classes([AllowAny])
def exercise_choices(request):
	"""
	Return available choices for exercise fields.
	"""
	return Response({
		'category': [{'value': k, 'label': v} for k, v in Exercise.CATEGORY_CHOICES],
		'equipment': [{'value': k, 'label': v} for k, v in Exercise.EQUIPMENT_CHOICES],
		'primary_muscle_group': [{'value': k, 'label': v} for k, v in Exercise.Primary_Muscle_Choices],
	}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([ExercisePermission])
def exercises(request):
	"""
	List exercises or create a new exercise.
	"""
	if request.method == 'GET':
		if request.user and request.user.is_authenticated:
			queryset = Exercise.objects.filter(
				Q(is_public=True) | Q(created_by=request.user)
			)
		else:
			queryset = Exercise.objects.filter(is_public=True)

		search = request.query_params.get('search', '').strip()
		category = request.query_params.get('category', '').strip()
		equipment = request.query_params.get('equipment', '').strip()
		muscle = request.query_params.get('muscle', '').strip()
		is_public = request.query_params.get('is_public', '').strip()
		mine = request.query_params.get('mine', '').strip()
		ordering = request.query_params.get('ordering', '').strip()

		if search:
			queryset = queryset.filter(
				Q(name__icontains=search) |
				Q(description__icontains=search) |
				Q(primary_muscle_group__icontains=search)
			)
		if category:
			error = _validate_choice_param(category, dict(Exercise.CATEGORY_CHOICES).keys(), 'category')
			if error:
				return error
			queryset = queryset.filter(category=category)
		if equipment:
			error = _validate_choice_param(equipment, dict(Exercise.EQUIPMENT_CHOICES).keys(), 'equipment')
			if error:
				return error
			queryset = queryset.filter(equipment=equipment)
		if muscle:
			queryset = queryset.filter(primary_muscle_group__icontains=muscle)
		if is_public:
			if is_public.lower() in ['true', 'false']:
				queryset = queryset.filter(is_public=is_public.lower() == 'true')
			else:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'is_public': ['Must be true or false.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
		if mine:
			if mine.lower() in ['true', 'false']:
				if mine.lower() == 'true':
					if request.user and request.user.is_authenticated:
						queryset = queryset.filter(created_by=request.user)
					else:
						queryset = queryset.none()
				else:
					queryset = queryset.filter(is_public=True)
			else:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'mine': ['Must be true or false.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)

		allowed_ordering = ['name', '-name', 'created_at', '-created_at', 'updated_at', '-updated_at']
		if ordering in allowed_ordering:
			queryset = queryset.order_by(ordering)
		else:
			queryset = queryset.order_by('name')

		serializer = ExerciseSerializer(queryset, many=True)
		return Response({'data': serializer.data}, status=status.HTTP_200_OK)

	serializer = ExerciseSerializer(data=request.data)
	if serializer.is_valid():
		try:
			exercise = serializer.save(created_by=request.user)
			return Response(
				{
					'message': 'Exercise created successfully',
					'data': ExerciseSerializer(exercise).data
				},
				status=status.HTTP_201_CREATED
			)
		except IntegrityError:
			return Response(
				{
					'error': 'Invalid exercise data',
					'detail': {'name': ['An exercise with this name already exists.']}
				},
				status=status.HTTP_400_BAD_REQUEST
			)
	return Response(
		{
			'error': 'Invalid exercise data',
			'detail': serializer.errors
		},
		status=status.HTTP_400_BAD_REQUEST
	)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([ExercisePermission])
def exercise_detail(request, exercise_id):
	"""
	Retrieve, update, or delete an exercise.
	"""
	try:
		exercise = Exercise.objects.get(id=exercise_id)
	except Exercise.DoesNotExist:
		return Response(
			{
				'error': 'Exercise not found'
			},
			status=status.HTTP_404_NOT_FOUND
		)

	if request.method == 'GET':
		if request.user and request.user.is_authenticated:
			can_view = exercise.is_public or _can_manage_exercise(request.user, exercise)
		else:
			can_view = exercise.is_public
		if not can_view:
			return Response(
				{'error': 'Forbidden'},
				status=status.HTTP_403_FORBIDDEN
			)
		serializer = ExerciseSerializer(exercise)
		return Response({'data': serializer.data}, status=status.HTTP_200_OK)

	if not _can_manage_exercise(request.user, exercise):
		return Response(
			{'error': 'Forbidden'},
			status=status.HTTP_403_FORBIDDEN
		)

	if request.method == 'PUT':
		serializer = ExerciseSerializer(exercise, data=request.data, partial=True)
		if serializer.is_valid():
			try:
				serializer.save()
				return Response(
					{
						'message': 'Exercise updated successfully',
						'data': serializer.data
					},
					status=status.HTTP_200_OK
				)
			except IntegrityError:
				return Response(
					{
						'error': 'Invalid exercise data',
						'detail': {'name': ['An exercise with this name already exists.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
		return Response(
			{
				'error': 'Invalid exercise data',
				'detail': serializer.errors
			},
			status=status.HTTP_400_BAD_REQUEST
		)

	exercise.delete()
	return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([CustomExercisePermission])
def custom_exercises(request):
	"""
	List custom exercises or create a new custom exercise.
	"""
	if request.method == 'GET':
		if request.user.is_staff:
			queryset = CustomExercise.objects.all()
		else:
			queryset = CustomExercise.objects.filter(created_by=request.user)

		queryset = queryset.select_related('created_by')

		search = request.query_params.get('search', '').strip()
		category = request.query_params.get('category', '').strip()
		equipment = request.query_params.get('equipment', '').strip()
		muscle = request.query_params.get('muscle', '').strip()
		ordering = request.query_params.get('ordering', '').strip()
		created_by = request.query_params.get('created_by', '').strip()
		created_from = request.query_params.get('created_from', '').strip()
		created_to = request.query_params.get('created_to', '').strip()
		updated_from = request.query_params.get('updated_from', '').strip()
		updated_to = request.query_params.get('updated_to', '').strip()

		if search:
			queryset = queryset.filter(
				Q(title__icontains=search) |
				Q(description__icontains=search) |
				Q(primary_muscle_group__icontains=search)
			)
		if category:
			error = _validate_choice_param(category, dict(CustomExercise.CATEGORY_CHOICES).keys(), 'category')
			if error:
				return error
			queryset = queryset.filter(category=category)
		if equipment:
			error = _validate_choice_param(equipment, dict(CustomExercise.EQUIPMENT_CHOICES).keys(), 'equipment')
			if error:
				return error
			queryset = queryset.filter(equipment=equipment)
		if muscle:
			queryset = queryset.filter(primary_muscle_group__icontains=muscle)
		if created_by:
			if not request.user.is_staff:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'created_by': ['Forbidden.']}
					},
					status=status.HTTP_403_FORBIDDEN
				)
			try:
				created_by_id = int(created_by)
			except ValueError:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'created_by': ['Must be an integer.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
			queryset = queryset.filter(created_by_id=created_by_id)

		created_from_dt = _validate_date_param(created_from, 'created_from')
		if isinstance(created_from_dt, Response):
			return created_from_dt
		if created_from_dt:
			queryset = queryset.filter(created_at__gte=created_from_dt)

		created_to_dt = _validate_date_param(created_to, 'created_to')
		if isinstance(created_to_dt, Response):
			return created_to_dt
		if created_to_dt:
			queryset = queryset.filter(created_at__lte=created_to_dt)

		updated_from_dt = _validate_date_param(updated_from, 'updated_from')
		if isinstance(updated_from_dt, Response):
			return updated_from_dt
		if updated_from_dt:
			queryset = queryset.filter(updated_at__gte=updated_from_dt)

		updated_to_dt = _validate_date_param(updated_to, 'updated_to')
		if isinstance(updated_to_dt, Response):
			return updated_to_dt
		if updated_to_dt:
			queryset = queryset.filter(updated_at__lte=updated_to_dt)

		allowed_ordering = ['title', '-title', 'created_at', '-created_at', 'updated_at', '-updated_at']
		if ordering in allowed_ordering:
			queryset = queryset.order_by(ordering)
		else:
			queryset = queryset.order_by('title')

		serializer = CustomExerciseSerializer(queryset, many=True)
		return Response({'data': serializer.data}, status=status.HTTP_200_OK)

	serializer = CustomExerciseSerializer(data=request.data)
	if serializer.is_valid():
		try:
			custom_exercise = serializer.save(created_by=request.user)
			return Response(
				{
					'message': 'Custom exercise created successfully',
					'data': CustomExerciseSerializer(custom_exercise).data
				},
				status=status.HTTP_201_CREATED
			)
		except IntegrityError:
			return Response(
				{
					'error': 'Invalid custom exercise data',
					'detail': {'title': ['A custom exercise with this title already exists.']}
				},
				status=status.HTTP_400_BAD_REQUEST
			)
	return Response(
		{
			'error': 'Invalid custom exercise data',
			'detail': serializer.errors
		},
		status=status.HTTP_400_BAD_REQUEST
	)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([CustomExercisePermission])
def custom_exercise_detail(request, custom_exercise_id):
	"""
	Retrieve, update, or delete a custom exercise.
	"""
	try:
		custom_exercise = CustomExercise.objects.get(id=custom_exercise_id)
	except CustomExercise.DoesNotExist:
		return Response(
			{
				'error': 'Custom exercise not found'
			},
			status=status.HTTP_404_NOT_FOUND
		)

	if not CustomExercisePermission().has_object_permission(request, None, custom_exercise):
		return Response(
			{'error': 'Forbidden'},
			status=status.HTTP_403_FORBIDDEN
		)

	if request.method == 'GET':
		serializer = CustomExerciseSerializer(custom_exercise)
		return Response({'data': serializer.data}, status=status.HTTP_200_OK)

	if request.method == 'PUT':
		serializer = CustomExerciseSerializer(custom_exercise, data=request.data, partial=True)
		if serializer.is_valid():
			try:
				serializer.save()
				return Response(
					{
						'message': 'Custom exercise updated successfully',
						'data': serializer.data
					},
					status=status.HTTP_200_OK
				)
			except IntegrityError:
				return Response(
					{
						'error': 'Invalid custom exercise data',
						'detail': {'title': ['A custom exercise with this title already exists.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
		return Response(
			{
				'error': 'Invalid custom exercise data',
				'detail': serializer.errors
			},
			status=status.HTTP_400_BAD_REQUEST
		)

	custom_exercise.delete()
	return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([ExerciseNotePermission])
def exercise_notes(request):
	"""
	List exercise notes or create a new note.
	"""
	if request.method == 'GET':
		if request.user.is_staff:
			queryset = ExerciseNote.objects.all()
		else:
			queryset = ExerciseNote.objects.filter(user=request.user)

		queryset = queryset.select_related('user', 'exercise', 'custom_exercise')

		exercise_id = request.query_params.get('exercise_id', '').strip()
		custom_exercise_id = request.query_params.get('custom_exercise_id', '').strip()
		ordering = request.query_params.get('ordering', '').strip()
		search = request.query_params.get('search', '').strip()
		user_id = request.query_params.get('user_id', '').strip()
		target = request.query_params.get('target', '').strip()
		has_notes = request.query_params.get('has_notes', '').strip()
		created_from = request.query_params.get('created_from', '').strip()
		created_to = request.query_params.get('created_to', '').strip()
		updated_from = request.query_params.get('updated_from', '').strip()
		updated_to = request.query_params.get('updated_to', '').strip()

		if exercise_id and custom_exercise_id:
			return Response(
				{
					'error': 'Invalid query parameter',
					'detail': {'exercise_id': ['Provide either exercise_id or custom_exercise_id, not both.']}
				},
				status=status.HTTP_400_BAD_REQUEST
			)

		if exercise_id:
			try:
				exercise_id_int = int(exercise_id)
			except ValueError:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'exercise_id': ['Must be an integer.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
			queryset = queryset.filter(exercise_id=exercise_id_int)
		if custom_exercise_id:
			try:
				custom_exercise_id_int = int(custom_exercise_id)
			except ValueError:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'custom_exercise_id': ['Must be an integer.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
			queryset = queryset.filter(custom_exercise_id=custom_exercise_id_int)

		if search:
			queryset = queryset.filter(
				Q(notes__icontains=search) |
				Q(exercise__name__icontains=search) |
				Q(custom_exercise__title__icontains=search)
			)

		if user_id:
			if not request.user.is_staff:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'user_id': ['Forbidden.']}
					},
					status=status.HTTP_403_FORBIDDEN
				)
			try:
				user_id_int = int(user_id)
			except ValueError:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'user_id': ['Must be an integer.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
			queryset = queryset.filter(user_id=user_id_int)

		if target:
			if target not in ['exercise', 'custom_exercise']:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'target': ["Must be 'exercise' or 'custom_exercise'."]}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
			if target == 'exercise':
				queryset = queryset.filter(exercise__isnull=False)
			else:
				queryset = queryset.filter(custom_exercise__isnull=False)

		if has_notes:
			if has_notes.lower() not in ['true', 'false']:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'has_notes': ['Must be true or false.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
			if has_notes.lower() == 'true':
				queryset = queryset.exclude(notes='')
			else:
				queryset = queryset.filter(notes='')

		created_from_dt = _validate_date_param(created_from, 'created_from')
		if isinstance(created_from_dt, Response):
			return created_from_dt
		if created_from_dt:
			queryset = queryset.filter(created_at__gte=created_from_dt)

		created_to_dt = _validate_date_param(created_to, 'created_to')
		if isinstance(created_to_dt, Response):
			return created_to_dt
		if created_to_dt:
			queryset = queryset.filter(created_at__lte=created_to_dt)

		updated_from_dt = _validate_date_param(updated_from, 'updated_from')
		if isinstance(updated_from_dt, Response):
			return updated_from_dt
		if updated_from_dt:
			queryset = queryset.filter(updated_at__gte=updated_from_dt)

		updated_to_dt = _validate_date_param(updated_to, 'updated_to')
		if isinstance(updated_to_dt, Response):
			return updated_to_dt
		if updated_to_dt:
			queryset = queryset.filter(updated_at__lte=updated_to_dt)

		allowed_ordering = ['created_at', '-created_at', 'updated_at', '-updated_at']
		if ordering in allowed_ordering:
			queryset = queryset.order_by(ordering)
		else:
			queryset = queryset.order_by('-updated_at')

		serializer = ExerciseNoteSerializer(queryset, many=True)
		return Response({'data': serializer.data}, status=status.HTTP_200_OK)

	serializer = ExerciseNoteSerializer(data=request.data, context={'request': request})
	if serializer.is_valid():
		try:
			note = serializer.save(user=request.user)
			return Response(
				{
					'message': 'Exercise note created successfully',
					'data': ExerciseNoteSerializer(note).data
				},
				status=status.HTTP_201_CREATED
			)
		except IntegrityError:
			return Response(
				{
					'error': 'Invalid exercise note data',
					'detail': {'notes': ['A note already exists for this exercise.']}
				},
				status=status.HTTP_400_BAD_REQUEST
			)
	return Response(
		{
			'error': 'Invalid exercise note data',
			'detail': serializer.errors
		},
		status=status.HTTP_400_BAD_REQUEST
	)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([ExerciseNotePermission])
def exercise_note_detail(request, note_id):
	"""
	Retrieve, update, or delete an exercise note.
	"""
	try:
		note = ExerciseNote.objects.get(id=note_id)
	except ExerciseNote.DoesNotExist:
		return Response(
			{
				'error': 'Exercise note not found'
			},
			status=status.HTTP_404_NOT_FOUND
		)

	if not ExerciseNotePermission().has_object_permission(request, None, note):
		return Response(
			{'error': 'Forbidden'},
			status=status.HTTP_403_FORBIDDEN
		)

	if request.method == 'GET':
		serializer = ExerciseNoteSerializer(note)
		return Response({'data': serializer.data}, status=status.HTTP_200_OK)

	if request.method == 'PUT':
		serializer = ExerciseNoteSerializer(note, data=request.data, partial=True, context={'request': request})
		if serializer.is_valid():
			try:
				serializer.save()
				return Response(
					{
						'message': 'Exercise note updated successfully',
						'data': serializer.data
					},
					status=status.HTTP_200_OK
				)
			except IntegrityError:
				return Response(
					{
						'error': 'Invalid exercise note data',
						'detail': {'notes': ['A note already exists for this exercise.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
		return Response(
			{
				'error': 'Invalid exercise note data',
				'detail': serializer.errors
			},
			status=status.HTTP_400_BAD_REQUEST
		)

	note.delete()
	return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([ExerciseProgramPermission])
def exercise_programs(request):
	"""
	List exercise programs or create a new exercise program.
	"""
	if request.method == 'GET':
		if request.user.is_staff:
			queryset = ExerciseProgram.objects.all()
		else:
			queryset = ExerciseProgram.objects.filter(
				Q(is_public=True) | Q(created_by=request.user)
			)

		queryset = queryset.select_related('created_by').prefetch_related('items__exercise', 'items__custom_exercise')

		search = request.query_params.get('search', '').strip()
		is_public = request.query_params.get('is_public', '').strip()
		mine = request.query_params.get('mine', '').strip()
		created_by = request.query_params.get('created_by', '').strip()
		exercise_id = request.query_params.get('exercise_id', '').strip()
		custom_exercise_id = request.query_params.get('custom_exercise_id', '').strip()
		ordering = request.query_params.get('ordering', '').strip()

		if search:
			queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))

		if is_public:
			if is_public.lower() in ['true', 'false']:
				queryset = queryset.filter(is_public=is_public.lower() == 'true')
			else:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'is_public': ['Must be true or false.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)

		if mine:
			if mine.lower() in ['true', 'false']:
				if mine.lower() == 'true':
					queryset = queryset.filter(created_by=request.user)
				else:
					queryset = queryset.exclude(created_by=request.user).filter(is_public=True)
			else:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'mine': ['Must be true or false.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)

		if created_by:
			if not request.user.is_staff:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'created_by': ['Forbidden.']}
					},
					status=status.HTTP_403_FORBIDDEN
				)
			try:
				created_by_id = int(created_by)
			except ValueError:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'created_by': ['Must be an integer.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
			queryset = queryset.filter(created_by_id=created_by_id)

		if exercise_id and custom_exercise_id:
			return Response(
				{
					'error': 'Invalid query parameter',
					'detail': {'exercise_id': ['Provide either exercise_id or custom_exercise_id, not both.']}
				},
				status=status.HTTP_400_BAD_REQUEST
			)

		if exercise_id:
			try:
				exercise_id_int = int(exercise_id)
			except ValueError:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'exercise_id': ['Must be an integer.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
			queryset = queryset.filter(items__exercise_id=exercise_id_int)

		if custom_exercise_id:
			try:
				custom_exercise_id_int = int(custom_exercise_id)
			except ValueError:
				return Response(
					{
						'error': 'Invalid query parameter',
						'detail': {'custom_exercise_id': ['Must be an integer.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
			queryset = queryset.filter(items__custom_exercise_id=custom_exercise_id_int)

		allowed_ordering = ['name', '-name', 'created_at', '-created_at', 'updated_at', '-updated_at']
		if ordering in allowed_ordering:
			queryset = queryset.order_by(ordering)
		else:
			queryset = queryset.order_by('name')

		queryset = queryset.distinct()

		serializer = ExerciseProgramSerializer(queryset, many=True)
		return Response({'data': serializer.data}, status=status.HTTP_200_OK)

	serializer = ExerciseProgramSerializer(data=request.data, context={'request': request})
	if serializer.is_valid():
		try:
			with transaction.atomic():
				program = serializer.save(created_by=request.user)
			return Response(
				{
					'message': 'Exercise program created successfully',
					'data': ExerciseProgramSerializer(program).data
				},
				status=status.HTTP_201_CREATED
			)
		except IntegrityError:
			return Response(
				{
					'error': 'Invalid exercise program data',
					'detail': {'name': ['An exercise program with this name already exists.']}
				},
				status=status.HTTP_400_BAD_REQUEST
			)
	return Response(
		{
			'error': 'Invalid exercise program data',
			'detail': serializer.errors
		},
		status=status.HTTP_400_BAD_REQUEST
	)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([ExerciseProgramPermission])
def exercise_program_detail(request, program_id):
	"""
	Retrieve, update, or delete an exercise program.
	"""
	try:
		program = ExerciseProgram.objects.select_related('created_by').prefetch_related('items__exercise', 'items__custom_exercise').get(id=program_id)
	except ExerciseProgram.DoesNotExist:
		return Response(
			{
				'error': 'Exercise program not found'
			},
			status=status.HTTP_404_NOT_FOUND
		)

	if request.method == 'GET':
		if not _can_view_program(request.user, program):
			return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
		serializer = ExerciseProgramSerializer(program)
		return Response({'data': serializer.data}, status=status.HTTP_200_OK)

	if not _can_manage_program(request.user, program):
		return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

	if request.method == 'PUT':
		serializer = ExerciseProgramSerializer(program, data=request.data, partial=True, context={'request': request})
		if serializer.is_valid():
			try:
				with transaction.atomic():
					serializer.save()
				return Response(
					{
						'message': 'Exercise program updated successfully',
						'data': serializer.data
					},
					status=status.HTTP_200_OK
				)
			except IntegrityError:
				return Response(
					{
						'error': 'Invalid exercise program data',
						'detail': {'name': ['An exercise program with this name already exists.']}
					},
					status=status.HTTP_400_BAD_REQUEST
				)
		return Response(
			{
				'error': 'Invalid exercise program data',
				'detail': serializer.errors
			},
			status=status.HTTP_400_BAD_REQUEST
		)

	program.delete()
	return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([ExerciseProgramPermission])
def exercise_program_reuse(request, program_id):
	"""
	Clone a visible program into the current user's library.
	"""
	try:
		program = ExerciseProgram.objects.prefetch_related('items').get(id=program_id)
	except ExerciseProgram.DoesNotExist:
		return Response(
			{
				'error': 'Exercise program not found'
			},
			status=status.HTTP_404_NOT_FOUND
		)

	if not _can_view_program(request.user, program):
		return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

	with transaction.atomic():
		reused_program = ExerciseProgram.objects.create(
			created_by=request.user,
			name=_build_reused_program_name(request.user, program.name),
			description=program.description,
			is_public=False,
		)
		ExerciseProgramItem.objects.bulk_create([
			ExerciseProgramItem(
				program=reused_program,
				exercise=item.exercise,
				custom_exercise=item.custom_exercise,
				position=item.position,
				week=item.week,
				day=item.day,
				sets=item.sets,
				reps=item.reps,
				load=item.load,
				rest_seconds=item.rest_seconds,
				notes=item.notes,
			)
			for item in program.items.all().order_by('position', 'id')
		])

	return Response(
		{
			'message': 'Exercise program reused successfully',
			'data': ExerciseProgramSerializer(reused_program).data
		},
		status=status.HTTP_201_CREATED
	)
