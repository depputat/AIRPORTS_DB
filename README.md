# AIRPORTS_DB

**AIRPORTS_DB** — Django-проект для работы с базой данных аэропортов и авиаперевозок. Проект позволяет просматривать справочники, анализировать данные по рейсам, работать с картой маршрутов и выполнять CRUD-операции для рейсов, пассажиров и билетов.

## Возможности

- список авиакомпаний, аэропортов и рейсов;
- аналитика и OLAP-страница;
- карта рейсов;
- API для получения данных по рейсу и активным рейсам;
- экспорт данных в CSV;
- CRUD для:
  - рейсов;
  - пассажиров;
  - билетов.

## Технологии

- Python 3
- Django 4.2
- PostgreSQL
- psycopg2-binary
- python-decouple
- HTML templates

## Структура проекта

```text
AIRPORTS_DB/
├── manage.py
├── requirements.txt
├── .env
├── bd_lab3_airports/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── posts/
    ├── models.py
    ├── views.py
    ├── forms.py
    ├── urls.py
    └── templates/
```

## Установка и запуск

1. Клонируйте репозиторий:

```bash
 git clone https://github.com/depputat/AIRPORTS_DB.git
 cd AIRPORTS_DB
```

2. Создайте и активируйте виртуальное окружение:

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

3. Установите зависимости:

```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` в корне проекта и добавьте переменные окружения:

```env
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_NAME=your-name-db
DATABASE_USER=your-username-db
DATABASE_PASSWORD=your-password-db
DATABASE_HOST=localhost
DATABASE_PORT=your-port-db
```

## Где взять `SECRET_KEY`

Для запуска проекта нужен `SECRET_KEY`. Его можно сгенерировать автоматически с помощью Python:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Команда выведет случайный ключ — просто скопируй его и вставь в файл `.env`.

5. Выполните миграции и запустите сервер:

```bash
python manage.py migrate
python manage.py runserver
```

После этого проект будет доступен по адресу `http://localhost:8000/`.

## Основные маршруты

- `/` — главная страница
- `/airlines/` — список авиакомпаний
- `/airports/` — список аэропортов
- `/flights/` — список рейсов
- `/olap/` — аналитика
- `/map/` — карта рейсов
- `/api/flight/<flight_id>/` — информация о рейсе
- `/api/active-flights/` — активные рейсы
- `/export/csv/` — экспорт в CSV

### CRUD-маршруты

- `/flights-crud/`
- `/passengers-crud/`
- `/tickets-crud/`

Для каждой сущности доступны создание, редактирование и удаление.

## Модель данных

Проект использует таблицы, связанные с:

- городами;
- аэропортами;
- авиакомпаниями;
- типами самолётов;
- самолётами;
- маршрутами;
- статусами рейсов;
- рейсами;
- пассажирами;
- билетами.

## Примечание

Часть моделей сопоставлена с уже существующими таблицами базы данных, поэтому для них используется `managed = False`.

## Автор

Проект выполнен в рамках лабораторной работы.
