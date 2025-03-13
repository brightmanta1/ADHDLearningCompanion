"""
Тесты для модуля извлечения концепций
"""

import pytest
from ADHDLOL.utils.concept_extractor import ConceptExtractor, ExtractedConcept


@pytest.fixture
def concept_extractor():
    """Фикстура для создания экземпляра ConceptExtractor"""
    return ConceptExtractor()


@pytest.fixture
def sample_text():
    """Фикстура с тестовым текстом"""
    return """
    Machine learning is a subset of artificial intelligence that focuses on data and algorithms.
    Neural networks are complex systems that can learn patterns. A neural network is defined as
    a computational model inspired by biological neurons.
    
    Deep learning refers to advanced neural networks with multiple layers. The concept of deep
    learning has revolutionized AI technology. Scientists like Geoffrey Hinton and Yann LeCun
    have made significant contributions to the field.
    
    In 2012, deep learning achieved remarkable results in computer vision tasks.
    """


def test_extract_concepts(concept_extractor, sample_text):
    """Тест извлечения концепций"""
    concepts = concept_extractor.extract_concepts(sample_text)

    assert len(concepts) > 0
    assert all(isinstance(c, ExtractedConcept) for c in concepts)

    # Проверяем наличие ключевых концепций
    concept_texts = [c.text.lower() for c in concepts]
    assert any("machine learning" in text for text in concept_texts)
    assert any("neural network" in text for text in concept_texts)
    assert any("deep learning" in text for text in concept_texts)


def test_extract_terms(concept_extractor, sample_text):
    """Тест извлечения терминов"""
    terms = concept_extractor.extract_terms(sample_text)

    assert isinstance(terms, dict)
    assert len(terms) > 0

    # Проверяем наличие определений
    assert any("neural network" in term.lower() for term in terms.keys())
    assert any("deep learning" in term.lower() for term in terms.keys())


def test_generate_tags(concept_extractor, sample_text):
    """Тест генерации тегов"""
    tags = concept_extractor.generate_tags(sample_text)

    assert isinstance(tags, list)
    assert len(tags) > 0
    assert len(tags) <= 10  # Проверяем ограничение на количество тегов

    # Проверяем наличие важных тегов
    tags_lower = [tag.lower() for tag in tags]
    assert any("learning" in tag for tag in tags_lower)
    assert any("neural" in tag for tag in tags_lower)
    assert any("ai" in tag or "artificial" in tag for tag in tags_lower)


def test_calculate_importance(concept_extractor):
    """Тест вычисления важности концепций"""
    text = "Deep learning is an important concept in AI. Neural networks are used in deep learning."
    concepts = concept_extractor.extract_concepts(text)

    # Проверяем, что важность в правильном диапазоне
    for concept in concepts:
        assert 0 <= concept.importance <= 1


def test_merge_similar_concepts(concept_extractor):
    """Тест объединения похожих концепций"""
    text = """
    Machine learning helps solve problems.
    ML is used in many applications.
    Machine Learning has transformed technology.
    """
    concepts = concept_extractor.extract_concepts(text)

    # Проверяем, что похожие концепции объединены
    concept_texts = [c.text.lower() for c in concepts]
    assert len([t for t in concept_texts if "machine learning" in t or "ml" in t]) == 1


def test_educational_terms(concept_extractor):
    """Тест распознавания образовательных терминов"""
    text = "Learning theory is important for understanding how students learn."
    concepts = concept_extractor.extract_concepts(text)

    # Проверяем наличие образовательных терминов
    educational_terms = [c for c in concepts if c.type == "EDUCATIONAL_TERM"]
    assert len(educational_terms) > 0


def test_error_handling(concept_extractor):
    """Тест обработки ошибок"""
    # Тест с пустым текстом
    assert concept_extractor.extract_concepts("") == []
    assert concept_extractor.extract_terms("") == {}
    assert concept_extractor.generate_tags("") == []

    # Тест с некорректным текстом
    assert concept_extractor.extract_concepts("   ") == []
    assert concept_extractor.extract_terms("   ") == {}
