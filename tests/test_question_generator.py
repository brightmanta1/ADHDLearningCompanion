"""
Тесты для модуля генерации вопросов
"""

import pytest
from unittest.mock import patch, MagicMock
import torch
from ADHDLOL.utils.question_generator import QuestionGenerator

@pytest.fixture
def question_generator():
    """Фикстура для создания экземпляра QuestionGenerator"""
    with patch('torch.cuda.is_available', return_value=False):  # Используем CPU для тестов
        generator = QuestionGenerator(use_gpu=False)
        return generator

def test_validate_text(question_generator):
    """Тест валидации текста"""
    # Пустой текст
    is_valid, error = question_generator._validate_text("")
    assert not is_valid
    assert "Empty text" in error
    
    # Слишком длинный текст
    long_text = "a" * (question_generator.max_text_length + 1)
    is_valid, error = question_generator._validate_text(long_text)
    assert not is_valid
    assert "Text too long" in error
    
    # Слишком короткий текст
    short_text = "one two"
    is_valid, error = question_generator._validate_text(short_text)
    assert not is_valid
    assert "Text too short" in error
    
    # Валидный текст
    valid_text = "This is a valid text with more than ten words for testing the validation function"
    is_valid, error = question_generator._validate_text(valid_text)
    assert is_valid
    assert error == ""

@pytest.mark.asyncio
async def test_generate_questions(question_generator):
    """Тест генерации вопросов"""
    text = "Machine learning is a subset of artificial intelligence that focuses on developing systems that can learn from data."
    
    # Мокаем генерацию вопросов
    with patch.object(question_generator, '_generate_multiple_choice') as mock_mc, \
         patch.object(question_generator, '_generate_true_false') as mock_tf, \
         patch.object(question_generator, '_generate_open_ended') as mock_oe, \
         patch.object(question_generator, '_add_explanation') as mock_explain:
        
        # Настраиваем моки
        mock_mc.return_value = [{
            "type": "multiple_choice",
            "question": "What is machine learning?",
            "options": ["A subset of AI", "A programming language", "A database", "A network protocol"],
            "correct_answer": "A subset of AI"
        }]
        
        mock_tf.return_value = [{
            "type": "true_false",
            "question": "Machine learning systems can learn from data.",
            "correct_answer": True
        }]
        
        mock_oe.return_value = [{
            "type": "open_ended",
            "question": "Explain how machine learning relates to AI.",
            "correct_answer": "Machine learning is a subset of AI that focuses on learning from data."
        }]
        
        mock_explain.side_effect = lambda q, _: {**q, "explanation": "Test explanation"}
        
        # Генерируем вопросы
        questions = question_generator.generate_questions(
            text,
            num_questions=3,
            question_types=["multiple_choice", "true_false", "open_ended"]
        )
        
        # Проверяем результаты
        assert len(questions) == 3
        assert any(q["type"] == "multiple_choice" for q in questions)
        assert any(q["type"] == "true_false" for q in questions)
        assert any(q["type"] == "open_ended" for q in questions)
        assert all("explanation" in q for q in questions)

def test_generate_multiple_choice(question_generator):
    """Тест генерации вопросов с множественным выбором"""
    text = "Python is a popular programming language."
    
    with patch.object(question_generator.model, 'generate') as mock_generate, \
         patch.object(question_generator.tokenizer, 'decode') as mock_decode:
        
        # Настраиваем моки
        mock_generate.return_value = torch.tensor([[1, 2, 3]])
        mock_decode.return_value = "What type of language is Python?"
        
        # Мокаем генерацию вариантов ответов
        with patch.object(question_generator, '_generate_answer_options') as mock_options:
            mock_options.return_value = ["Programming language", "Natural language", "Markup language", "Query language"]
            
            questions = question_generator._generate_multiple_choice(text)
            
            assert len(questions) == 1
            assert questions[0]["type"] == "multiple_choice"
            assert len(questions[0]["options"]) == 4
            assert "difficulty" in questions[0]

def test_generate_true_false(question_generator):
    """Тест генерации вопросов типа правда/ложь"""
    text = "Python is a programming language."
    
    with patch.object(question_generator.model, 'generate') as mock_generate, \
         patch.object(question_generator.tokenizer, 'decode') as mock_decode:
        
        mock_generate.return_value = torch.tensor([[1, 2, 3]])
        mock_decode.return_value = "Python is a programming language."
        
        questions = question_generator._generate_true_false(text)
        
        assert len(questions) == 1
        assert questions[0]["type"] == "true_false"
        assert isinstance(questions[0]["correct_answer"], bool)
        assert "difficulty" in questions[0]

def test_generate_open_ended(question_generator):
    """Тест генерации открытых вопросов"""
    text = "Python is a programming language."
    
    with patch.object(question_generator.model, 'generate') as mock_generate, \
         patch.object(question_generator.tokenizer, 'decode') as mock_decode:
        
        mock_generate.return_value = torch.tensor([[1, 2, 3]])
        mock_decode.side_effect = ["What is Python?", "Python is a programming language."]
        
        questions = question_generator._generate_open_ended(text)
        
        assert len(questions) == 1
        assert questions[0]["type"] == "open_ended"
        assert "correct_answer" in questions[0]
        assert "difficulty" in questions[0]

def test_add_explanation(question_generator):
    """Тест добавления объяснений к вопросам"""
    question = {
        "type": "multiple_choice",
        "question": "What is Python?",
        "correct_answer": "A programming language"
    }
    text = "Python is a programming language."
    
    with patch.object(question_generator.model, 'generate') as mock_generate, \
         patch.object(question_generator.tokenizer, 'decode') as mock_decode:
        
        mock_generate.return_value = torch.tensor([[1, 2, 3]])
        mock_decode.return_value = "Python is classified as a programming language because it is used to write computer programs."
        
        result = question_generator._add_explanation(question, text)
        
        assert "explanation" in result
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 0

def test_calculate_difficulty(question_generator):
    """Тест расчета сложности вопросов"""
    # Простой вопрос
    assert question_generator._calculate_difficulty("", "What is your name?") == "easy"
    
    # Вопрос средней сложности
    assert question_generator._calculate_difficulty("", "What are the primary characteristics of Python?") == "medium"
    
    # Сложный вопрос
    assert question_generator._calculate_difficulty("", "What are the implications of using asynchronous programming paradigms?") == "hard"

def test_negate_statement(question_generator):
    """Тест преобразования утверждений в отрицание"""
    # Простое отрицание
    assert "is not" in question_generator._negate_statement("Python is a programming language")
    
    # Отрицание с множественным числом
    assert "are not" in question_generator._negate_statement("Lists are mutable")
    
    # Сложное отрицание
    statement = "This statement has no simple negation"
    assert question_generator._negate_statement(statement).startswith("It is not true that") 