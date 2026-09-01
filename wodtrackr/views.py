from django.db import IntegrityError, transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Exercise, ExerciseProgram, ExerciseProgramItem
from .permissions import ExercisePermission, ExerciseProgramPermission
from .serializers import ExerciseProgramItemSerializer, ExerciseProgramSerializer, ExerciseSerializer


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


def _parse_bool_query(value, field_name):
    if value == '':
        return None
    lowered = value.lower()
    if lowered in ['true', 'false']:
        return lowered == 'true'
    return Response(
        {
            'error': 'Invalid query parameter',
            'detail': {field_name: ['Must be true or false.']}
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def exercise_choices(request):
    """
    Return available values from existing exercise rows.
    """

    def distinct_values(field_name):
        return [
            {'value': value, 'label': value.title()}
            for value in Exercise.objects.exclude(**{f'{field_name}__isnull': True}).exclude(**{field_name: ''}).values_list(field_name, flat=True).distinct().order_by(field_name)
        ]

    return Response(
        {
            'category': distinct_values('category'),
            'body_part': distinct_values('body_part'),
            'equipment': distinct_values('equipment'),
            'muscle_group': distinct_values('muscle_group'),
            'target': distinct_values('target_muscle'),
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def exercise_program_choices(request):
    """
    Return static choice sets for exercise programs.
    """
    return Response(
        {
            'difficulty': [{'value': key, 'label': label} for key, label in ExerciseProgram.DIFFICULTY_CHOICES],
            'duration_weeks': [{'value': key, 'label': label} for key, label in ExerciseProgram.DURATION_WEEKS_CHOICES],
        },
        status=status.HTTP_200_OK,
    )


@api_view(['GET', 'POST'])
@permission_classes([ExercisePermission])
def exercises(request):
    """
    List exercises or create a new exercise.
    """
    if request.method == 'GET':
        if request.user and request.user.is_authenticated:
            base_queryset = Exercise.objects.filter(Q(is_public=True) | Q(created_by=request.user))
        else:
            base_queryset = Exercise.objects.filter(is_public=True)

        queryset = base_queryset
        search = request.query_params.get('search', '').strip()
        category = request.query_params.get('category', '').strip()
        body_part = request.query_params.get('body_part', '').strip()
        equipment = request.query_params.get('equipment', '').strip()
        muscle = request.query_params.get('muscle', '').strip()
        target = request.query_params.get('target', '').strip()
        is_public = request.query_params.get('is_public', '').strip()
        mine = request.query_params.get('mine', '').strip()
        ordering = request.query_params.get('ordering', '').strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(category__icontains=search)
                | Q(body_part__icontains=search)
                | Q(equipment__icontains=search)
                | Q(muscle_group__icontains=search)
                | Q(target_muscle__icontains=search)
            )

        if category:
            queryset = queryset.filter(category__iexact=category)
        if body_part:
            queryset = queryset.filter(body_part__iexact=body_part)
        if equipment:
            queryset = queryset.filter(equipment__iexact=equipment)
        if muscle:
            queryset = queryset.filter(muscle_group__icontains=muscle)
        if target:
            queryset = queryset.filter(target_muscle__icontains=target)

        parsed_is_public = _parse_bool_query(is_public, 'is_public')
        if isinstance(parsed_is_public, Response):
            return parsed_is_public
        if parsed_is_public is not None:
            queryset = queryset.filter(is_public=parsed_is_public)

        parsed_mine = _parse_bool_query(mine, 'mine')
        if isinstance(parsed_mine, Response):
            return parsed_mine
        if parsed_mine is True:
            if request.user and request.user.is_authenticated:
                queryset = queryset.filter(created_by=request.user)
            else:
                queryset = queryset.none()
        elif parsed_mine is False:
            queryset = queryset.filter(is_public=True)

        allowed_ordering = ['name', '-name', 'created_at', '-created_at', 'updated_at', '-updated_at']
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('name')

        filtered_serializer = ExerciseSerializer(queryset, many=True, context={'request': request})
        all_serializer = ExerciseSerializer(base_queryset.order_by('name'), many=True, context={'request': request})
        return Response(
            {
                'data': filtered_serializer.data,
                'filtered_exercises': filtered_serializer.data,
                'all_exercises': all_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    serializer = ExerciseSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            exercise = serializer.save(created_by=request.user)
            return Response(
                {
                    'message': 'Exercise created successfully',
                    'data': ExerciseSerializer(exercise, context={'request': request}).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError:
            return Response(
                {
                    'error': 'Invalid exercise data',
                    'detail': {'name': ['An exercise with this name already exists.']},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    return Response(
        {
            'error': 'Invalid exercise data',
            'detail': serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
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
        return Response({'error': 'Exercise not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        if request.user and request.user.is_authenticated:
            can_view = exercise.is_public or _can_manage_exercise(request.user, exercise)
        else:
            can_view = exercise.is_public
        if not can_view:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ExerciseSerializer(exercise, context={'request': request})
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    if not _can_manage_exercise(request.user, exercise):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'PUT':
        serializer = ExerciseSerializer(exercise, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {
                        'message': 'Exercise updated successfully',
                        'data': serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            except IntegrityError:
                return Response(
                    {
                        'error': 'Invalid exercise data',
                        'detail': {'name': ['An exercise with this name already exists.']},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {
                'error': 'Invalid exercise data',
                'detail': serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    exercise.delete()
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
            queryset = ExerciseProgram.objects.filter(Q(is_public=True) | Q(created_by=request.user))

        queryset = queryset.select_related('created_by').prefetch_related('exercises', 'items__exercise')

        search = request.query_params.get('search', '').strip()
        is_public = request.query_params.get('is_public', '').strip()
        mine = request.query_params.get('mine', '').strip()
        difficulty = request.query_params.get('difficulty', '').strip()
        duration_weeks = request.query_params.get('duration_weeks', '').strip()
        exercise_id = request.query_params.get('exercise_id', '').strip()
        ordering = request.query_params.get('ordering', '').strip()

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(note__icontains=search)
            )

        parsed_is_public = _parse_bool_query(is_public, 'is_public')
        if isinstance(parsed_is_public, Response):
            return parsed_is_public
        if parsed_is_public is not None:
            queryset = queryset.filter(is_public=parsed_is_public)

        parsed_mine = _parse_bool_query(mine, 'mine')
        if isinstance(parsed_mine, Response):
            return parsed_mine
        if parsed_mine is True:
            queryset = queryset.filter(created_by=request.user)
        elif parsed_mine is False:
            queryset = queryset.exclude(created_by=request.user).filter(is_public=True)

        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        if duration_weeks:
            try:
                duration_weeks_value = int(duration_weeks)
            except ValueError:
                return Response(
                    {
                        'error': 'Invalid query parameter',
                        'detail': {'duration_weeks': ['Must be an integer.']},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(duration_weeks=duration_weeks_value)

        if exercise_id:
            try:
                exercise_id_int = int(exercise_id)
            except ValueError:
                return Response(
                    {
                        'error': 'Invalid query parameter',
                        'detail': {'exercise_id': ['Must be an integer.']},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(items__exercise_id=exercise_id_int)

        allowed_ordering = ['name', '-name', 'created_at', '-created_at', 'updated_at', '-updated_at']
        if ordering in allowed_ordering:
            queryset = queryset.order_by(ordering)
        else:
            queryset = queryset.order_by('name')

        serializer = ExerciseProgramSerializer(queryset.distinct(), many=True, context={'request': request})
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    serializer = ExerciseProgramSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            with transaction.atomic():
                program = serializer.save(created_by=request.user)
            return Response(
                {
                    'message': 'Exercise program created successfully',
                    'data': ExerciseProgramSerializer(program, context={'request': request}).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError:
            return Response(
                {
                    'error': 'Invalid exercise program data',
                    'detail': {'name': ['An exercise program with this name already exists.']},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
    return Response(
        {
            'error': 'Invalid exercise program data',
            'detail': serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([ExerciseProgramPermission])
def exercise_program_detail(request, program_id):
    """
    Retrieve, update, or delete an exercise program.
    """
    try:
        program = ExerciseProgram.objects.select_related('created_by').prefetch_related('exercises', 'items__exercise').get(id=program_id)
    except ExerciseProgram.DoesNotExist:
        return Response({'error': 'Exercise program not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        if not _can_view_program(request.user, program):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ExerciseProgramSerializer(program, context={'request': request})
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    if not _can_manage_program(request.user, program):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if request.method in ['PUT', 'PATCH']:
        serializer = ExerciseProgramSerializer(program, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    serializer.save()
                program.refresh_from_db()
                program = ExerciseProgram.objects.select_related('created_by').prefetch_related('exercises', 'items__exercise').get(id=program.id)
                response_serializer = ExerciseProgramSerializer(program, context={'request': request})
                return Response(
                    {
                        'message': 'Exercise program updated successfully',
                        'data': response_serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            except IntegrityError:
                return Response(
                    {
                        'error': 'Invalid exercise program data',
                        'detail': {'name': ['An exercise program with this name already exists.']},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        return Response(
            {
                'error': 'Invalid exercise program data',
                'detail': serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    program.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([ExerciseProgramPermission])
def exercise_program_item(request, program_id):
    """
    List, create, update, or delete items for a specific exercise program.
    """
    try:
        program = ExerciseProgram.objects.select_related('created_by').get(id=program_id)
    except ExerciseProgram.DoesNotExist:
        return Response({'error': 'Exercise program not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        if not _can_view_program(request.user, program):
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        items = program.items.select_related('exercise').order_by('position', 'id')
        serializer = ExerciseProgramItemSerializer(items, many=True, context={'request': request})
        return Response({'data': serializer.data}, status=status.HTTP_200_OK)

    if not _can_manage_program(request.user, program):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'DELETE':
        item_id = request.query_params.get('id') or request.data.get('id')
        if not item_id:
            return Response(
                {
                    'error': 'Invalid exercise program item data',
                    'detail': {'id': ['This field is required.']},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item_id_int = int(item_id)
        except (TypeError, ValueError):
            return Response(
                {
                    'error': 'Invalid exercise program item data',
                    'detail': {'id': ['Must be an integer.']},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item = ExerciseProgramItem.objects.get(id=item_id_int, program=program)
        except ExerciseProgramItem.DoesNotExist:
            return Response({'error': 'Exercise program item not found'}, status=status.HTTP_404_NOT_FOUND)

        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    if request.method == 'PUT':
        item_id = request.data.get('id')
        if not item_id:
            return Response(
                {
                    'error': 'Invalid exercise program item data',
                    'detail': {'id': ['This field is required.']},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item_id_int = int(item_id)
        except (TypeError, ValueError):
            return Response(
                {
                    'error': 'Invalid exercise program item data',
                    'detail': {'id': ['Must be an integer.']},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item = ExerciseProgramItem.objects.get(id=item_id_int, program=program)
        except ExerciseProgramItem.DoesNotExist:
            return Response({'error': 'Exercise program item not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = ExerciseProgramItemSerializer(item, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {
                        'message': 'Exercise program item updated successfully',
                        'data': serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )
            except IntegrityError:
                return Response(
                    {
                        'error': 'Invalid exercise program item data',
                        'detail': {'position': ['An item with this position already exists in this program.']},
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return Response(
            {
                'error': 'Invalid exercise program item data',
                'detail': serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    serializer = ExerciseProgramItemSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        try:
            item = serializer.save(program=program)
            program.exercises.add(item.exercise)
            return Response(
                {
                    'message': 'Exercise program item created successfully',
                    'data': ExerciseProgramItemSerializer(item, context={'request': request}).data,
                },
                status=status.HTTP_201_CREATED,
            )
        except IntegrityError:
            return Response(
                {
                    'error': 'Invalid exercise program item data',
                    'detail': {'position': ['An item with this position already exists in this program.']},
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    return Response(
        {
            'error': 'Invalid exercise program item data',
            'detail': serializer.errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


@api_view(['POST'])
@permission_classes([ExerciseProgramPermission])
def exercise_program_reuse(request, program_id):
    """
    Clone a visible program into the current user's library.
    """
    try:
        program = ExerciseProgram.objects.prefetch_related('items', 'exercises').get(id=program_id)
    except ExerciseProgram.DoesNotExist:
        return Response({'error': 'Exercise program not found'}, status=status.HTTP_404_NOT_FOUND)

    if not _can_view_program(request.user, program):
        return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    with transaction.atomic():
        reused_program = ExerciseProgram.objects.create(
            created_by=request.user,
            name=_build_reused_program_name(request.user, program.name),
            description=program.description,
            difficulty=program.difficulty,
            duration_weeks=program.duration_weeks,
            program_image=program.program_image,
            note=program.note,
            is_public=False,
        )
        ExerciseProgramItem.objects.bulk_create([
            ExerciseProgramItem(
                program=reused_program,
                exercise=item.exercise,
                position=item.position,
                week=item.week,
                day=item.day,
                sets=item.sets,
                reps=item.reps,
                load=item.load,
                rest_seconds=item.rest_seconds,
            )
            for item in program.items.all().order_by('position', 'id')
        ])
        reused_program.exercises.set(program.exercises.all())

    return Response(
        {
            'message': 'Exercise program reused successfully',
            'data': ExerciseProgramSerializer(reused_program, context={'request': request}).data,
        },
        status=status.HTTP_201_CREATED,
    )
