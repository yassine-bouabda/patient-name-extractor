import json
import io
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

client = TestClient(app)


def load_sample_document():
    """Load the sample document for testing"""
    with open("data/sample_doc.json", "r", encoding="utf-8") as f:
        return json.load(f)


def create_json_file(data):
    """Create a mock JSON file for upload testing"""
    json_content = json.dumps(data, ensure_ascii=False)
    return io.BytesIO(json_content.encode("utf-8"))


# Basic endpoint tests
def test_root__should_return_welcome_message():
    """Test root endpoint returns welcome message"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Medical Documents API" in response.json()["message"]


def test_health__should_return_healthy_status():
    """Test health endpoint returns healthy status"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# Document validation tests
def test_validate_document__should_return_success_when_valid_document():
    """Test document validation with valid sample document"""
    sample_doc = load_sample_document()
    file_content = create_json_file(sample_doc)

    response = client.post(
        "/validate",
        files={"file": ("sample_doc.json", file_content, "application/json")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_validate_document__should_return_error_when_invalid_file():
    """Test document validation with invalid file"""
    text_content = b"This is not JSON"

    response = client.post(
        "/validate",
        files={"file": ("test.txt", io.BytesIO(text_content), "text/plain")},
    )

    assert response.status_code == 400


# Patient extraction tests
def test_extract_patient__should_return_patient_name_when_valid_sample_document():
    """Test patient extraction with sample document containing Monsieur Jean DUPONT"""
    sample_doc = load_sample_document()
    file_content = create_json_file(sample_doc)

    response = client.post(
        "/extract-patient",
        files={"file": ("sample_doc.json", file_content, "application/json")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["patient_name"] is not None
    assert data["patient_name"]["first_name"] == "Jean"
    assert data["patient_name"]["family_name"] == "DUPONT"


def test_extract_patient__should_return_none_when_no_patient_found():
    """Test patient extraction when no patient name is found"""
    doc_without_patient = {
        "pages": [
            {
                "words": [
                    {
                        "text": "consultation",
                        "bbox": {
                            "x_min": 0.1,
                            "x_max": 0.2,
                            "y_min": 0.1,
                            "y_max": 0.2,
                        },
                    },
                    {
                        "text": "médicale",
                        "bbox": {
                            "x_min": 0.2,
                            "x_max": 0.3,
                            "y_min": 0.1,
                            "y_max": 0.2,
                        },
                    },
                ]
            }
        ]
    }
    file_content = create_json_file(doc_without_patient)

    response = client.post(
        "/extract-patient",
        files={"file": ("no_patient.json", file_content, "application/json")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["patient_name"] is None


def test_extract_patient__should_return_error_when_invalid_file():
    """Test patient extraction with invalid file"""
    text_content = b"This is not JSON"

    response = client.post(
        "/extract-patient",
        files={"file": ("test.txt", io.BytesIO(text_content), "text/plain")},
    )

    assert response.status_code == 400
