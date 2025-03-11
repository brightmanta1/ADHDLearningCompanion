"""
Тесты для модуля управления GPU ресурсами
"""

import pytest
import torch
from unittest.mock import patch, MagicMock
from ADHDLOL.utils.gpu_manager import GPUManager, GPUStats

@pytest.fixture
def gpu_manager():
    """Фикстура для создания экземпляра GPUManager"""
    return GPUManager()

def test_init_no_gpu():
    """Тест инициализации без GPU"""
    with patch('torch.cuda.is_available', return_value=False):
        manager = GPUManager()
        assert not manager.available
        assert manager.device_count == 0
        assert len(manager.devices) == 0

def test_init_with_gpu():
    """Тест инициализации с GPU"""
    with patch('torch.cuda.is_available', return_value=True), \
         patch('torch.cuda.device_count', return_value=2):
        manager = GPUManager()
        assert manager.available
        assert manager.device_count == 2
        assert len(manager.devices) == 2

def test_get_optimal_device_no_gpu():
    """Тест получения оптимального устройства без GPU"""
    with patch('torch.cuda.is_available', return_value=False):
        manager = GPUManager()
        device = manager.get_optimal_device()
        assert device == torch.device('cpu')

def test_get_optimal_device_with_gpu():
    """Тест получения оптимального устройства с GPU"""
    mock_gpu = MagicMock()
    mock_gpu.id = 0
    mock_gpu.memoryFree = 8.0  # 8GB свободной памяти
    
    with patch('torch.cuda.is_available', return_value=True), \
         patch('GPUtil.getGPUs', return_value=[mock_gpu]), \
         patch('torch.cuda.device_count', return_value=1):
        manager = GPUManager()
        device = manager.get_optimal_device(required_memory=4.0)
        assert device == torch.device('cuda:0')

def test_get_optimal_device_insufficient_memory():
    """Тест получения устройства при недостатке памяти"""
    mock_gpu = MagicMock()
    mock_gpu.id = 0
    mock_gpu.memoryFree = 2.0  # 2GB свободной памяти
    
    with patch('torch.cuda.is_available', return_value=True), \
         patch('GPUtil.getGPUs', return_value=[mock_gpu]):
        manager = GPUManager()
        device = manager.get_optimal_device(required_memory=4.0)
        assert device == torch.device('cpu')

def test_get_gpu_stats():
    """Тест получения статистики GPU"""
    mock_gpu = MagicMock()
    mock_gpu.id = 0
    mock_gpu.memoryTotal = 16.0
    mock_gpu.memoryUsed = 4.0
    mock_gpu.memoryFree = 12.0
    mock_gpu.load = 0.3
    mock_gpu.temperature = 65.0
    
    with patch('torch.cuda.is_available', return_value=True), \
         patch('GPUtil.getGPUs', return_value=[mock_gpu]):
        manager = GPUManager()
        stats = manager.get_gpu_stats()
        
        assert len(stats) == 1
        assert isinstance(stats[0], GPUStats)
        assert stats[0].device_id == 0
        assert stats[0].memory_total == 16.0
        assert stats[0].memory_free == 12.0
        assert stats[0].gpu_load == 0.3
        assert stats[0].temperature == 65.0

def test_cleanup():
    """Тест очистки памяти GPU"""
    with patch('torch.cuda.is_available', return_value=True), \
         patch('torch.cuda.empty_cache') as mock_empty_cache:
        manager = GPUManager()
        manager.cleanup()
        mock_empty_cache.assert_called_once()

def test_get_memory_usage():
    """Тест получения информации об использовании памяти"""
    with patch('torch.cuda.is_available', return_value=True), \
         patch('torch.cuda.max_memory_allocated', return_value=2*1024**3), \
         patch('psutil.Process') as mock_process:
        mock_process.return_value.memory_info.return_value.rss = 4*1024**3
        
        manager = GPUManager()
        memory_info = manager.get_memory_usage()
        
        assert memory_info["cpu_memory_gb"] == 4.0
        assert memory_info["gpu_memory_gb"] == 2.0

def test_is_gpu_suitable():
    """Тест проверки пригодности GPU"""
    mock_gpu = MagicMock()
    mock_gpu.id = 0
    mock_gpu.memoryFree = 8.0
    mock_gpu.temperature = 70.0
    
    with patch('torch.cuda.is_available', return_value=True), \
         patch('GPUtil.getGPUs', return_value=[mock_gpu]):
        manager = GPUManager()
        
        # GPU подходит
        assert manager.is_gpu_suitable(required_memory=4.0, max_temperature=80.0)
        
        # Недостаточно памяти
        assert not manager.is_gpu_suitable(required_memory=16.0)
        
        # Слишком высокая температура
        assert not manager.is_gpu_suitable(required_memory=4.0, max_temperature=60.0) 