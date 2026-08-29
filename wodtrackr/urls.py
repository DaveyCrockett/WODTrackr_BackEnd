from django.urls import path
from rest_framework import views
from . import views

urlpatterns = [
    path('exercises/choices/', views.exercise_choices, name='exercise_choices'),
    path('exercises/', views.exercises, name='exercises'),
    path('exercises/<int:exercise_id>/', views.exercise_detail, name='exercise_detail'),
    path('exercise-programs/choices/', views.exercise_program_choices, name='exercise_program_choices'),
    path('exercise-programs/', views.exercise_programs, name='exercise_programs'),
    path('exercise-programs/<int:program_id>/', views.exercise_program_detail, name='exercise_program_detail'),
    path('exercise-programs/<int:program_id>/item/', views.exercise_program_item, name='exercise_program_item'),
    path('exercise-programs/<int:program_id>/reuse/', views.exercise_program_reuse, name='exercise_program_reuse'),
]


