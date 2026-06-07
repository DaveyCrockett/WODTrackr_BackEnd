from rest_framework import serializers

from .models import Exercise, CustomExercise, ExerciseNote, ExerciseProgram, ExerciseProgramItem, Equipment


class ExerciseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    def validate_name(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError('Name must be at least 2 characters long.')
        if len(cleaned) > 120:
            raise serializers.ValidationError('Name must be 120 characters or fewer.')
        return cleaned

    def validate_primary_muscle_group(self, value):
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) > 50:
            raise serializers.ValidationError('Primary muscle group must be 50 characters or fewer.')
        return cleaned

    def validate_description(self, value):
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) > 1000:
            raise serializers.ValidationError('Description must be 1000 characters or fewer.')
        return cleaned

    class Meta:
        model = Exercise
        fields = (
            'id',
            'name',
            'description',
            'category',
            'equipment',
            'primary_muscle_group',
            'is_public',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_by', 'created_by_username', 'created_at', 'updated_at')


class EquipmentSerializer(serializers.ModelSerializer):
    value = serializers.CharField(source='equipment', read_only=True)
    label = serializers.SerializerMethodField()

    def get_label(self, obj):
        return dict(Equipment.EQUIPMENT_CHOICES).get(obj.equipment, obj.equipment.replace('_', ' ').title())

    class Meta:
        model = Equipment
        fields = (
            'id',
            'equipment',
            'value',
            'label',
        )
        read_only_fields = ('id', 'equipment', 'value', 'label')


class CustomExerciseSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    def validate_title(self, value):
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise serializers.ValidationError('Title must be at least 2 characters long.')
        if len(cleaned) > 120:
            raise serializers.ValidationError('Title must be 120 characters or fewer.')
        return cleaned

    def validate_primary_muscle_group(self, value):
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) > 50:
            raise serializers.ValidationError('Primary muscle group must be 50 characters or fewer.')
        return cleaned

    def validate_description(self, value):
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) > 1000:
            raise serializers.ValidationError('Description must be 1000 characters or fewer.')
        return cleaned

    class Meta:
        model = CustomExercise
        fields = (
            'id',
            'title',
            'description',
            'category',
            'equipment',
            'primary_muscle_group',
            'created_by',
            'created_by_username',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_by', 'created_by_username', 'created_at', 'updated_at')


class ExerciseNoteSerializer(serializers.ModelSerializer):
    user_username = serializers.CharField(source='user.username', read_only=True)
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    custom_exercise_title = serializers.CharField(source='custom_exercise.title', read_only=True)

    def validate_notes(self, value):
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) > 5000:
            raise serializers.ValidationError('Notes must be 5000 characters or fewer.')
        return cleaned

    def validate(self, attrs):
        exercise = attrs.get('exercise', getattr(self.instance, 'exercise', None))
        custom_exercise = attrs.get('custom_exercise', getattr(self.instance, 'custom_exercise', None))

        if (exercise is None and custom_exercise is None) or (exercise is not None and custom_exercise is not None):
            raise serializers.ValidationError('Provide exactly one of exercise or custom_exercise.')

        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if custom_exercise is not None:
            if not (user and (user.is_staff or custom_exercise.created_by == user)):
                raise serializers.ValidationError('Custom exercise not found.')

        if exercise is not None:
            if not (user and (exercise.is_public or exercise.created_by == user or user.is_staff)):
                raise serializers.ValidationError('Exercise not found.')

        return attrs

    class Meta:
        model = ExerciseNote
        fields = (
            'id',
            'user',
            'user_username',
            'exercise',
            'exercise_name',
            'custom_exercise',
            'custom_exercise_title',
            'notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('user', 'user_username', 'created_at', 'updated_at')


class ExerciseProgramItemSerializer(serializers.ModelSerializer):
    exercise_name = serializers.CharField(source='exercise.name', read_only=True)
    custom_exercise_name = serializers.CharField(source='custom_exercise.name', read_only=True)
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

    def validate_notes(self, value):
        if value is None:
            return value
        cleaned = value.strip()
        if len(cleaned) > 2000:
            raise serializers.ValidationError('Notes must be 2000 characters or fewer.')
        return cleaned

    def validate(self, attrs):
        exercise = attrs.get('exercise', getattr(self.instance, 'exercise', None))
        custom_exercise = attrs.get('custom_exercise', getattr(self.instance, 'custom_exercise', None))

        if (exercise is None and custom_exercise is None) or (exercise is not None and custom_exercise is not None):
            raise serializers.ValidationError('Provide exactly one of exercise or custom_exercise.')

        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if custom_exercise is not None:
            if not (user and (user.is_staff or custom_exercise.created_by == user)):
                raise serializers.ValidationError('Custom exercise not found.')

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
            'custom_exercise',
            'custom_exercise_name',
            'position',
            'week',
            'day',
            'sets',
            'reps',
            'load',
            'rest_seconds',
            'notes',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')


class ExerciseProgramSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    equipment = serializers.StringRelatedField(many=True, read_only=True)
    equipment_ids = serializers.PrimaryKeyRelatedField(
        queryset=Equipment.objects.all(),
        many=True,
        write_only=True,
        required=False,
        source='equipment'
    )
    items = ExerciseProgramItemSerializer(many=True, required=False)

    def to_internal_value(self, data):
        # Accept legacy aliases from clients while keeping the canonical API fields.
        mutable_data = data.copy() if hasattr(data, 'copy') else dict(data)

        equipment_value = mutable_data.get('equipment')
        if 'equipment_ids' not in mutable_data and isinstance(equipment_value, list):
            mutable_data['equipment_ids'] = equipment_value

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

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        equipment_data = validated_data.pop('equipment', [])
        program = ExerciseProgram.objects.create(**validated_data)
        if equipment_data:
            program.equipment.set(equipment_data)
        self._create_items(program, items_data)
        return program

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        equipment_data = validated_data.pop('equipment', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if equipment_data is not None:
            instance.equipment.set(equipment_data)

        if items_data is not None:
            instance.items.all().delete()
            self._create_items(instance, items_data)

        return instance

    class Meta:
        model = ExerciseProgram
        fields = (
            'id',
            'name',
            'description',
            'category',
            'equipment',
            'equipment_ids',
            'primary_muscle_group',
            'difficulty',
            'duration_weeks',
            'program_image',
            'is_public',
            'created_by',
            'created_by_username',
            'items',
            'created_at',
            'updated_at',
            'goal',
        )
        read_only_fields = ('created_by', 'created_by_username', 'created_at', 'updated_at')
