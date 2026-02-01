from django.db import IntegrityError
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Exercise
from .permissions import ExercisePermission
from .serializers import ExerciseSerializer


def _can_manage_exercise(user, exercise):
	return user.is_staff or exercise.created_by == user


@api_view(['GET', 'POST'])
@permission_classes([ExercisePermission])
def exercises(request):
	"""
	List exercises or create a new exercise.
	"""
	if request.method == 'GET':
		queryset = Exercise.objects.filter(
			Q(is_public=True) | Q(created_by=request.user)
		)

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
			queryset = queryset.filter(category=category)
		if equipment:
			queryset = queryset.filter(equipment=equipment)
		if muscle:
			queryset = queryset.filter(primary_muscle_group__icontains=muscle)
		if is_public.lower() in ['true', 'false']:
			queryset = queryset.filter(is_public=is_public.lower() == 'true')
		if mine.lower() in ['true', 'false']:
			if mine.lower() == 'true':
				queryset = queryset.filter(created_by=request.user)
			else:
				queryset = queryset.filter(is_public=True)

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
		if not (exercise.is_public or _can_manage_exercise(request.user, exercise)):
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
