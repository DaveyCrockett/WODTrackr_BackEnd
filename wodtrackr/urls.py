from django.urls import path
from .views import exercises, exercise_detail

urlpatterns = [
    path('exercises/', exercises, name='exercises'),
    path('exercises/<int:exercise_id>/', exercise_detail, name='exercise_detail'),
]
