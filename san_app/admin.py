# admin.py
from django.contrib import admin
from .models import Participant, Response

@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'birth_date', 'user')
    search_fields = ('name', 'user__username')

@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('participant', 'phase', 'timestamp', 'wellbeing_score', 'activity_score', 'mood_score', 'overall_score')
    list_filter = ('phase', 'participant__gender')
    search_fields = ('participant__name',)