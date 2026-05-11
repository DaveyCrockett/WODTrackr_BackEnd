from django.urls import path
from .views import (
    exercises,
    exercise_choices,
    exercise_detail,
    custom_exercises,
    custom_exercise_detail,
    exercise_notes,
    exercise_note_detail,
    exercise_programs,
    exercise_program_choices,
    exercise_program_detail,
    exercise_program_item,
    exercise_program_reuse,
)

urlpatterns = [
    path('exercises/choices/', exercise_choices, name='exercise_choices'),
    path('exercises/', exercises, name='exercises'),
    path('exercises/<int:exercise_id>/', exercise_detail, name='exercise_detail'),
    path('custom-exercises/', custom_exercises, name='custom_exercises'),
    path('custom-exercises/<int:custom_exercise_id>/', custom_exercise_detail, name='custom_exercise_detail'),
    path('exercise-notes/', exercise_notes, name='exercise_notes'),
    path('exercise-notes/<int:note_id>/', exercise_note_detail, name='exercise_note_detail'),
    path('exercise-programs/choices/', exercise_program_choices, name='exercise_program_choices'),
    path('exercise-programs/', exercise_programs, name='exercise_programs'),
    path('exercise-programs/<int:program_id>/', exercise_program_detail, name='exercise_program_detail'),
    path('exercise-programs/<int:program_id>/item/', exercise_program_item, name='exercise_program_item'),
    path('exercise-programs/<int:program_id>/reuse/', exercise_program_reuse, name='exercise_program_reuse'),
]
