from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import ValidationError
import logging
from name_extractor import NameExtractor, InvalidDocumentFormat
from schemas import MedicalDocument
from utils import parse_json_file

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Medical Documents API")

name_extractor = NameExtractor()


@app.get("/")
async def root():
    return {"message": "Medical Documents API with Enhanced Name Extraction"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "extractor": "ready"}


@app.post("/validate")
async def validate_document(file: UploadFile = File(...)):
    try:
        data = await parse_json_file(file)
        doc = MedicalDocument.model_validate(data)
        return {"success": True, "document_id": doc.document_id}
    except ValidationError as e:
        raise HTTPException(400, [str(err) for err in e.errors()])


@app.post("/extract-patient")
async def extract_patient(file: UploadFile = File(...)):
    try:
        data = await parse_json_file(file)
        doc = MedicalDocument.model_validate(data)

        doc_dict = doc.model_dump()

        patient_name = await name_extractor.extract_patient_name_from_document(doc_dict)

        return {
            "success": True,
            "document_id": doc.document_id,
            "patient_name": patient_name.to_dict()
            if patient_name
            else None,  # Handle None case
        }
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(400, [str(err) for err in e.errors()])
    except InvalidDocumentFormat as e:
        return {"success": False, "error": f"Invalid document format: {str(e)}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"success": False, "error": "Internal server error"}
