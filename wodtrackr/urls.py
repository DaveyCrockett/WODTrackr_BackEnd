from django.urls import path
from .views import (
    exercises,
    exercise_choices,
    exercise_detail,
    custom_exercises,
    custom_exercise_detail,
    exercise_notes,
    exercise_note_detail,
)

urlpatterns = [
    path('exercises/choices/', exercise_choices, name='exercise_choices'),
    path('exercises/', exercises, name='exercises'),
    path('exercises/<int:exercise_id>/', exercise_detail, name='exercise_detail'),
    path('custom-exercises/', custom_exercises, name='custom_exercises'),
    path('custom-exercises/<int:custom_exercise_id>/', custom_exercise_detail, name='custom_exercise_detail'),
    path('exercise-notes/', exercise_notes, name='exercise_notes'),
    path('exercise-notes/<int:note_id>/', exercise_note_detail, name='exercise_note_detail'),
]
