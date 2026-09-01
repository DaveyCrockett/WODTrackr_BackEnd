from django.db import models
from django.core.validators import MinLengthValidator
from django.db.models.functions import Lower
from django.contrib.auth.models import User


class Exercise(models.Model):
	"""
	Represents a single exercise definition.
	"""

	DIFFICULTY_CHOICES = [
		('beginner', 'Beginner'),
		('intermediate', 'Intermediate'),
		('advanced', 'Advanced'),
	]

	name = models.CharField(
		max_length=120,
		unique=True,
		validators=[MinLengthValidator(2)]
	)
	dataset_id = models.CharField(max_length=16, blank=True, null=True, unique=True)
	category = models.CharField(max_length=100, blank=True, null=True)
	body_part = models.CharField(max_length=100, blank=True, null=True)
	equipment = models.CharField(max_length=100, blank=True, null=True)
	muscle_group = models.CharField(max_length=120, blank=True, null=True)
	secondary_muscles = models.JSONField(default=list, blank=True)
	target_muscle = models.CharField(max_length=100, blank=True, null=True)
	instruction_steps = models.JSONField(blank=True, null=True)
	media_id = models.CharField(max_length=64, blank=True, null=True)
	image_url = models.URLField(max_length=500, blank=True, null=True)
	image_upload = models.ImageField(upload_to='exercise_dataset/images/', blank=True, null=True)
	attribution = models.CharField(max_length=255, blank=True, null=True)
	dataset_created_at = models.DateTimeField(blank=True, null=True)
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='exercises')
	is_public = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	instructions = models.JSONField(blank=True, null=True)
	gif_url = models.URLField(max_length=500, blank=True, null=True)

	class Meta:
		ordering = ['name']
		constraints = [
			models.CheckConstraint(condition=~models.Q(name=''), name='exercise_name_not_blank'),
			models.UniqueConstraint(Lower('name'), name='exercise_name_unique_ci'),
		]
		indexes = [
			models.Index(fields=['image_url']),
			models.Index(fields=['image_upload']),
			models.Index(fields=['name']),
			models.Index(fields=['dataset_id']),
			models.Index(fields=['category']),
			models.Index(fields=['body_part']),
			models.Index(fields=['equipment']),
			models.Index(fields=['muscle_group']),
			models.Index(fields=['media_id']),
			models.Index(fields=['is_public']),
			models.Index(fields=['created_by']),
			models.Index(fields=['target_muscle']),
			models.Index(fields=['created_at']),
			models.Index(fields=['updated_at']),
			models.Index(fields=['created_by', 'is_public']),
		]

	def __str__(self):
		return self.name

class ExerciseProgram(models.Model):
	"""
	A reusable exercise program that can be private or shared with other users.
	"""

	DIFFICULTY_CHOICES = [
		('beginner', 'Beginner'),
		('intermediate', 'Intermediate'),
		('advanced', 'Advanced'),
		('all levels', 'All Levels'),
	]

	DURATION_WEEKS_CHOICES = [
		(1, '1'),
		(2, '2'),
		(3, '3'),
		(4, '4'),
		(5, '5'),
		(6, '6'),
		(7, '7'),
		(8, '8'),
		(9, '9'),
		(10, '10'),
		(11, '11'),
		(12, '12'),
	]

	created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='exercise_programs')
	name = models.CharField(
		max_length=120,
		validators=[MinLengthValidator(2)]
	)
	description = models.TextField(blank=True)
	exercises = models.ManyToManyField(Exercise, verbose_name=("Exercises"))
	difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='all levels')
	duration_weeks = models.PositiveSmallIntegerField(choices=DURATION_WEEKS_CHOICES, default=1)
	program_image = models.ImageField(upload_to='exercise_program_images/', blank=False)
	is_public = models.BooleanField(default=False)
	note = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)


	class Meta:
		ordering = ['name']
		constraints = [
			models.CheckConstraint(condition=~models.Q(name=''), name='exercise_program_name_not_blank'),
			models.UniqueConstraint(Lower('name'), 'created_by', name='exercise_program_name_unique_ci'),
		]
		indexes = [
			models.Index(fields=['name']),
			models.Index(fields=['difficulty']),
			models.Index(fields=['duration_weeks']),
			models.Index(fields=['created_by']),
			models.Index(fields=['is_public']),
			models.Index(fields=['created_at']),
			models.Index(fields=['updated_at']),
			models.Index(fields=['created_by', 'is_public']),
		]

	def __str__(self):
		return f"{self.name} ({self.created_by.username})"


class ExerciseProgramItem(models.Model):
	"""
	A single exercise entry inside a program.
	"""
	program = models.ForeignKey(ExerciseProgram, on_delete=models.CASCADE, related_name='items')
	exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, null=True, blank=True, related_name='program_items')
	position = models.PositiveIntegerField(default=1)
	week = models.PositiveIntegerField(null=True, blank=True)
	day = models.PositiveIntegerField(null=True, blank=True)
	sets = models.PositiveIntegerField(null=True, blank=True)
	reps = models.CharField(max_length=50, blank=True)
	load = models.CharField(max_length=50, blank=True)
	rest_seconds = models.PositiveIntegerField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['position', 'id']
		constraints = [
			models.CheckConstraint(
				condition=(
					(models.Q(exercise__isnull=False))
				),
				name='exercise_program_item_single_target'
			),
			models.UniqueConstraint(fields=['program', 'position'], name='exercise_program_item_position_unique'),
		]
		indexes = [
			models.Index(fields=['program']),
			models.Index(fields=['exercise']),
			models.Index(fields=['position']),
			models.Index(fields=['week']),
			models.Index(fields=['day']),
		]

	def __str__(self):
		target = self.exercise.name if self.exercise_id else 'Unknown Exercise'
		return f"{self.program.name} #{self.position} - {target}"
