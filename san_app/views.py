from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ParticipantForm, ResponseForm
from .models import Participant, Response
import pandas as pd
import matplotlib

matplotlib.use('Agg')  # Используем non-GUI backend
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import seaborn as sns
from datetime import datetime
from django.contrib.auth import login, logout
from .forms import CustomUserCreationForm
from django.contrib.auth.views import LoginView as AuthLoginView
from django.http import HttpResponseForbidden
from django.contrib import messages

QUESTIONS = [
    {"num": 1, "left": "Самочувствие хорошее", "right": "Самочувствие плохое"},
    {"num": 2, "left": "Чувствую себя сильным", "right": "Чувствую себя слабым"},
    {"num": 3, "left": "Пассивный", "right": "Активный"},
    {"num": 4, "left": "Малоподвижный", "right": "Подвижный"},
    {"num": 5, "left": "Веселый", "right": "Грустный"},
    {"num": 6, "left": "Хорошее настроение", "right": "Плохое настроение"},
    {"num": 7, "left": "Работоспособный", "right": "Разбитый"},
    {"num": 8, "left": "Полный сил", "right": "Обессиленный"},
    {"num": 9, "left": "Медлительный", "right": "Быстрый"},
    {"num": 10, "left": "Бездеятельный", "right": "Деятельный"},
    {"num": 11, "left": "Счастливый", "right": "Несчастный"},
    {"num": 12, "left": "Жизнерадостный", "right": "Мрачный"},
    {"num": 13, "left": "Напряженный", "right": "Расслабленный"},
    {"num": 14, "left": "Здоровый", "right": "Больной"},
    {"num": 15, "left": "Безучастный", "right": "Увлеченный"},
    {"num": 16, "left": "Равнодушный", "right": "Взволнованный"},
    {"num": 17, "left": "Восторженный", "right": "Унылый"},
    {"num": 18, "left": "Радостный", "right": "Печальный"},
    {"num": 19, "left": "Отдохнувший", "right": "Усталый"},
    {"num": 20, "left": "Свежий", "right": "Изнуренный"},
    {"num": 21, "left": "Сонливый", "right": "Возбужденный"},
    {"num": 22, "left": "Желание отдохнуть", "right": "Желание работать"},
    {"num": 23, "left": "Спокойный", "right": "Озабоченный"},
    {"num": 24, "left": "Оптимистичный", "right": "Пессимистичный"},
    {"num": 25, "left": "Выносливый", "right": "Утомляемый"},
    {"num": 26, "left": "Бодрый", "right": "Вялый"},
    {"num": 27, "left": "Соображать трудно", "right": "Соображать легко"},
    {"num": 28, "left": "Рассеянный", "right": "Внимательный"},
    {"num": 29, "left": "Полный надежд", "right": "Разочарованный"},
    {"num": 30, "left": "Довольный", "right": "Недовольный"},
]


def is_admin(user):
    return user.is_authenticated and user.is_staff


