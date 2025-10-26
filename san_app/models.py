# models.py (полный код с изменениями)
from django.contrib.auth.models import User
from django.db import models
from datetime import date  # Добавьте импорт

class Participant(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="participants", null=True, blank=True)
    name = models.CharField(max_length=100, verbose_name="Фамилия, инициалы")
    gender = models.CharField(max_length=1, choices=[('M', 'Мужской'), ('F', 'Женский')], verbose_name="Пол")
    birth_date = models.DateField(verbose_name="Дата рождения")

    def __str__(self):
        return f"{self.name} ({self.gender})"

    @property
    def age(self):
        today = date.today()
        return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))

# Остальной код модели Response без изменений...

class Response(models.Model):
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name="responses")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Дата и время")
    phase = models.CharField(max_length=10, choices=[('before', 'До занятия'), ('after', 'После занятия')], verbose_name="Фаза")

    # Поля для 30 вопросов (-3 до +3)
    q1 = models.IntegerField(default=0, verbose_name="1. Самочувствие хорошее / плохое")
    q2 = models.IntegerField(default=0, verbose_name="2. Сильный / слабый")
    q3 = models.IntegerField(default=0, verbose_name="3. Пассивный / активный")
    q4 = models.IntegerField(default=0, verbose_name="4. Малоподвижный / подвижный")
    q5 = models.IntegerField(default=0, verbose_name="5. Веселый / грустный")
    q6 = models.IntegerField(default=0, verbose_name="6. Хорошее настроение / плохое")
    q7 = models.IntegerField(default=0, verbose_name="7. Работоспособный / разбитый")
    q8 = models.IntegerField(default=0, verbose_name="8. Полный сил / обессиленный")
    q9 = models.IntegerField(default=0, verbose_name="9. Медлительный / быстрый")
    q10 = models.IntegerField(default=0, verbose_name="10. Бездеятельный / деятельный")
    q11 = models.IntegerField(default=0, verbose_name="11. Счастливый / несчастный")
    q12 = models.IntegerField(default=0, verbose_name="12. Жизнерадостный / мрачный")
    q13 = models.IntegerField(default=0, verbose_name="13. Напряженный / расслабленный")
    q14 = models.IntegerField(default=0, verbose_name="14. Здоровый / больной")
    q15 = models.IntegerField(default=0, verbose_name="15. Безучастный / увлеченный")
    q16 = models.IntegerField(default=0, verbose_name="16. Равнодушный / взволнованный")
    q17 = models.IntegerField(default=0, verbose_name="17. Восторженный / унылый")
    q18 = models.IntegerField(default=0, verbose_name="18. Радостный / печальный")
    q19 = models.IntegerField(default=0, verbose_name="19. Отдохнувший / усталый")
    q20 = models.IntegerField(default=0, verbose_name="20. Свежий / изнуренный")
    q21 = models.IntegerField(default=0, verbose_name="21. Сонливый / возбужденный")
    q22 = models.IntegerField(default=0, verbose_name="22. Желание отдохнуть / работать")
    q23 = models.IntegerField(default=0, verbose_name="23. Спокойный / озабоченный")
    q24 = models.IntegerField(default=0, verbose_name="24. Оптимистичный / пессимистичный")
    q25 = models.IntegerField(default=0, verbose_name="25. Выносливый / утомляемый")
    q26 = models.IntegerField(default=0, verbose_name="26. Бодрый / вялый")
    q27 = models.IntegerField(default=0, verbose_name="27. Соображать трудно / легко")
    q28 = models.IntegerField(default=0, verbose_name="28. Рассеянный / внимательный")
    q29 = models.IntegerField(default=0, verbose_name="29. Полный надежд / разочарованный")
    q30 = models.IntegerField(default=0, verbose_name="30. Довольный / недовольный")

    # Константы для расчёта (True - левый полюс положительный)

    POLARITIES = [
        True, True, False, False, True, True, True, True, False, False,
        True, True, False, True, False, False, True, True, True, True,
        False, False, True, True, True, True, False, False, True, True
    ]

    WELLBEING_ITEMS = [1, 2, 7, 8, 13, 14, 19, 20, 25, 26]
    ACTIVITY_ITEMS = [3, 4, 9, 10, 15, 16, 21, 22, 27, 28]
    MOOD_ITEMS = [5, 6, 11, 12, 17, 18, 23, 24, 29, 30]

    def get_score(self, q_num):
        value = getattr(self, f'q{q_num}')
        is_left_pos = self.POLARITIES[q_num - 1]
        if is_left_pos:
            return 4 + value  # +3 -> 7, -3 -> 1
        else:
            return 4 - value  # +3 -> 1, -3 -> 7

    @property
    def wellbeing_score(self):
        scores = [self.get_score(i) for i in self.WELLBEING_ITEMS]
        return sum(scores) / 10

    @property
    def activity_score(self):
        scores = [self.get_score(i) for i in self.ACTIVITY_ITEMS]
        return sum(scores) / 10

    @property
    def mood_score(self):
        scores = [self.get_score(i) for i in self.MOOD_ITEMS]
        return sum(scores) / 10

    @property
    def overall_score(self):
        scores = [self.get_score(i) for i in range(1, 31)]
        return sum(scores) / 30

    def __str__(self):
        return f"{self.participant} - {self.phase} - {self.timestamp}"