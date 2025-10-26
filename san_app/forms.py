from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Participant, Response


class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['name', 'gender', 'birth_date']
        labels = {
            'name': 'Фамилия, инициалы',
            'gender': 'Пол',
            'birth_date': 'Дата рождения'
        }
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ParticipantForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class ResponseForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = ['phase'] + [f'q{i}' for i in range(1, 31)]
        widgets = {}
        labels = {
            'phase': 'Фаза тестирования'
        }
        for i in range(1, 31):
            widgets[f'q{i}'] = forms.RadioSelect(choices=[
                (3, '3'), (2, '2'), (1, '1'), (0, '0'),
                (-1, '-1'), (-2, '-2'), (-3, '-3')
            ])

    phase = forms.ChoiceField(
        choices=Response.phase.field.choices,
        widget=forms.Select,
        label='Фаза тестирования'
    )


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Электронная почта")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        labels = {
            "username": "Имя пользователя",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"