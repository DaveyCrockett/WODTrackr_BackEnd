from django.db import models
from django.contrib.auth.models import User


class Exercise(models.Model):
	"""
	Represents a single exercise definition.
	"""
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

	name = models.CharField(max_length=120, unique=True)
	description = models.TextField(blank=True)
	category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
	equipment = models.CharField(max_length=20, choices=EQUIPMENT_CHOICES, default='bodyweight')
	primary_muscle_group = models.CharField(max_length=50, blank=True)
	created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='exercises')
	is_public = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name