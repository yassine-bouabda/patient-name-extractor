from fastapi import HTTPException
import json
from fastapi import UploadFile


def _is_valid_french_first_name(name: str) -> bool:
    """
    Validate French first name:
    - Starts with capital letter, rest lowercase
    - Only alphabetic characters
    - At least 2 characters long
    """
    return (
        name
        and len(name) >= 2
        and name[0].isupper()
        and name[1:].islower()
        and name.isalpha()
    )


def _is_valid_french_family_name(name: str) -> bool:
    """
    Validate French family name:
    - All uppercase letters
    - Only alphabetic characters
    - At least 2 characters long
    """
    return name and len(name) >= 2 and name.isupper() and name.isalpha()


async def parse_json_file(file: UploadFile) -> dict:
    if file.content_type != "application/json":
        raise HTTPException(400, "Only JSON files accepted")

    content = await file.read()

    # Add 100 character minimum check
    if len(content) < 100:
        raise HTTPException(400, "JSON file must contain at least 100 characters")

    try:
        return json.loads(content.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(400, "Invalid JSON file")
