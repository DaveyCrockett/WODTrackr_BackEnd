from django.urls import path
from rest_framework import views
from . import views

urlpatterns = [
    path('exercises/choices/', views.exercise_choices, name='exercise_choices'),
    path('equipment/', views.equipment_list, name='equipment_list'),
    path('equipment/<int:equipment_id>/', views.equipment_detail, name='equipment_detail'),
    path('exercises/', views.exercises, name='exercises'),
    path('exercises/<int:exercise_id>/', views.exercise_detail, name='exercise_detail'),
    path('custom-exercises/', views.custom_exercises, name='custom_exercises'),
    path('custom-exercises/<int:custom_exercise_id>/', views.custom_exercise_detail, name='custom_exercise_detail'),
    path('exercise-notes/', views.exercise_notes, name='exercise_notes'),
    path('exercise-notes/<int:note_id>/', views.exercise_note_detail, name='exercise_note_detail'),
    path('exercise-programs/choices/', views.exercise_program_choices, name='exercise_program_choices'),
    path('exercise-programs/', views.exercise_programs, name='exercise_programs'),
    path('exercise-programs/<int:program_id>/', views.exercise_program_detail, name='exercise_program_detail'),
    path('exercise-programs/<int:program_id>/item/', views.exercise_program_item, name='exercise_program_item'),
    path('exercise-programs/<int:program_id>/reuse/', views.exercise_program_reuse, name='exercise_program_reuse'),
]


