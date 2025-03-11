"""
Тесты для многопользовательской системы
"""
import pytest
import asyncio
from datetime import datetime
from ADHDLOL.utils import (
    ServiceManager,
    SessionManager,
    ResourceManager,
    Task,
    TaskPriority,
    ResourceType
)

@pytest.fixture
async def service_manager():
    """Фикстура для ServiceManager."""
    manager = ServiceManager()
    yield manager
    # Очистка после тестов
    for task in manager.background_tasks:
        task.cancel()

@pytest.fixture
async def session_manager():
    """Фикстура для SessionManager."""
    return SessionManager()

@pytest.fixture
async def resource_manager():
    """Фикстура для ResourceManager."""
    return ResourceManager()

@pytest.mark.asyncio
async def test_session_creation(session_manager):
    """Тест создания сессии."""
    user_id = "test_user"
    session_id = await session_manager.create_session(user_id)
    
    assert session_id is not None
    session = await session_manager.get_session(session_id)
    assert session is not None
    assert session.user_id == user_id
    assert session.is_active

@pytest.mark.asyncio
async def test_session_cleanup(session_manager):
    """Тест очистки сессий."""
    user_id = "test_user"
    session_id = await session_manager.create_session(user_id)
    
    # Проверка активной сессии
    stats = await session_manager.get_session_stats()
    assert stats["total_sessions"] == 1
    
    # Завершение сессии
    result = await session_manager.end_session(session_id)
    assert result is True
    
    # Проверка после завершения
    stats = await session_manager.get_session_stats()
    assert stats["total_sessions"] == 0

@pytest.mark.asyncio
async def test_resource_allocation(resource_manager):
    """Тест выделения ресурсов."""
    # Создание тестовой задачи
    task = Task(
        task_id="test_task",
        user_id="test_user",
        session_id="test_session",
        priority=TaskPriority.HIGH,
        resource_requirements={
            ResourceType.CPU: 20.0,
            ResourceType.MEMORY: 512.0
        },
        created_at=datetime.now(),
        timeout=30.0,
        coroutine=asyncio.sleep(0.1)
    )
    
    # Проверка возможности выделения ресурсов
    can_allocate = resource_manager._can_allocate_resources(task.resource_requirements)
    assert can_allocate is True
    
    # Добавление задачи
    status = await resource_manager.submit_task(task)
    assert status == "queued"
    
    # Проверка статистики
    stats = await resource_manager.get_resource_stats()
    assert stats["tasks"]["total"] == 1

@pytest.mark.asyncio
async def test_service_request_handling(service_manager):
    """Тест обработки запросов сервисом."""
    user_id = "test_user"
    request_data = {
        "type": "text_processing",
        "priority": "medium",
        "content": {
            "text": "Test text",
            "language": "ru"
        }
    }
    
    # Отправка запроса
    response = await service_manager.handle_request(user_id, request_data)
    
    assert response["status"] in ["queued", "completed"]
    assert "task_id" in response
    assert "session_id" in response

@pytest.mark.asyncio
async def test_concurrent_requests(service_manager):
    """Тест параллельной обработки запросов."""
    async def make_request(user_id: str):
        request_data = {
            "type": "text_processing",
            "priority": "medium",
            "content": {
                "text": f"Test text for {user_id}",
                "language": "ru"
            }
        }
        return await service_manager.handle_request(user_id, request_data)
    
    # Создание нескольких параллельных запросов
    users = [f"user_{i}" for i in range(5)]
    tasks = [make_request(user_id) for user_id in users]
    
    # Выполнение запросов
    responses = await asyncio.gather(*tasks)
    
    # Проверка результатов
    assert len(responses) == 5
    for response in responses:
        assert response["status"] in ["queued", "completed"]
        assert "task_id" in response
        assert "session_id" in response

@pytest.mark.asyncio
async def test_resource_limits(resource_manager):
    """Тест лимитов ресурсов."""
    # Создание задачи с большими требованиями
    task = Task(
        task_id="heavy_task",
        user_id="test_user",
        session_id="test_session",
        priority=TaskPriority.HIGH,
        resource_requirements={
            ResourceType.CPU: 150.0,  # Больше максимума
            ResourceType.MEMORY: 1024 * 10  # Больше максимума
        },
        created_at=datetime.now(),
        timeout=30.0,
        coroutine=asyncio.sleep(0.1)
    )
    
    # Проверка отказа в выделении ресурсов
    status = await resource_manager.submit_task(task)
    assert status == "rejected"

@pytest.mark.asyncio
async def test_task_priority(resource_manager):
    """Тест приоритезации задач."""
    # Создание задач с разными приоритетами
    tasks = []
    for priority in TaskPriority:
        task = Task(
            task_id=f"task_{priority.name}",
            user_id="test_user",
            session_id="test_session",
            priority=priority,
            resource_requirements={
                ResourceType.CPU: 10.0,
                ResourceType.MEMORY: 256.0
            },
            created_at=datetime.now(),
            timeout=30.0,
            coroutine=asyncio.sleep(0.1)
        )
        tasks.append(task)
    
    # Добавление задач в обратном порядке
    for task in reversed(tasks):
        status = await resource_manager.submit_task(task)
        assert status == "queued"
    
    # Проверка статистики
    stats = await resource_manager.get_resource_stats()
    assert stats["tasks"]["total"] == len(TaskPriority) 