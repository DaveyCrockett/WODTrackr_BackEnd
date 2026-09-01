from rest_framework import serializers
from django.conf import settings

from .models import Exercise, ExerciseProgram, ExerciseProgramItem


class ExerciseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    target = serializers.CharField(source='target_muscle', required=False, allow_null=True, allow_blank=True)
    dataset_created_at = serializers.DateTimeField(required=False, allow_null=True)
    title = serializers.CharField(source='name', read_only=True)
    primary_muscle_group = serializers.CharField(source='muscle_group', read_only=True)
    image_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    image_upload = serializers.ImageField(required=False, allow_null=True)
    resolved_image_url = serializers.SerializerMethodField(read_only=True)
    gif_absolute_url = serializers.SerializerMethodField(read_only=True)

    def _build_absolute_url(self, value):
        if not value:
            return ''

        if isinstance(value, str) and (value.startswith('http://') or value.startswith('https://')):
            return value

        request = self.context.get('request')
        if request is None:
            return value

        if str(value).startswith('/'):
            return request.build_absolute_uri(value)

        return request.build_absolute_uri(f'/{value}')

    def _resolve_image_source(self, obj):
        image_upload = getattr(obj, 'image_upload', None)
        if image_upload:
            if hasattr(image_upload, 'url'):
                return image_upload.url
            return image_upload

        image_value = getattr(obj, 'image_url', None)
        if image_value:
            return image_value

        return ''

    def get_resolved_image_url(self, obj):
        return self._build_absolute_url(self._resolve_image_source(obj))

    def get_gif_absolute_url(self, obj):
        return self._build_absolute_url(obj.gif_url)

    def to_internal_value(self, data):
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)

        if 'name' not in mutable_data and 'title' in mutable_data:
            mutable_data['name'] = mutable_data.get('title')

        if 'muscle_group' not in mutable_data and 'primary_muscle_group' in mutable_data:
            mutable_data['muscle_group'] = mutable_data.get('primary_muscle_group')

        if 'target_muscle' not in mutable_data and 'target' in mutable_data:
            mutable_data['target_muscle'] = mutable_data.get('target')

        if 'dataset_created_at' not in mutable_data and 'source_created_at' in mutable_data:
            mutable_data['dataset_created_at'] = mutable_data.get('source_created_at')

        return super().to_internal_value(mutable_data)

    def validate_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError('Name must be at least 2 characters long.')
        if len(cleaned) > 120:
            raise serializers.ValidationError('Name must be 120 characters or fewer.')
        return cleaned

    def validate_muscle_group(self, value):
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) > 120:
            raise serializers.ValidationError('Muscle group must be 120 characters or fewer.')
        return cleaned

    def validate_secondary_muscles(self, value):
        if value is None:
            return []
        if not isinstance(value, list):
            raise serializers.ValidationError('Secondary muscles must be a list of strings.')
        invalid_values = [item for item in value if not isinstance(item, str) or not item.strip()]
        if invalid_values:
            raise serializers.ValidationError('Secondary muscles must contain only non-empty strings.')
        return [item.strip() for item in value]

    class Meta:
        model = Exercise
        fields = (
            'id',
            'dataset_id',
            'name',
            'title',
            'category',
            'body_part',
            'muscle_group',
            'primary_muscle_group',
            'secondary_muscles',
            'target',
            'target_muscle',
            'equipment',
            'instructions',
            'instruction_steps',
            'media_id',
            'image_url',
            'image_upload',
            'resolved_image_url',
            'gif_url',
            'gif_absolute_url',
            'attribution',
            'dataset_created_at',
            'is_public',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_by', 'created_by_username', 'created_at', 'updated_at')


class ExerciseProgramItemSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    position = serializers.IntegerField(required=False, min_value=1)
    week = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    day = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    sets = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    rest_seconds = serializers.IntegerField(required=False, allow_null=True, min_value=0)

    def validate_reps(self, value):
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) > 50:
            raise serializers.ValidationError('Reps must be 50 characters or fewer.')
        return cleaned

    def validate_load(self, value):
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) > 50:
            raise serializers.ValidationError('Load must be 50 characters or fewer.')
        return cleaned

    def validate(self, attrs):
        exercise = attrs.get('exercise', getattr(self.instance, 'exercise', None))

        if exercise is None:
            raise serializers.ValidationError('Exercise is required.')

        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if exercise is not None:
            if not (user and (exercise.is_public or exercise.created_by == user or user.is_staff)):
                raise serializers.ValidationError('Exercise not found.')

        return attrs

    class Meta:
        model = ExerciseProgramItem
        fields = (
            'id',
            'exercise',
            'exercise_name',
            'position',
            'week',
            'day',
            'sets',
            'reps',
            'load',
            'rest_seconds',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class ExerciseProgramSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    exercises = serializers.PrimaryKeyRelatedField(many=True, queryset=Exercise.objects.all(), required=False)
    items = ExerciseProgramItemSerializer(many=True, required=False)
    program_image = serializers.ImageField(required=False, allow_null=False)
    image_url = serializers.SerializerMethodField(read_only=True)

    def get_image_url(self, obj):
        if obj.program_image and hasattr(obj.program_image, 'url'):
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(obj.program_image.url)
            return obj.program_image.url
        return f"{settings.MEDIA_URL}default_program_image.jpg"

    def to_internal_value(self, data):
        # Accept legacy aliases from clients while keeping the canonical API fields.
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)

        if 'items' not in mutable_data and 'item' in mutable_data:
            mutable_data['items'] = mutable_data.get('item')

        return super().to_internal_value(mutable_data)

    def validate_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError('Name must be at least 2 characters long.')
        if len(cleaned) > 120:
            raise serializers.ValidationError('Name must be 120 characters or fewer.')
        return cleaned

    def validate_description(self, value):
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) > 3000:
            raise serializers.ValidationError('Description must be 3000 characters or fewer.')
        return cleaned

    def validate_items(self, value):
        normalized_positions = []
        for index, item in enumerate(value, start=1):
            position = item.get('position') or index
            normalized_positions.append(position)

        if len(normalized_positions) != len(set(normalized_positions)):
            raise serializers.ValidationError('Item positions must be unique within a program.')

        return value

    def _prepare_items(self, items_data):
        prepared_items = []
        for index, item_data in enumerate(items_data, start=1):
            prepared_item = dict(item_data)
            prepared_item['position'] = prepared_item.get('position') or index
            prepared_items.append(prepared_item)
        return prepared_items

    def _create_items(self, program, items_data):
        for item_data in self._prepare_items(items_data):
            ExerciseProgramItem.objects.create(program=program, **item_data)

    def _sync_program_exercises_from_items(self, program):
        exercise_ids = program.items.values_list('exercise_id', flat=True)
        program.exercises.set(Exercise.objects.filter(id__in=exercise_ids))

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        exercises_data = validated_data.pop('exercises', [])
        program = ExerciseProgram.objects.create(**validated_data)
        if exercises_data:
            program.exercises.set(exercises_data)
        self._create_items(program, items_data)
        if items_data:
            self._sync_program_exercises_from_items(program)
        return program

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        exercises_data = validated_data.pop('exercises', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if exercises_data is not None:
            instance.exercises.set(exercises_data)

        if items_data is not None:
            instance.items.all().delete()
            self._create_items(instance, items_data)
            self._sync_program_exercises_from_items(instance)

        return instance

    class Meta:
        model = ExerciseProgram
        fields = (
            'id',
            'name',
            'description',
            'exercises',
            'difficulty',
            'duration_weeks',
            'program_image',
            'image_url',
            'is_public',
            'note',
            'created_by',
            'created_by_username',
            'items',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_by', 'created_by_username', 'created_at', 'updated_at')

    