@login_required
def home(request):
    """Главная страница - редирект в зависимости от роли пользователя"""
    if request.user.is_staff:
        return redirect('admin_dashboard')
    else:
        return redirect('profile')


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Главная панель администратора"""
    total_participants = Participant.objects.count()
    total_responses = Response.objects.count()
    responses_before = Response.objects.filter(phase='before').count()
    responses_after = Response.objects.filter(phase='after').count()

    # Последние 10 ответов
    recent_responses = Response.objects.select_related('participant').order_by('-timestamp')[:10]

    context = {
        'total_participants': total_participants,
        'total_responses': total_responses,
        'responses_before': responses_before,
        'responses_after': responses_after,
        'recent_responses': recent_responses,
    }

    return render(request, 'admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def participants_list(request):
    """Список всех участников"""
    participants = Participant.objects.all().order_by('-id')

    # Добавляем статистику по каждому участнику
    participants_data = []
    for p in participants:
        participants_data.append({
            'participant': p,
            'responses_count': p.responses.count(),
            'last_response': p.responses.order_by('-timestamp').first(),
        })

    return render(request, 'participants_list.html', {'participants_data': participants_data})


@login_required
@user_passes_test(is_admin)
def responses_list(request):
    """Список всех ответов"""
    responses = Response.objects.select_related('participant').order_by('-timestamp')

    return render(request, 'responses_list.html', {'responses': responses})


@login_required
def profile(request):
    """Страница профиля - здесь пользователь проверяет/редактирует свои данные"""
    # Если это админ, редиректим на админ-панель
    if request.user.is_staff:
        return redirect('admin_dashboard')

    participant = Participant.objects.filter(user=request.user).first()

    if not participant:
        # Создаем участника с минимальными данными при первом входе
        participant = Participant.objects.create(
            user=request.user,
            name=request.user.username,
            gender="M",
            birth_date=datetime.now().date()
        )

    if request.method == 'POST':
        form = ParticipantForm(request.POST, instance=participant)
        if form.is_valid():
            form.save()
            # После сохранения данных перенаправляем на тест
            return redirect('take_survey', participant_id=participant.id)
    else:
        form = ParticipantForm(instance=participant)

    return render(request, 'profile.html', {'form': form, 'participant': participant})


@login_required
def create_participant(request):
    """Эта view больше не используется - всегда редирект на профиль"""
    return redirect('profile')


@login_required
def take_survey(request, participant_id=None):
    """Страница прохождения опроса САН"""
    # Получаем участника
    if participant_id:
        participant = get_object_or_404(Participant, id=participant_id)
        # Проверка безопасности: участник должен принадлежать текущему пользователю
        if participant.user != request.user and not request.user.is_staff:
            return HttpResponseForbidden("У вас нет доступа к этому участнику.")
    else:
        participant = Participant.objects.filter(user=request.user).first()
        if not participant:
            # Если участника нет, отправляем в профиль для создания
            return redirect('profile')

    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.participant = participant
            response.save()

            wellbeing = response.wellbeing_score
            activity = response.activity_score
            mood = response.mood_score
            overall = response.overall_score

            return render(request, 'take_survey.html', {
                'form': ResponseForm(),
                'participant': participant,
                'questions': QUESTIONS,
                'show_result': True,
                'wellbeing': wellbeing,
                'activity': activity,
                'mood': mood,
                'overall': overall
            })
    else:
        form = ResponseForm()

    return render(request, 'take_survey.html', {
        'form': form,
        'participant': participant,
        'questions': QUESTIONS
    })


@login_required
@user_passes_test(is_admin)
def report(request):
    """Страница с отчетами и графиками (только для администраторов)"""
    responses = Response.objects.all()

    if not responses.exists():
        return render(request, 'report.html', {
            'img_base64_list': [],
            'table_html': '<p>Нет данных для отображения.</p>',
            'error': 'Нет доступных данных для построения отчета.'
        })

    # Подготовка данных
    data = []
    for resp in responses:
        data.append({
            'participant': resp.participant.name,
            'gender': resp.participant.gender,
            'phase': resp.phase,
            'wellbeing': resp.wellbeing_score,
            'activity': resp.activity_score,
            'mood': resp.mood_score,
            'overall': resp.overall_score,
            'birth_date': resp.participant.birth_date,
            'timestamp': resp.timestamp,
        })

    df = pd.DataFrame(data)

    # Расчет возраста
    df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
    current_date = pd.to_datetime(datetime.now().date())
    df['age'] = (current_date - df['birth_date']).dt.days / 365.25
    df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0)

    # Конвертация score-колонок в числовой тип
    for col in ['wellbeing', 'activity', 'mood', 'overall']:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    img_base64_list = []

    # 1. Столбчатый график
    try:
        grouped = df.groupby(['gender', 'phase'])[['wellbeing', 'activity', 'mood']].mean()
        if not grouped.empty:
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            grouped.unstack().plot(kind='bar', ax=ax1)
            plt.title('Средние баллы САН до и после занятия по полу')
            plt.ylabel('Балл')
            plt.xlabel('Пол')
            plt.xticks(rotation=45)
            plt.legend(title='Показатель / Фаза')
            plt.tight_layout()
            buf1 = BytesIO()
            fig1.savefig(buf1, format='png', bbox_inches='tight')
            buf1.seek(0)
            img_base64_list.append(base64.b64encode(buf1.read()).decode('utf-8'))
            plt.close(fig1)
    except Exception as e:
        print(f"Ошибка при создании графика 1: {e}")

    # 2. Линейный график изменений
    try:
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        for gender in ['M', 'F']:
            gender_data = df[df['gender'] == gender].groupby('phase')[['wellbeing', 'activity', 'mood']].mean()
            if not gender_data.empty:
                gender_label = 'Мужской' if gender == 'M' else 'Женский'
                for metric in ['wellbeing', 'activity', 'mood']:
                    metric_label = {'wellbeing': 'Самочувствие', 'activity': 'Активность', 'mood': 'Настроение'}[metric]
                    ax2.plot(gender_data.index, gender_data[metric],
                             label=f'{metric_label} ({gender_label})', marker='o')
        plt.title('Динамика баллов САН по фазам и полу')
        plt.ylabel('Балл')
        plt.xlabel('Фаза')
        plt.legend()
        plt.tight_layout()
        buf2 = BytesIO()
        fig2.savefig(buf2, format='png', bbox_inches='tight')
        buf2.seek(0)
        img_base64_list.append(base64.b64encode(buf2.read()).decode('utf-8'))
        plt.close(fig2)
    except Exception as e:
        print(f"Ошибка при создании графика 2: {e}")

    # 3. Круговые диаграммы
    for gender in ['M', 'F']:
        for phase in ['before', 'after']:
            try:
                fig3, ax3 = plt.subplots(figsize=(6, 6))
                subset = df[(df['gender'] == gender) & (df['phase'] == phase)]['wellbeing']
                labels = ['>5', '4-5', '<4']
                sizes = [
                    len(subset[subset > 5.0]),
                    len(subset[(subset >= 4.0) & (subset <= 5.0)]),
                    len(subset[subset < 4.0])
                ]

                if sum(sizes) > 0:
                    ax3.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                    ax3.axis('equal')
                    gender_label = 'Мужской' if gender == 'M' else 'Женский'
                    phase_label = 'До занятия' if phase == 'before' else 'После занятия'
                    plt.title(f'{gender_label} - {phase_label}\n(Самочувствие)')
                else:
                    ax3.text(0.5, 0.5, 'Нет данных', horizontalalignment='center',
                             verticalalignment='center', transform=ax3.transAxes)
                    ax3.axis('equal')
                    plt.title(f'{gender} - {phase} (Нет данных)')

                plt.tight_layout()
                buf3 = BytesIO()
                fig3.savefig(buf3, format='png', bbox_inches='tight')
                buf3.seek(0)
                img_base64_list.append(base64.b64encode(buf3.read()).decode('utf-8'))
                plt.close(fig3)
            except Exception as e:
                print(f"Ошибка при создании круговой диаграммы {gender}-{phase}: {e}")

    # 4. График рассеяния
    try:
        fig4, ax4 = plt.subplots(figsize=(10, 6))
        for phase in ['before', 'after']:
            subset = df[df['phase'] == phase]
            if not subset.empty:
                phase_label = 'До занятия' if phase == 'before' else 'После занятия'
                ax4.scatter(subset['age'], subset['overall'], label=phase_label, alpha=0.6, s=50)
        plt.title('Общий балл vs Возраст по фазам')
        plt.ylabel('Общий балл')
        plt.xlabel('Возраст (лет)')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        buf4 = BytesIO()
        fig4.savefig(buf4, format='png', bbox_inches='tight')
        buf4.seek(0)
        img_base64_list.append(base64.b64encode(buf4.read()).decode('utf-8'))
        plt.close(fig4)
    except Exception as e:
        print(f"Ошибка при создании графика 4: {e}")

    # 5. Ящик с усами
    try:
        fig5, ax5 = plt.subplots(figsize=(10, 6))
        df.boxplot(column=['wellbeing', 'activity', 'mood'], by='phase', ax=ax5)
        plt.title('Распределение баллов по фазам')
        plt.suptitle('')
        plt.ylabel('Балл')
        plt.xlabel('Фаза')
        plt.tight_layout()
        buf5 = BytesIO()
        fig5.savefig(buf5, format='png', bbox_inches='tight')
        buf5.seek(0)
        img_base64_list.append(base64.b64encode(buf5.read()).decode('utf-8'))
        plt.close(fig5)
    except Exception as e:
        print(f"Ошибка при создании графика 5: {e}")

    # 6. Тепловая карта корреляции
    try:
        fig6, ax6 = plt.subplots(figsize=(8, 6))
        correlation_matrix = df[['wellbeing', 'activity', 'mood', 'age']].corr()
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm',
                    vmin=-1, vmax=1, center=0, ax=ax6, fmt='.2f')
        plt.title('Корреляция между баллами и возрастом')
        plt.tight_layout()
        buf6 = BytesIO()
        fig6.savefig(buf6, format='png', bbox_inches='tight')
        buf6.seek(0)
        img_base64_list.append(base64.b64encode(buf6.read()).decode('utf-8'))
        plt.close(fig6)
    except Exception as e:
        print(f"Ошибка при создании графика 6: {e}")

    # Таблица в HTML
    try:
        grouped = df.groupby(['gender', 'phase'])[['wellbeing', 'activity', 'mood']].mean()
        table_html = grouped.to_html(float_format='%.2f')
    except Exception as e:
        table_html = f'<p>Ошибка при создании таблицы: {e}</p>'

    return render(request, 'report.html', {
        'img_base64_list': img_base64_list,
        'table_html': table_html
    })


def register(request):
    """Регистрация нового пользователя"""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Автоматически логиним пользователя после регистрации
            login(request, user)
            # Перенаправляем в профиль для заполнения данных
            return redirect('profile')
    else:
        form = CustomUserCreationForm()

    return render(request, "register.html", {"form": form})


class CustomLoginView(AuthLoginView):
    """Кастомный view для входа с перенаправлением на профиль или админ-панель"""

    def get_success_url(self):
        # После входа перенаправляем в зависимости от роли
        if self.request.user.is_staff:
            return '/admin-dashboard/'
        return '/profile/'


def logout_view(request):
    """Выход из системы с перенаправлением на страницу входа"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('login')