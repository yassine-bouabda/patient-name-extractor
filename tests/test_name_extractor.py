import pytest
import sys
import os

# Add parent directory to path to import name_extractor
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from name_extractor import (
    NameExtractor,
    PatientName,
)


# PatientName class tests
def test_patient_name__should_create_valid_object_when_valid_names():
    """Test creating a valid PatientName object"""
    patient = PatientName(0, 1, "Jean", "DUPONT")
    assert patient.first_name == "Jean"
    assert patient.family_name == "DUPONT"


def test_patient_name__should_raise_error_when_invalid_first_name():
    """Test that invalid first name raises ValueError"""
    with pytest.raises(ValueError):
        PatientName(0, 1, "jean", "DUPONT")  # lowercase first name


def test_patient_name__should_raise_error_when_invalid_family_name():
    """Test that invalid family name raises ValueError"""
    with pytest.raises(ValueError):
        PatientName(0, 1, "Jean", "dupont")  # lowercase family name


# NameExtractor._detect_patient_name_using_prefix tests
@pytest.mark.asyncio
async def test_detect_patient_name_using_prefix__should_return_patient_name_when_monsieur_prefix():
    """Test detection with Monsieur prefix"""
    extractor = NameExtractor()
    sorted_words = [
        {
            "text": "Monsieur",
            "bbox": {"x_min": 0.75, "x_max": 0.81, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "Jean",
            "bbox": {"x_min": 0.81, "x_max": 0.87, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "DUPONT",
            "bbox": {"x_min": 0.87, "x_max": 0.93, "y_min": 0.09, "y_max": 0.1},
        },
    ]
    result = await extractor._detect_patient_name_using_prefix(sorted_words)
    assert result is not None
    assert result.first_name == "Jean"
    assert result.family_name == "DUPONT"


@pytest.mark.asyncio
async def test_detect_patient_name_using_prefix__should_return_none_when_no_prefix():
    """Test when no valid prefix is found"""
    extractor = NameExtractor()
    sorted_words = [
        {
            "text": "Patient",
            "bbox": {"x_min": 0.75, "x_max": 0.81, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "Jean",
            "bbox": {"x_min": 0.81, "x_max": 0.87, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "DUPONT",
            "bbox": {"x_min": 0.87, "x_max": 0.93, "y_min": 0.09, "y_max": 0.1},
        },
    ]
    result = await extractor._detect_patient_name_using_prefix(sorted_words)
    assert result is None


# NameExtractor._detect_patient_name_using_keywords tests
@pytest.mark.asyncio
async def test_detect_patient_name_using_keywords__should_return_patient_name_when_patient_keyword():
    """Test detection with patient keyword"""
    extractor = NameExtractor()
    sorted_words = [
        {
            "text": "patient",
            "bbox": {"x_min": 0.75, "x_max": 0.81, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "Jean",
            "bbox": {"x_min": 0.81, "x_max": 0.87, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "DUPONT",
            "bbox": {"x_min": 0.87, "x_max": 0.93, "y_min": 0.09, "y_max": 0.1},
        },
    ]
    result = await extractor._detect_patient_name_using_keywords(sorted_words)
    assert result is not None
    assert result.first_name == "Jean"
    assert result.family_name == "DUPONT"


@pytest.mark.asyncio
async def test_detect_patient_name_using_keywords__should_return_patient_name_when_nom_prenom_keywords():
    """Test detection with Nom: and Prénom: keywords"""
    extractor = NameExtractor()
    sorted_words = [
        {
            "text": "Nom:",
            "bbox": {"x_min": 0.75, "x_max": 0.81, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "MARTIN",
            "bbox": {"x_min": 0.81, "x_max": 0.87, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "Prénom:",
            "bbox": {"x_min": 0.87, "x_max": 0.93, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "Pierre",
            "bbox": {"x_min": 0.93, "x_max": 0.99, "y_min": 0.09, "y_max": 0.1},
        },
    ]
    result = await extractor._detect_patient_name_using_keywords(sorted_words)
    assert result is not None
    assert result.first_name == "Pierre"
    assert result.family_name == "MARTIN"


@pytest.mark.asyncio
async def test_detect_patient_name_using_keywords__should_return_none_when_no_keywords():
    """Test when no valid keywords are found"""
    extractor = NameExtractor()
    sorted_words = [
        {
            "text": "consultation",
            "bbox": {"x_min": 0.75, "x_max": 0.81, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "Jean",
            "bbox": {"x_min": 0.81, "x_max": 0.87, "y_min": 0.09, "y_max": 0.1},
        },
        {
            "text": "DUPONT",
            "bbox": {"x_min": 0.87, "x_max": 0.93, "y_min": 0.09, "y_max": 0.1},
        },
    ]
    result = await extractor._detect_patient_name_using_keywords(sorted_words)
    assert result is None


# NameExtractor.detect_patient_name tests
@pytest.mark.asyncio
async def test_detect_patient_name__should_prioritize_prefix_over_keywords():
    """Test that prefix detection has priority over keyword detection"""
    extractor = NameExtractor()
    page = {
        "words": [
            {
                "text": "patient",
                "bbox": {"x_min": 0.70, "x_max": 0.75, "y_min": 0.09, "y_max": 0.1},
            },
            {
                "text": "Monsieur",
                "bbox": {"x_min": 0.75, "x_max": 0.81, "y_min": 0.09, "y_max": 0.1},
            },
            {
                "text": "Jean",
                "bbox": {"x_min": 0.81, "x_max": 0.87, "y_min": 0.09, "y_max": 0.1},
            },
            {
                "text": "DUPONT",
                "bbox": {"x_min": 0.87, "x_max": 0.93, "y_min": 0.09, "y_max": 0.1},
            },
        ]
    }
    result = await extractor.detect_patient_name_from_page(page)
    assert result is not None
    assert result.first_name == "Jean"
    assert result.family_name == "DUPONT"


@pytest.mark.asyncio
async def test_detect_patient_name__should_return_none_when_no_detection_possible():
    """Test when no detection method succeeds"""
    extractor = NameExtractor()
    page = {
        "words": [
            {
                "text": "consultation",
                "bbox": {"x_min": 0.75, "x_max": 0.81, "y_min": 0.09, "y_max": 0.1},
            },
            {
                "text": "hanche",
                "bbox": {"x_min": 0.81, "x_max": 0.87, "y_min": 0.09, "y_max": 0.1},
            },
            {
                "text": "bien",
                "bbox": {"x_min": 0.87, "x_max": 0.93, "y_min": 0.09, "y_max": 0.1},
            },
        ]
    }
    result = await extractor.detect_patient_name_from_page(page)
    assert result is None


# NameExtractor.extract_patient_name_from_document tests
@pytest.mark.asyncio
async def test_extract_patient_name_from_document__should_return_patient_name_when_valid_document():
    """Test extraction with valid document"""
    extractor = NameExtractor()
    document = {
        "pages": [
            {
                "words": [
                    {
                        "text": "Monsieur",
                        "bbox": {
                            "x_min": 0.75,
                            "x_max": 0.81,
                            "y_min": 0.09,
                            "y_max": 0.1,
                        },
                    },
                    {
                        "text": "Jean",
                        "bbox": {
                            "x_min": 0.81,
                            "x_max": 0.87,
                            "y_min": 0.09,
                            "y_max": 0.1,
                        },
                    },
                    {
                        "text": "DUPONT",
                        "bbox": {
                            "x_min": 0.87,
                            "x_max": 0.93,
                            "y_min": 0.09,
                            "y_max": 0.1,
                        },
                    },
                ]
            }
        ]
    }
    result = await extractor.extract_patient_name_from_document(document)
    assert result is not None
    assert result.first_name == "Jean"
    assert result.family_name == "DUPONT"


@pytest.mark.asyncio
async def test_extract_patient_name_from_document__should_return_none_when_no_patient_found():
    """Test extraction when no patient name is found"""
    extractor = NameExtractor()
    document = {
        "pages": [
            {
                "words": [
                    {
                        "text": "consultation",
                        "bbox": {
                            "x_min": 0.75,
                            "x_max": 0.81,
                            "y_min": 0.09,
                            "y_max": 0.1,
                        },
                    },
                    {
                        "text": "hanche",
                        "bbox": {
                            "x_min": 0.81,
                            "x_max": 0.87,
                            "y_min": 0.09,
                            "y_max": 0.1,
                        },
                    },
                    {
                        "text": "traitement",
                        "bbox": {
                            "x_min": 0.87,
                            "x_max": 0.93,
                            "y_min": 0.09,
                            "y_max": 0.1,
                        },
                    },
                ]
            }
        ]
    }
    result = await extractor.extract_patient_name_from_document(document)
    assert result is None
