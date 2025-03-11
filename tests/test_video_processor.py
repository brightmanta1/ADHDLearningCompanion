"""
Тесты для модуля обработки видео
"""

import os
import pytest
import asyncio
from unittest.mock import Mock, patch
from ADHDLOL.utils.video_processor import VideoProcessor, VideoSegment

@pytest.fixture
def video_processor():
    """Фикстура для создания экземпляра VideoProcessor"""
    processor = VideoProcessor(cache_dir="./test_cache", use_gpu=False)
    return processor

@pytest.fixture
def sample_video_url():
    """Фикстура с тестовым URL видео"""
    return "https://www.youtube.com/watch?v=test_video"

@pytest.fixture
def mock_whisper_result():
    """Фикстура с моком результата транскрибации"""
    return {
        "text": "This is a test transcript",
        "segments": [
            {"text": "This is segment one", "start": 0.0, "end": 5.0},
            {"text": "This is segment two", "start": 5.0, "end": 10.0}
        ]
    }

@pytest.mark.asyncio
async def test_process_video_success(video_processor, sample_video_url):
    """Тест успешной обработки видео"""
    with patch("yt_dlp.YoutubeDL") as mock_ydl, \
         patch.object(video_processor, "_extract_audio") as mock_extract_audio, \
         patch.object(video_processor, "_transcribe_audio") as mock_transcribe_audio, \
         patch.object(video_processor, "_cleanup_temp_files") as mock_cleanup:
        
        # Настройка моков
        mock_ydl.return_value.__enter__.return_value.download.return_value = None
        mock_extract_audio.return_value = "test_audio.wav"
        mock_transcribe_audio.return_value = {
            "text": "Test transcript",
            "segments": [{"text": "Test segment", "start": 0.0, "end": 5.0}]
        }
        
        # Выполнение теста
        result = await video_processor.process_video(sample_video_url)
        
        # Проверки
        assert result["status"] == "success"
        assert "segments" in result
        assert "metadata" in result
        assert len(result["segments"]) > 0

@pytest.mark.asyncio
async def test_process_video_error(video_processor, sample_video_url):
    """Тест обработки ошибок при обработке видео"""
    with patch("yt_dlp.YoutubeDL") as mock_ydl:
        # Симуляция ошибки при загрузке
        mock_ydl.return_value.__enter__.return_value.download.side_effect = Exception("Download error")
        
        # Выполнение теста
        result = await video_processor.process_video(sample_video_url)
        
        # Проверки
        assert result["status"] == "error"
        assert "message" in result
        assert "Download error" in result["message"]

def test_extract_key_points(video_processor):
    """Тест извлечения ключевых моментов"""
    test_text = "This is a test text for key points extraction. It should generate some key points."
    key_points = video_processor._extract_key_points(test_text)
    
    assert isinstance(key_points, list)
    assert len(key_points) > 0

def test_create_thumbnail(video_processor):
    """Тест создания thumbnail"""
    with patch("cv2.VideoCapture") as mock_cv:
        mock_cv.return_value.read.return_value = (True, "mock_frame")
        mock_cv.return_value.get.return_value = 30.0
        
        thumbnail_path = video_processor._create_thumbnail("test_video.mp4", 1.0)
        assert thumbnail_path is not None

def test_segment_video(video_processor, mock_whisper_result):
    """Тест сегментации видео"""
    with patch.object(video_processor, "_extract_key_points") as mock_extract_points, \
         patch.object(video_processor, "_create_thumbnail") as mock_create_thumbnail:
        
        mock_extract_points.return_value = ["Key point 1"]
        mock_create_thumbnail.return_value = "thumbnail.jpg"
        
        segments = video_processor._segment_video("test_video.mp4", mock_whisper_result)
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        assert isinstance(segments[0], VideoSegment)
        assert segments[0].transcript is not None
        assert segments[0].key_points is not None

def test_create_interactive_elements(video_processor):
    """Тест создания интерактивных элементов"""
    test_segment = VideoSegment(
        start_time=0.0,
        end_time=5.0,
        transcript="Test transcript",
        key_points=["Key point 1"],
        thumbnail_path="thumbnail.jpg"
    )
    
    processed_segments = video_processor._create_interactive_elements([test_segment])
    
    assert isinstance(processed_segments, list)
    assert len(processed_segments) > 0
    assert "interactive_elements" in processed_segments[0]
    assert "questions" in processed_segments[0]["interactive_elements"]

@pytest.fixture(autouse=True)
def cleanup():
    """Очистка тестовых файлов после каждого теста"""
    yield
    if os.path.exists("./test_cache"):
        for file in os.listdir("./test_cache"):
            try:
                os.remove(os.path.join("./test_cache", file))
            except:
                pass
        os.rmdir("./test_cache") 