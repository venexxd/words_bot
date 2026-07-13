# English Words Bot v2 🇬🇧

Телеграм-бот для изучения английских слов: уровни CEFR, интервальное повторение (SRS), темы, мини-игры, достижения, статистика, напоминания и админ-панель с импортом слов.

## Стек

- Python 3.11, **aiogram 3** (асинхронный)
- **SQLAlchemy 2.0 async**: локально — SQLite, на сервере — PostgreSQL (переключается автоматически через `DATABASE_URL`)
- APScheduler — ежедневные напоминания

## Архитектура

```
words_bot_v2/
├─ bot.py               # точка входа
├─ config.py            # настройки из переменных окружения
├─ states.py            # FSM-состояния
├─ database/            # engine + модели (users, words, user_progress, learning_history, user_achievements)
├─ handlers/            # start, training, games, stats, settings, admin
├─ services/            # SRS, подбор слов, умная проверка ответов, достижения
├─ keyboards/           # inline-клавиатуры
├─ middlewares/         # сессия БД + автосоздание пользователя, streak, сброс дневного счётчика
└─ data/                # seed: 258 слов A1–C2 с переводами, IPA, примерами, синонимами, темами
```

## Переменные окружения

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | токен от @BotFather (обязательно) |
| `DATABASE_URL` | строка подключения. По умолчанию SQLite (`sqlite+aiosqlite:///bot.db`). Railway подставляет Postgres автоматически |
| `ADMIN_IDS` | Telegram ID админов через запятую, например `123456789` |
| `BOT_TZ` | часовой пояс напоминаний, по умолчанию `Europe/Moscow` |

Свой Telegram ID можно узнать у бота @userinfobot.

## Запуск локально

```bash
cd words_bot_v2
pip install -r requirements.txt
export BOT_TOKEN="ваш_токен"
export ADMIN_IDS="ваш_telegram_id"
python3 bot.py
```

При первом запуске бот сам создаст таблицы и зальёт стартовую базу слов.

## Деплой на Railway

1. Залей папку в GitHub-репозиторий.
2. На railway.app: **New Project → Deploy from GitHub repo**.
3. Добавь базу: **+ New → Database → PostgreSQL**. В сервисе бота в Variables добавь ссылку `DATABASE_URL` → `$Postgres.DATABASE_URL`.
4. В Variables сервиса бота добавь `BOT_TOKEN` и `ADMIN_IDS`.
5. Готово — Procfile уже в репозитории (`worker: python3 bot.py`). Любой `git push` автоматически передеплоит бота.

## Как расширить базу до 10 000+ слов

В комплекте 258 качественных слов (A1–C2). База расширяется без кода — просто пришли боту (как админ) CSV- или JSON-файл.

**CSV** (колонки): `en,ru,pos,level,topic,example,example_ru,ipa,synonyms,forms,freq`
— в `ru`, `synonyms`, `forms` варианты разделяются `|`:

```csv
en,ru,pos,level,topic,example,example_ru,ipa,synonyms,forms,freq
apple,яблоко,noun,A1,Еда,I eat an apple every day.,Я ем яблоко каждый день.,ˈæp.əl,,apples,50
car,машина|автомобиль,noun,A1,Путешествия,My car is red.,Моя машина красная.,kɑːr,automobile|vehicle,cars,80
```

**JSON** — список объектов, `ru`/`synonyms`/`forms` — массивы строк.

Готовые источники частотных списков: NGSL, Oxford 3000/5000, kaikki.org (Wiktionary-дампы с переводами и IPA), ECDICT, SUBTLEX/COCA. Сконвертируй в CSV указанного формата и отправь боту.

## Возможности

- Уровни A1–C2 и «Все уровни»
- Режимы: обычный, новые слова, повторение ошибок, случайные, избранное, быстрое повторение (20 слов)
- Оба направления: EN→RU и RU→EN (переключается в настройках)
- Интервальное повторение: 1/3/7/14/30/60 дней, при ошибке слово возвращается раньше
- Умная проверка: регистр, пробелы, артикли, несколько переводов, синонимы, опечатки (расстояние Левенштейна)
- Примеры употребления, IPA-транскрипция, формы слова
- Темы: Путешествия, Еда, Работа, IT, Бизнес, Медицина, Дом, Семья, Животные, Спорт и др.
- Мини-игры: выбери перевод (4 варианта), собери слово из букв, правда/ложь
- Ежедневная цель (10–100 слов), streak 🔥, XP, достижения, лидерборд /top
- Напоминания в выбранное время
- /stats, /profile с прогрессом по уровням
- Админка: /addword, /delword, импорт CSV/JSON файлом в чат

## Идеи на будущее

- ИИ-проверка свободных ответов через OpenAI API
- Еженедельные отчёты о прогрессе
- Экзамен-режим и фразовые глаголы отдельным блоком
- Экспорт прогресса в CSV
