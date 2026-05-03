from django.contrib import admin

from .models import CustomExercise, Exercise, ExerciseNote, ExerciseProgram, ExerciseProgramItem


admin.site.register(Exercise)
admin.site.register(CustomExercise)
admin.site.register(ExerciseNote)
admin.site.register(ExerciseProgram)
admin.site.register(ExerciseProgramItem)
