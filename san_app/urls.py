from django.urls import path
from .views import create_participant, take_survey, report

urlpatterns = [
    path('new_participant/', create_participant, name='new_participant'),
    path('survey/<int:participant_id>/', take_survey, name='take_survey'),
    path('report/', report, name='report'),
]