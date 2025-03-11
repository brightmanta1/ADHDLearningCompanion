"""
Тесты для модуля управления кэшем
"""

import os
import time
import pytest
from datetime import datetime, timedelta
from ADHDLOL.utils.cache_manager import CacheManager
from dataclasses import dataclass

@dataclass
class TestData:
    """Тестовая структура данных"""
    name: str
    value: int

@pytest.fixture
def cache_manager():
    """Фикстура для создания экземпляра CacheManager"""
    manager = CacheManager(cache_dir="./test_cache", max_age_days=1)
    yield manager
    # Очистка после тестов
    manager.clear()
    for dir_path in manager.dirs.values():
        try:
            os.rmdir(dir_path)
        except:
            pass
    try:
        os.rmdir("./test_cache")
    except:
        pass

def test_init_cache_dirs(cache_manager):
    """Тест инициализации директорий кэша"""
    for dir_path in cache_manager.dirs.values():
        assert os.path.exists(dir_path)
        assert os.path.isdir(dir_path)

def test_generate_key():
    """Тест генерации ключей кэша"""
    manager = CacheManager()
    
    # Тест с разными типами данных
    assert manager._generate_key("test") == manager._generate_key("test")
    assert manager._generate_key({"a": 1}) == manager._generate_key({"a": 1})
    assert manager._generate_key([1, 2, 3]) == manager._generate_key([1, 2, 3])
    
    # Тест с префиксом
    key1 = manager._generate_key("test", prefix="prefix1")
    key2 = manager._generate_key("test", prefix="prefix2")
    assert key1 != key2
    assert key1.startswith("prefix1_")
    assert key2.startswith("prefix2_")

def test_cache_operations(cache_manager):
    """Тест основных операций с кэшем"""
    # Тест сохранения и получения данных
    key = cache_manager._generate_key("test_data")
    data = {"test": "value"}
    
    cache_manager.set(key, data, "text")
    cached_data = cache_manager.get(key, "text")
    
    assert cached_data == data
    assert cache_manager.is_cached(key, "text")

def test_cache_dataclass(cache_manager):
    """Тест работы с dataclass"""
    test_data = TestData(name="test", value=42)
    key = cache_manager._generate_key("test_dataclass")
    
    cache_manager.set(key, test_data, "text")
    cached_data = cache_manager.get(key, "text")
    
    assert cached_data["name"] == test_data.name
    assert cached_data["value"] == test_data.value

def test_cache_expiration(cache_manager):
    """Тест устаревания кэша"""
    # Устанавливаем малый срок жизни кэша для теста
    cache_manager.max_age = timedelta(seconds=1)
    
    key = cache_manager._generate_key("test_expiration")
    data = {"test": "value"}
    
    cache_manager.set(key, data, "text")
    assert cache_manager.get(key, "text") == data
    
    # Ждем устаревания кэша
    time.sleep(2)
    assert cache_manager.get(key, "text") is None

def test_cache_size(cache_manager):
    """Тест подсчета размера кэша"""
    # Сохраняем данные в разные типы кэша
    data = {"test": "value" * 100}  # Создаем данные с известным размером
    
    for cache_type in ["text", "video"]:
        key = cache_manager._generate_key(f"test_size_{cache_type}")
        cache_manager.set(key, data, cache_type)
    
    # Проверяем размер для конкретного типа
    text_size = cache_manager.get_cache_size("text")
    assert text_size > 0
    
    # Проверяем общий размер
    total_size = cache_manager.get_cache_size()
    assert total_size > text_size

def test_cache_clear(cache_manager):
    """Тест очистки кэша"""
    # Сохраняем данные
    data = {"test": "value"}
    key1 = cache_manager._generate_key("test1")
    key2 = cache_manager._generate_key("test2")
    
    cache_manager.set(key1, data, "text")
    cache_manager.set(key2, data, "video")
    
    # Очищаем конкретный тип кэша
    cache_manager.clear("text")
    assert cache_manager.get(key1, "text") is None
    assert cache_manager.get(key2, "video") == data
    
    # Очищаем весь кэш
    cache_manager.clear()
    assert cache_manager.get(key2, "video") is None

def test_cleanup_old_cache(cache_manager):
    """Тест очистки устаревшего кэша"""
    cache_manager.max_age = timedelta(seconds=1)
    
    # Сохраняем данные
    data = {"test": "value"}
    key = cache_manager._generate_key("test_cleanup")
    cache_manager.set(key, data, "text")
    
    # Ждем устаревания кэша
    time.sleep(2)
    
    # Запускаем очистку
    cache_manager.cleanup_old_cache()
    assert not os.path.exists(cache_manager._get_cache_path(key, "text"))

def test_error_handling(cache_manager):
    """Тест обработки ошибок"""
    # Тест с некорректным типом кэша
    with pytest.raises(Exception):
        cache_manager.get("key", "invalid_type")
    
    # Тест с некорректными данными
    key = cache_manager._generate_key("test_error")
    cache_manager.set(key, {"test": "value"}, "text")
    
    # Портим файл кэша
    with open(cache_manager._get_cache_path(key, "text"), 'w') as f:
        f.write("invalid data")
    
    # Проверяем, что получаем None вместо ошибки
    assert cache_manager.get(key, "text") is None 