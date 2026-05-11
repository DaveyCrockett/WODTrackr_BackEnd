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
			models.Index(fields=['primary_muscle_group']),
			models.Index(fields=['created_at']),
			models.Index(fields=['updated_at']),
			models.Index(fields=['created_by', 'is_public']),
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
	name = models.CharField(
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
		ordering = ['name']
		constraints = [
			models.CheckConstraint(condition=~models.Q(name=''), name='custom_exercise_name_not_blank'),
			models.UniqueConstraint(Lower('name'), 'created_by', name='custom_exercise_name_unique_ci'),
		]
		indexes = [
			models.Index(fields=['name']),
			models.Index(fields=['category']),
			models.Index(fields=['equipment']),
			models.Index(fields=['created_by']),
			models.Index(fields=['primary_muscle_group']),
		]

	def __str__(self):
		return f"{self.name} ({self.created_by.username})"


class ExerciseProgram(models.Model):
	"""
	A reusable exercise program that can be private or shared with other users.
	"""
	CATEGORY_CHOICES = Exercise.CATEGORY_CHOICES
	EQUIPMENT_CHOICES = Exercise.EQUIPMENT_CHOICES
	Primary_Muscle_Choices = Exercise.Primary_Muscle_Choices
	GOAL_CHOICES = [
		('strength', 'Strength'),
		('hypertrophy', 'Hypertrophy'),
		('endurance', 'Endurance'),
		('fat_loss', 'Fat Loss'),
		('mobility', 'Mobility'),
		('performance', 'Performance'),
		('general_fitness', 'General Fitness'),
		('other', 'Other'),
	]

	DIFFICULTY_CHOICES = [
		('beginner', 'Beginner'),
		('intermediate', 'Intermediate'),
		('advanced', 'Advanced'),
		('all_levels', 'All Levels'),
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
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
	equipment = models.CharField(max_length=20, choices=EQUIPMENT_CHOICES, default='bodyweight')
	primary_muscle_group = models.CharField(max_length=50, choices=Primary_Muscle_Choices, blank=True)
	goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='other')
	difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='all levels')
	duration_weeks = models.PositiveSmallIntegerField(choices=DURATION_WEEKS_CHOICES, default=1)
	is_public = models.BooleanField(default=False)
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
			models.Index(fields=['category']),
			models.Index(fields=['equipment']),
			models.Index(fields=['primary_muscle_group']),
			models.Index(fields=['goal']),
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
	custom_exercise = models.ForeignKey(CustomExercise, on_delete=models.CASCADE, null=True, blank=True, related_name='program_items')
	position = models.PositiveIntegerField(default=1)
	week = models.PositiveIntegerField(null=True, blank=True)
	day = models.PositiveIntegerField(null=True, blank=True)
	sets = models.PositiveIntegerField(null=True, blank=True)
	reps = models.CharField(max_length=50, blank=True)
	load = models.CharField(max_length=50, blank=True)
	rest_seconds = models.PositiveIntegerField(null=True, blank=True)
	notes = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['position', 'id']
		constraints = [
			models.CheckConstraint(
				condition=(
					(models.Q(exercise__isnull=False) & models.Q(custom_exercise__isnull=True)) |
					(models.Q(exercise__isnull=True) & models.Q(custom_exercise__isnull=False))
				),
				name='exercise_program_item_single_target'
			),
			models.UniqueConstraint(fields=['program', 'position'], name='exercise_program_item_position_unique'),
		]
		indexes = [
			models.Index(fields=['program']),
			models.Index(fields=['exercise']),
			models.Index(fields=['custom_exercise']),
			models.Index(fields=['position']),
			models.Index(fields=['week']),
			models.Index(fields=['day']),
		]

	def __str__(self):
		target = self.exercise.name if self.exercise_id else self.custom_exercise.name
		return f"{self.program.name} #{self.position} - {target}"


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
		target = self.exercise.name if self.exercise_id else self.custom_exercise.name
		return f"Notes: {self.user.username} - {target}"