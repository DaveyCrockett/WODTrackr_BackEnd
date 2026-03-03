from django.db import models
from django.core.validators import MinLengthValidator
from django.db.models.functions import Lower
from django.contrib.auth.models import User


class Exercise(models.Model):
	"""
	Represents a single exercise definition.
	"""
	Primary_Muscle_Choices = [
		('back', 'Back'),
		('cardio', 'Cardio'),
		('chest', 'Chest'),
		('core', 'Core'),
		('full_body', 'Full Body'),
		('glutes', 'Glutes'),
		('legs', 'Legs'),
		('shoulders', 'Shoulders'),
		('other', 'Other'),
	]

	CATEGORY_CHOICES = [
		('weightlifting', 'Weightlifting'),
		('powerlifting', 'Powerlifting'),
		('gymnastics', 'Gymnastics'),
		('monostructural', 'Monostructural'),
		('accessory', 'Accessory'),
		('mobility', 'Mobility'),
		('other', 'Other'),
	]

	EQUIPMENT_CHOICES = [
		('bodyweight', 'Bodyweight'),
		('barbell', 'Barbell'),
		('dumbbell', 'Dumbbell'),
		('kettlebell', 'Kettlebell'),
		('medicine_ball', 'Medicine Ball'),
		('box', 'Plyo Box'),
		('rig', 'Pull-up Rig'),
		('rings', 'Rings'),
		('rope', 'Climbing Rope'),
		('rower', 'Rower'),
		('bike', 'Bike'),
		('ski_erg', 'SkiErg'),
		('assault_runner', 'Assault Runner'),
		('jump_rope', 'Jump Rope'),
		('sled', 'Sled'),
		('sandbag', 'Sandbag'),
		('pegboard', 'Pegboard'),
		('other', 'Other'),
	]

	name = models.CharField(
		max_length=120,
		unique=True,
		validators=[MinLengthValidator(2)]
	)
	description = models.TextField(blank=True)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
	equipment = models.CharField(max_length=20, choices=EQUIPMENT_CHOICES, default='bodyweight')
	primary_muscle_group = models.CharField(max_length=50, choices=Primary_Muscle_Choices, blank=True)
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='exercises')
	is_public = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['name']
		constraints = [
			models.CheckConstraint(condition=~models.Q(name=''), name='exercise_name_not_blank'),
			models.UniqueConstraint(Lower('name'), name='exercise_name_unique_ci'),
		]
		indexes = [
			models.Index(fields=['name']),
			models.Index(fields=['category']),
			models.Index(fields=['equipment']),
			models.Index(fields=['is_public']),
			models.Index(fields=['created_by']),
		]

	def __str__(self):
		return self.name


class CustomExercise(models.Model):
	"""
	Represents a user-defined custom exercise.
	"""
	CATEGORY_CHOICES = Exercise.CATEGORY_CHOICES
	EQUIPMENT_CHOICES = Exercise.EQUIPMENT_CHOICES
	Primary_Muscle_Choices = Exercise.Primary_Muscle_Choices

	created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='custom_exercises')
	title = models.CharField(
		max_length=120,
		validators=[MinLengthValidator(2)]
	)
	description = models.TextField(blank=True)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
	equipment = models.CharField(max_length=20, choices=EQUIPMENT_CHOICES, default='bodyweight')
	primary_muscle_group = models.CharField(max_length=50, choices=Primary_Muscle_Choices, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['title']
		constraints = [
			models.CheckConstraint(condition=~models.Q(title=''), name='custom_exercise_title_not_blank'),
			models.UniqueConstraint(Lower('title'), 'created_by', name='custom_exercise_title_unique_ci'),
		]
		indexes = [
			models.Index(fields=['title']),
			models.Index(fields=['category']),
			models.Index(fields=['equipment']),
			models.Index(fields=['created_by']),
		]

	def __str__(self):
		return f"{self.title} ({self.created_by.username})"


class ExerciseNote(models.Model):
	"""
	Per-user notes for either a shared exercise or a custom exercise.
	"""
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_notes')
	exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
	custom_exercise = models.ForeignKey(CustomExercise, on_delete=models.CASCADE, null=True, blank=True, related_name='notes')
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-updated_at']
		constraints = [
			models.CheckConstraint(
				condition=(
					(models.Q(exercise__isnull=False) & models.Q(custom_exercise__isnull=True)) |
					(models.Q(exercise__isnull=True) & models.Q(custom_exercise__isnull=False))
				),
				name='exercise_note_single_target'
			),
			models.UniqueConstraint(fields=['user', 'exercise'], name='unique_note_per_user_exercise'),
			models.UniqueConstraint(fields=['user', 'custom_exercise'], name='unique_note_per_user_custom_exercise'),
		]
		indexes = [
			models.Index(fields=['user']),
			models.Index(fields=['exercise']),
			models.Index(fields=['custom_exercise']),
		]

	def __str__(self):
		target = self.exercise.name if self.exercise_id else self.custom_exercise.title
		return f"Notes: {self.user.username} - {target}"