"""
Тесты для ServiceManager
"""

import os
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from ADHDLOL.utils.service_manager import ServiceManager
from ADHDLOL.utils.resource_manager import TaskPriority, ResourceType


@pytest.fixture
def service_manager():
    """Фикстура для создания ServiceManager с мок-зависимостями."""
    with patch("pinecone.init"), patch("pinecone.Index"), patch(
        "pinecone.list_indexes", return_value=[]
    ):
        manager = ServiceManager()
        return manager


@pytest.mark.asyncio
async def test_handle_request(service_manager):
    """Тест обработки запроса."""
    # Подготовка тестовых данных
    user_id = "test_user"
    request_data = {
        "type": "text_processing",
        "content": {"text": "Test content for processing"},
    }

    # Мокаем методы базы данных
    service_manager.database.get_user_profile = Mock(return_value=None)
    service_manager.database.create_user_profile = Mock(
        return_value={"user_id": user_id, "preferences": {}}
    )
    service_manager.database.save_analytics_event = Mock()

    # Выполнение запроса
    result = await service_manager.handle_request(user_id, request_data)

    # Проверки
    assert result["status"] in ["queued", "error"]
    assert "task_id" in result
    assert "session_id" in result

    # Проверяем, что методы были вызваны
    service_manager.database.get_user_profile.assert_called_once_with(user_id)
    service_manager.database.save_analytics_event.assert_called_once()


@pytest.mark.asyncio
async def test_personalize_request(service_manager):
    """Тест персонализации запроса."""
    user_id = "test_user"
    request_data = {
        "type": "video_processing",
        "content": {"url": "https://example.com/video"},
    }

    # Мокаем scheduler
    service_manager.scheduler.create_personalized_schedule = Mock(
        return_value={
            "optimal_times": ["09:00", "14:00"],
            "recommended_breaks": [15, 30],
        }
    )

    # Выполнение персонализации
    result = await service_manager._personalize_request(user_id, request_data)

    # Проверки
    assert "optimal_time" in result
    assert "personalization" in result
    assert result["personalization"]["user_id"] == user_id
    assert isinstance(result["personalization"]["timestamp"], str)


def test_determine_priority(service_manager):
    """Тест определения приоритета задачи."""
    # Тест разных приоритетов
    assert (
        service_manager._determine_priority({"priority": "high"}) == TaskPriority.HIGH
    )
    assert service_manager._determine_priority({"priority": "low"}) == TaskPriority.LOW
    assert service_manager._determine_priority({}) == TaskPriority.MEDIUM


def test_calculate_resource_requirements(service_manager):
    """Тест расчета требуемых ресурсов."""
    # Тест для видео
    video_req = service_manager._calculate_resource_requirements(
        {"type": "video_processing"}
    )
    assert video_req[ResourceType.CPU] == 30.0
    assert video_req[ResourceType.GPU] == 50.0
    assert video_req[ResourceType.MEMORY] == 1024.0

    # Тест для текста
    text_req = service_manager._calculate_resource_requirements(
        {"type": "text_processing"}
    )
    assert text_req[ResourceType.CPU] == 20.0
    assert text_req[ResourceType.MEMORY] == 768.0


@pytest.mark.asyncio
async def test_process_request(service_manager):
    """Тест обработки разных типов контента."""
    # Мокаем процессоры
    service_manager.content_processor.process_content = Mock(
        return_value={"title": "Test Video", "duration": 300}
    )
    service_manager.text_processor.process_text = Mock(
        return_value=Mock(
            topics=["test"],
            tags=["tag1"],
            simplified="Simple text",
            highlighted_terms={"term": "context"},
        )
    )
    service_manager.database.save_content_metadata = Mock()

    # Тест обработки видео
    video_result = await service_manager._process_request(
        {"type": "video_processing", "content": {"url": "https://example.com/video"}}
    )
    assert video_result["status"] == "success"
    assert video_result["type"] == "video"

    # Тест обработки текста
    text_result = await service_manager._process_request(
        {"type": "text_processing", "content": {"text": "Test content"}}
    )
    assert text_result["status"] == "success"
    assert text_result["type"] == "text"
    assert "simplified" in text_result["result"]
