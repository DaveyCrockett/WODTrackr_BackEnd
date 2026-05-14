from django.contrib import admin

from .models import CustomExercise, Exercise, ExerciseNote, ExerciseProgram, ExerciseProgramItem, Equipment


admin.site.register(Exercise)
admin.site.register(CustomExercise)
admin.site.register(ExerciseNote)
admin.site.register(Equipment)
admin.site.register(ExerciseProgram)
admin.site.register(ExerciseProgramItem)
