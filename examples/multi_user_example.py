"""
Пример использования многопользовательской системы ADHDLearningCompanion
"""

import asyncio
import logging
from typing import Dict, Any
from ADHDLOL.utils import ServiceManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


async def simulate_video_request(
    service: ServiceManager, user_id: str, video_url: str
) -> Dict[str, Any]:
    """Симуляция запроса на обработку видео."""
    request_data = {
        "type": "video_processing",
        "priority": "high",
        "content": {"url": video_url, "format": "youtube"},
        "timeout": 600,  # 10 минут
    }
    return await service.handle_request(user_id, request_data)


async def simulate_text_request(
    service: ServiceManager, user_id: str, text: str
) -> Dict[str, Any]:
    """Симуляция запроса на обработку текста."""
    request_data = {
        "type": "text_processing",
        "priority": "medium",
        "content": {"text": text, "language": "ru"},
        "timeout": 300,  # 5 минут
    }
    return await service.handle_request(user_id, request_data)


async def simulate_learning_session(service: ServiceManager, user_id: str) -> None:
    """Симуляция учебной сессии пользователя."""
    # Обработка видео
    video_result = await simulate_video_request(
        service, user_id, "https://www.youtube.com/watch?v=_HURE27oTX4"
    )
    print(f"\nРезультат обработки видео для пользователя {user_id}:")
    print(video_result)

    # Обработка текста
    text_result = await simulate_text_request(
        service,
        user_id,
        "Квантовая механика - это раздел физики, изучающий поведение материи и энергии на атомном и субатомном уровнях.",
    )
    print(f"\nРезультат обработки текста для пользователя {user_id}:")
    print(text_result)

    # Получение статистики
    stats = await service.get_service_stats()
    print(f"\nСтатистика сервиса после обработки запросов пользователя {user_id}:")
    print(stats)


async def main():
    """Основная функция примера."""
    try:
        # Инициализация сервиса
        service = ServiceManager()
        print("Сервис инициализирован")

        # Симуляция нескольких пользователей
        users = ["user1", "user2", "user3"]
        tasks = [simulate_learning_session(service, user_id) for user_id in users]

        # Запуск всех задач параллельно
        print("\nЗапуск параллельных сессий для пользователей...")
        await asyncio.gather(*tasks)

        print("\nВсе сессии завершены")

    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        # В реальном приложении здесь был бы код очистки ресурсов
        print("\nЗавершение работы сервиса")


if __name__ == "__main__":
    # Запуск примера
    print("Запуск примера многопользовательской системы...")
    asyncio.run(main())
