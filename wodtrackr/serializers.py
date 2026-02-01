from rest_framework import serializers

from .models import Exercise


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
