"""
Интеграционные тесты для сервиса
"""
import os
import pytest
import asyncio
from datetime import datetime
from unittest.mock import patch
from ADHDLOL.utils.service_manager import ServiceManager
from ADHDLOL.utils.celery_app import celery_app, redis_client
from ADHDLOL.monitoring.metrics import MetricsCollector

@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def service_manager():
    """Фикстура для ServiceManager."""
    manager = ServiceManager()
    yield manager
    # Очистка после тестов
    await manager.session_manager.cleanup_inactive_sessions()
    redis_client.flushall()

@pytest.mark.integration
class TestServiceIntegration:
    """Интеграционные тесты сервиса."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, service_manager):
        """Тест полного рабочего процесса."""
        # Создание пользователя и сессии
        user_id = "test_user"
        
        # Обработка текстового контента
        text_request = {
            "type": "text_processing",
            "content": {
                "text": "Test content for processing with ADHD considerations"
            }
        }
        
        text_result = await service_manager.handle_request(user_id, text_request)
        assert text_result["status"] == "queued"
        
        # Проверка создания профиля
        profile = await service_manager.database.get_user_profile(user_id)
        assert profile is not None
        
        # Проверка метрик
        assert MetricsCollector.REQUEST_COUNT._value.get() > 0
    
    @pytest.mark.asyncio
    async def test_celery_integration(self, service_manager):
        """Тест интеграции с Celery."""
        # Создание задачи
        task = celery_app.send_task(
            'process_content',
            args=['text_processing', {'text': 'Test content'}]
        )
        
        # Ожидание результата
        result = task.get(timeout=10)
        assert result["status"] == "success"
        
        # Проверка метрик Celery
        assert MetricsCollector.TASK_STATUS._value.get() > 0
    
    @pytest.mark.asyncio
    async def test_redis_caching(self, service_manager):
        """Тест кэширования Redis."""
        cache_key = "test_key"
        cache_data = {"test": "data"}
        
        # Сохранение в кэш
        redis_client.set(
            cache_key,
            str(cache_data),
            ex=300  # 5 минут
        )
        
        # Проверка кэша
        cached_data = redis_client.get(cache_key)
        assert cached_data is not None
        
        # Проверка метрик кэша
        MetricsCollector.track_cache_operation(hit=True)
        assert MetricsCollector.CACHE_HITS._value.get() > 0
    
    @pytest.mark.asyncio
    async def test_resource_management(self, service_manager):
        """Тест управления ресурсами."""
        # Создание нескольких задач
        tasks = []
        for i in range(5):
            request = {
                "type": "text_processing",
                "content": {"text": f"Test content {i}"},
                "priority": "high"
            }
            task = await service_manager.handle_request("test_user", request)
            tasks.append(task)
        
        # Проверка очереди
        queue_size = len(service_manager.resource_manager._task_queue)
        MetricsCollector.update_queue_size(queue_size)
        assert MetricsCollector.QUEUE_SIZE._value.get() > 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, service_manager):
        """Тест обработки ошибок."""
        # Некорректный запрос
        invalid_request = {
            "type": "invalid_type",
            "content": {}
        }
        
        result = await service_manager.handle_request("test_user", invalid_request)
        assert result["status"] == "error"
        
        # Проверка метрик ошибок
        assert MetricsCollector.REQUEST_COUNT.labels(
            type="invalid_type",
            status="error"
        )._value.get() > 0
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, service_manager):
        """Тест параллельной обработки запросов."""
        # Создание нескольких параллельных запросов
        async def make_request(i):
            return await service_manager.handle_request(
                f"user_{i}",
                {
                    "type": "text_processing",
                    "content": {"text": f"Concurrent test {i}"}
                }
            )
        
        # Запуск параллельных запросов
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Проверка результатов
        assert all(r["status"] in ["queued", "error"] for r in results)
        
        # Проверка активных сессий
        session_count = len(service_manager.session_manager._sessions)
        MetricsCollector.update_session_count(session_count)
        assert MetricsCollector.ACTIVE_SESSIONS._value.get() > 0 