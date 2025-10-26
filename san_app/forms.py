from django import forms
from .models import Participant, Response

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['name', 'gender', 'birth_date']

class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['phase'] + [f'q{i}' for i in range(1, 31)]
        widgets = {}
        for i in range(1, 31):
            widgets[f'q{i}'] = forms.RadioSelect(choices=[
                (3, '3'), (2, '2'), (1, '1'), (0, '0'),
                (-1, '1'), (-2, '2'), (-3, '3')
            ])

    phase = forms.ChoiceField(choices=Response.phase.field.choices, widget=forms.Select)