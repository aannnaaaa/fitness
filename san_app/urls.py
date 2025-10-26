from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Главная страница после входа - профиль или админ-панель
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),

    # Админ-панель
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('report/', views.report, name='report'),
    path('participants/', views.participants_list, name='participants_list'),
    path('responses/', views.responses_list, name='responses_list'),

    # Прохождение опроса
    path('survey/<int:participant_id>/', views.take_survey, name='take_survey'),

    # Аутентификация
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Устаревший URL для обратной совместимости (редирект на профиль)
    path('new_participant/', views.create_participant, name='new_participant'),
]