"""Модели базы данных (SQLAlchemy 2.0). Работают и с SQLite, и с PostgreSQL."""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import (
    JSON, BigInteger, Boolean, Date, DateTime, ForeignKey, Index, Integer,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)  # Telegram ID
    username: Mapped[Optional[str]] = mapped_column(String(64))
    first_name: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Настройки
    level: Mapped[str] = mapped_column(String(8), default="all")        # A1..C2 / all
    direction: Mapped[str] = mapped_column(String(8), default="en_ru")  # en_ru / ru_en
    mode: Mapped[str] = mapped_column(String(16), default="normal")
    topic: Mapped[Optional[str]] = mapped_column(String(64))
    daily_goal: Mapped[int] = mapped_column(Integer, default=20)
    reminder_time: Mapped[Optional[str]] = mapped_column(String(5))     # "19:00"

    # Прогресс / геймификация
    xp: Mapped[int] = mapped_column(Integer, default=0)
    streak: Mapped[int] = mapped_column(Integer, default=0)
    best_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_active: Mapped[Optional[date]] = mapped_column(Date)
    words_today: Mapped[int] = mapped_column(Integer, default=0)
    combo: Mapped[int] = mapped_column(Integer, default=0)
    best_combo: Mapped[int] = mapped_column(Integer, default=0)
    correct_total: Mapped[int] = mapped_column(Integer, default=0)
    wrong_total: Mapped[int] = mapped_column(Integer, default=0)


class Word(Base):
    __tablename__ = "words"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    en: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    ru: Mapped[list] = mapped_column(JSON, default=list)          # варианты перевода
    pos: Mapped[Optional[str]] = mapped_column(String(16))        # часть речи
    level: Mapped[str] = mapped_column(String(4), default="P3", index=True)  # P1..P5 — категория популярности
    freq: Mapped[Optional[int]] = mapped_column(Integer)          # частотный ранг
    ipa: Mapped[Optional[str]] = mapped_column(String(64))
    example: Mapped[Optional[str]] = mapped_column(Text)
    example_ru: Mapped[Optional[str]] = mapped_column(Text)
    synonyms: Mapped[list] = mapped_column(JSON, default=list)
    forms: Mapped[list] = mapped_column(JSON, default=list)       # формы слова
    topic: Mapped[Optional[str]] = mapped_column(String(64), index=True)


class Progress(Base):
    """Прогресс пользователя по конкретному слову (+ избранное, + SRS)."""
    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "word_id", name="uq_user_word"),
        Index("ix_progress_review", "user_id", "next_review"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id"), index=True)
    correct: Mapped[int] = mapped_column(Integer, default=0)
    wrong: Mapped[int] = mapped_column(Integer, default=0)
    stage: Mapped[int] = mapped_column(Integer, default=0)        # ступень SRS: 0..6
    next_review: Mapped[Optional[datetime]] = mapped_column(DateTime)
    favorite: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime)


class History(Base):
    """Журнал ответов — для статистики и еженедельных отчётов."""
    __tablename__ = "learning_history"
    __table_args__ = (Index("ix_history_user_ts", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"))
    word_id: Mapped[int] = mapped_column(Integer, ForeignKey("words.id"))
    correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "code", name="uq_user_ach"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    code: Mapped[str] = mapped_column(String(32))
    unlocked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
