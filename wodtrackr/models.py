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
	]

	title = models.CharField(
		max_length=120,
		unique=True,
		validators=[MinLengthValidator(2)]
	)
	difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='beginner')
	description = models.TextField(blank=True)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
	equipment = models.CharField(max_length=20, choices=EQUIPMENT_CHOICES, default='bodyweight')
	primary_muscle_group = models.CharField(max_length=50, choices=Primary_Muscle_Choices, blank=True)
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='exercises')
	is_public = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['title']
		constraints = [
			models.CheckConstraint(condition=~models.Q(title=''), name='exercise_name_not_blank'),
			models.UniqueConstraint(Lower('title'), name='exercise_name_unique_ci'),
		]
		indexes = [
			models.Index(fields=['title']),
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
		return self.title

class ExerciseProgram(models.Model):
	"""
	A reusable exercise program that can be private or shared with other users.
	"""
	CATEGORY_CHOICES = Exercise.CATEGORY_CHOICES
	Primary_Muscle_Choices = Exercise.Primary_Muscle_Choices
	GOAL_CHOICES = Exercise.GOAL_CHOICES
	EQUIPMENT_CHOICES = Exercise.EQUIPMENT_CHOICES

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
	title = models.CharField(
		max_length=120,
		validators=[MinLengthValidator(2)]
	)
	description = models.TextField(blank=True)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
	equipment = models.CharField(max_length=20, choices=EQUIPMENT_CHOICES, blank=True)
	primary_muscle_group = models.CharField(max_length=50, choices=Primary_Muscle_Choices, blank=True)
	goal = models.CharField(max_length=20, choices=GOAL_CHOICES, default='other')
	difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='all levels')
	duration_weeks = models.PositiveSmallIntegerField(choices=DURATION_WEEKS_CHOICES, default=1)
	program_image = models.ImageField(upload_to='exercise_program_images/', blank=False)
	is_public = models.BooleanField(default=False)
	note = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)


	class Meta:
		ordering = ['title']
		constraints = [
			models.CheckConstraint(condition=~models.Q(title=''), name='exercise_program_name_not_blank'),
			models.UniqueConstraint(Lower('title'), 'created_by', name='exercise_program_name_unique_ci'),
		]
		indexes = [
			models.Index(fields=['title']),
			models.Index(fields=['category']),
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
		return f"{self.title} ({self.created_by.username})"


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
		target = self.exercise.title if self.exercise_id else self.custom_exercise.title
		return f"{self.program.title} #{self.position} - {target}"
