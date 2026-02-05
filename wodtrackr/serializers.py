from rest_framework import serializers

from .models import Exercise, CustomExercise, ExerciseNote


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
