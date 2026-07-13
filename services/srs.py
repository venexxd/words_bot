"""Интервальное повторение (Spaced Repetition).

Ступени: 1 → 3 → 7 → 14 → 30 → 60 дней.
Ошибка откатывает на 2 ступени назад и возвращает слово через 10 минут.
Слово считается выученным со ступени LEARNED_STAGE.
"""
from datetime import datetime, timedelta

from database.models import Progress

INTERVALS_DAYS = [1, 3, 7, 14, 30, 60]
LEARNED_STAGE = 3  # ответил верно минимум на интервалах 1, 3 и 7 дней


def apply_answer(progress: Progress, correct: bool) -> None:
    now = datetime.utcnow()
    progress.last_seen = now
    if correct:
        progress.correct = (progress.correct or 0) + 1
        stage = min(progress.stage or 0, len(INTERVALS_DAYS) - 1)
        progress.next_review = now + timedelta(days=INTERVALS_DAYS[stage])
        progress.stage = min((progress.stage or 0) + 1, len(INTERVALS_DAYS))
    else:
        progress.wrong = (progress.wrong or 0) + 1
        progress.stage = max(0, (progress.stage or 0) - 2)
        progress.next_review = now + timedelta(minutes=10)


def is_learned(progress: Progress) -> bool:
    return (progress.stage or 0) >= LEARNED_STAGE
