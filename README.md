# ADHDLearningCompanion

Персонализированная система обучения для людей с СДВГ (ADHD).

## Возможности

- Обработка и адаптация образовательного контента
- Персонализированные расписания обучения
- Анализ паттернов концентрации
- Интерактивные упражнения
- Real-time отслеживание прогресса
- Многопользовательский режим

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/ADHDLearningCompanion.git
cd ADHDLearningCompanion
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл, добавив необходимые ключи
```

## Конфигурация

### Supabase
- `SUPABASE_URL`: URL вашего Supabase проекта
- `SUPABASE_KEY`: Публичный ключ Supabase
- `SUPABASE_SERVICE_KEY`: Сервисный ключ Supabase

### Pinecone
- `PINECONE_API_KEY`: API ключ Pinecone
- `PINECONE_ENVIRONMENT`: Окружение Pinecone (например, "us-west1-gcp")
- `PINECONE_INDEX_NAME`: Название индекса (по умолчанию "learning-content")

## API Endpoints

### Обработка контента
```http
POST /api/process
Content-Type: application/json

{
    "type": "video_processing",
    "content": {
        "url": "https://example.com/video"
    },
    "priority": "medium"
}
```

### Профиль пользователя
```http
GET /api/profile/{user_id}
PUT /api/profile/{user_id}
```

### Расписание
```http
POST /api/schedule/{user_id}
Content-Type: application/json

{
    "preferences": {
        "preferred_times": ["morning", "evening"],
        "break_duration": 15
    }
}
```

### Аналитика
```http
GET /api/analytics/{user_id}?event_type=learning_session
```

### WebSocket
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/{user_id}');
```

## Архитектура

### Компоненты
- `ServiceManager`: Управление сервисами и обработка запросов
- `PersonalizationEngine`: Персонализация контента с использованием Pinecone
- `LearningScheduler`: Создание оптимальных расписаний
- `ContentProcessor`: Обработка видео и текстового контента
- `Database`: Взаимодействие с Supabase

### База данных
- `user_profiles`: Профили пользователей
- `learning_sessions`: Сессии обучения
- `content_metadata`: Метаданные контента
- `analytics_events`: События аналитики
- `resource_usage`: Использование ресурсов

## Разработка

### Запуск тестов
```bash
pytest tests/
```

### Запуск API
```bash
uvicorn ADHDLOL.api.main:app --reload
```

### Форматирование кода
```bash
black .
isort .
```

## Безопасность

- Аутентификация через Supabase
- Row Level Security (RLS) для данных
- CORS настройки
- Валидация входных данных
- Ограничение ресурсов

## Оптимизация

- Кэширование через Redis (планируется)
- Очереди задач через Celery (планируется)
- Балансировка нагрузки
- Мониторинг ресурсов

## Лицензия

MIT License

## Контакты

- Email: your.email@example.com
- GitHub: https://github.com/yourusername 