from django.contrib import admin

from .models import Exercise, ExerciseProgram, ExerciseProgramItem


admin.site.register(Exercise)
admin.site.register(ExerciseProgram)
admin.site.register(ExerciseProgramItem)
