from django.shortcuts import render, redirect, get_object_or_404
from .forms import ParticipantForm, ResponseForm
from .models import Participant, Response
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import seaborn as sns
from datetime import datetime

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

def create_participant(request):
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save()
            return redirect('take_survey', participant_id=participant.id)
    else:
        form = ParticipantForm()
    return render(request, 'create_participant.html', {'form': form})

def take_survey(request, participant_id):
    participant = get_object_or_404(Participant, id=participant_id)
    if request.method == 'POST':
        form = ResponseForm(request.POST)
        if form.is_valid():
            response = form.save(commit=False)
            response.participant = participant
            response.save()
            return redirect('report')
    else:
        form = ResponseForm()
    return render(request, 'take_survey.html', {'form': form, 'participant': participant, 'questions': QUESTIONS})

def report(request):
    # Собираем данные в DataFrame
    responses = Response.objects.all()
    if not responses.exists():
        return render(request, 'report.html', {
            'img_base64_list': [],
            'table_html': '<p>Нет данных для отображения.</p>',
            'error': 'Нет доступных данных для построения отчета.'
        })

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

    # Конвертация birth_date в pandas datetime и расчет возраста
    df['birth_date'] = pd.to_datetime(df['birth_date'], errors='coerce')
    current_date = pd.to_datetime(datetime.now().date())  # 02:11 PM CET, October 26, 2025
    df['age'] = (current_date - df['birth_date']).dt.days / 365.25  # Примерный возраст
    df['age'] = pd.to_numeric(df['age'], errors='coerce').fillna(0)

    # Конвертация score-колонок в числовой тип
    for col in ['wellbeing', 'activity', 'mood', 'overall']:
        df[col] = (
            df[col]
            .astype(str)  # Преобразуем в строку
            .str.replace(',', '.', regex=False)  # Заменяем запятые на точки
            .apply(lambda x: x.strip() if isinstance(x, str) else x)  # Удаляем пробелы
            .replace('', '0')  # Заменяем пустые строки на '0'
            .pipe(pd.to_numeric, errors='coerce')  # Конвертируем в float
            .fillna(0)  # Заменяем NaN на 0
        )

    # Список для хранения base64 изображений
    img_base64_list = []

    # 1. Столбчатый график
    grouped = df.groupby(['gender', 'phase'])[['wellbeing', 'activity', 'mood']].mean().unstack()
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    grouped.plot(kind='bar', ax=ax1)
    plt.title('Средние баллы САН до и после занятия по полу')
    plt.ylabel('Балл')
    plt.xlabel('Пол / Фаза')
    plt.xticks(rotation=45)
    buf1 = BytesIO()
    fig1.savefig(buf1, format='png', bbox_inches='tight')
    buf1.seek(0)
    img_base64_list.append(base64.b64encode(buf1.read()).decode('utf-8'))
    plt.close(fig1)

    # 2. Линейный график изменений
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    for gender in ['M', 'F']:
        gender_data = df[df['gender'] == gender].groupby('phase')[['wellbeing', 'activity', 'mood']].mean()
        for metric in ['wellbeing', 'activity', 'mood']:
            if not gender_data.empty:
                ax2.plot(gender_data.index, gender_data[metric], label=f'{metric} {gender}', marker='o')
    plt.title('Динамика баллов САН по фазам и полу')
    plt.ylabel('Балл')
    plt.xlabel('Фаза')
    plt.legend()
    buf2 = BytesIO()
    fig2.savefig(buf2, format='png', bbox_inches='tight')
    buf2.seek(0)
    img_base64_list.append(base64.b64encode(buf2.read()).decode('utf-8'))
    plt.close(fig2)

    # 3. Круговые диаграммы
    for gender in ['M', 'F']:
        for phase in ['before', 'after']:
            fig3, ax3 = plt.subplots(figsize=(4, 4))
            subset = df[(df['gender'] == gender) & (df['phase'] == phase)]['wellbeing']
            labels = ['>5', '4-5', '<4']
            sizes = [
                len(subset[subset > 5.0]),
                len(subset[(subset >= 4.0) & (subset <= 5.0)]),
                len(subset[subset < 4.0])
            ]
            # Проверяем, есть ли ненулевые значения в sizes
            if sum(sizes) > 0:
                ax3.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                ax3.axis('equal')
                plt.title(f'{gender} - {phase}')
            else:
                # Если данных нет, создаем пустую диаграмму с сообщением
                ax3.text(0.5, 0.5, 'Нет данных', horizontalalignment='center', verticalalignment='center')
                ax3.axis('equal')
                plt.title(f'{gender} - {phase} (Нет данных)')
            buf3 = BytesIO()
            fig3.savefig(buf3, format='png', bbox_inches='tight')
            buf3.seek(0)
            img_base64_list.append(base64.b64encode(buf3.read()).decode('utf-8'))
            plt.close(fig3)

    # 4. График рассеяния
    fig4, ax4 = plt.subplots(figsize=(10, 6))
    for phase in ['before', 'after']:
        subset = df[df['phase'] == phase]
        if not subset.empty:
            ax4.scatter(subset['age'], subset['overall'], label=phase, alpha=0.5)
    plt.title('Overall Score vs Age by Phase')
    plt.ylabel('Overall Score')
    plt.xlabel('Age (years)')
    plt.legend()
    buf4 = BytesIO()
    fig4.savefig(buf4, format='png', bbox_inches='tight')
    buf4.seek(0)
    img_base64_list.append(base64.b64encode(buf4.read()).decode('utf-8'))
    plt.close(fig4)

    # 5. Ящик с усами
    fig5, ax5 = plt.subplots(figsize=(10, 6))
    df.boxplot(column=['wellbeing', 'activity', 'mood'], by='phase', ax=ax5)
    plt.title('Распределение баллов по фазам')
    plt.suptitle('')
    plt.ylabel('Балл')
    buf5 = BytesIO()
    fig5.savefig(buf5, format='png', bbox_inches='tight')
    buf5.seek(0)
    img_base64_list.append(base64.b64encode(buf5.read()).decode('utf-8'))
    plt.close(fig5)

    # 6. Тепловая карта корреляции
    fig6, ax6 = plt.subplots(figsize=(8, 6))
    correlation_matrix = df[['wellbeing', 'activity', 'mood', 'age']].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', vmin=-1, vmax=1, center=0)
    plt.title('Корреляция между баллами и возрастом')
    buf6 = BytesIO()
    fig6.savefig(buf6, format='png', bbox_inches='tight')
    buf6.seek(0)
    img_base64_list.append(base64.b64encode(buf6.read()).decode('utf-8'))
    plt.close(fig6)

    # Таблица в HTML
    table_html = grouped.to_html()

    return render(request, 'report.html', {'img_base64_list': img_base64_list, 'table_html': table_html})