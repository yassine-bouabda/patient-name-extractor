import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Set
from utils import _is_valid_french_first_name, _is_valid_french_family_name


@dataclass
class NameExtractorConfig:
    """Configuration for NameExtractor behavior"""

    offset_next_line: int = 5
    sort_document: bool = True
    name_prefixes: Set[str] = field(
        default_factory=lambda: {
            "monsieur",
            "madame",
            "mme",
            "mlle",
            "mr",
            "mrs",
            "Mrs",
            "Mme",
            "Mlle",
        }
    )
    doctor_prefixes: Set[str] = field(default_factory=lambda: {"dr", "docteur"})
    nom_keywords: Set[str] = field(
        default_factory=lambda: {"nom:", "nom", "nom de famille", "famille"}
    )
    prenom_keywords: Set[str] = field(default_factory=lambda: {"prénom", "prenom"})
    patient_keywords: Set[str] = field(default_factory=lambda: {"patient:", "patient"})


class InvalidDocumentFormat(Exception):
    """Raised when document format is invalid"""

    pass


class PatientName:
    def __init__(
        self,
        first_name_index: int,
        family_name_index: int,
        first_name: str,
        family_name: str,
    ):
        self.first_name_index = first_name_index
        self.family_name_index = family_name_index
        self.first_name = first_name
        self.family_name = family_name
        self._validate()

    def _validate(self):
        """Validate French name format without position constraints"""
        if not _is_valid_french_first_name(self.first_name):
            raise ValueError(f"Invalid French first name format: {self.first_name}")
        if not _is_valid_french_family_name(self.family_name):
            raise ValueError(f"Invalid French family name format: {self.family_name}")

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for API responses"""
        return {"first_name": self.first_name, "family_name": self.family_name}


class NameExtractor:
    def __init__(self, config: NameExtractorConfig = None):
        self.config = config or NameExtractorConfig()
        self.logger = logging.getLogger(__name__)

    async def extract_patient_name_from_document(
        self, document: dict
    ) -> Optional[PatientName]:
        """Extract patient name from document

        Args:
            document: Document containing pages with words

        Returns:
            PatientName if found, None otherwise

        Raises:
            InvalidDocumentFormat: If document structure is invalid
        """
        try:
            if "pages" not in document:
                raise InvalidDocumentFormat("Document must contain 'pages' field")

            self.logger.info(f"Processing document with {len(document['pages'])} pages")

            for page_idx, page in enumerate(document["pages"]):
                self.logger.debug(f"Processing page {page_idx}")
                patient_name = await self.detect_patient_name_from_page(page)
                if patient_name:
                    self.logger.info(
                        f"Found patient name: {patient_name.first_name} {patient_name.family_name}"
                    )
                    return patient_name

            self.logger.info("No patient name found in document")
            return None

        except KeyError as e:
            raise InvalidDocumentFormat(f"Missing required field: {e}")
        except Exception as e:
            self.logger.error(f"Error processing document: {e}")
            raise

    async def detect_patient_name_from_page(self, page: Dict) -> Optional[PatientName]:
        """Detect patient name from a single page

        Args:
            page: Page containing words with text and bbox

        Returns:
            PatientName if found, None otherwise
        """
        try:
            if "words" not in page:
                raise InvalidDocumentFormat("Page must contain 'words' field")

            words = page["words"]
            if not words:
                return None

            if self.config.sort_document:
                sorted_words_by_y = sorted(words, key=lambda x: x["bbox"]["y_min"])
                sorted_words = sorted(
                    sorted_words_by_y, key=lambda x: x["bbox"]["x_min"]
                )
            else:
                sorted_words = words

            detected_name = await self._detect_patient_name_using_prefix(sorted_words)
            if detected_name:
                return detected_name

            detected_name = await self._detect_patient_name_using_keywords(sorted_words)
            if detected_name:
                return detected_name

            return None

        except KeyError as e:
            raise InvalidDocumentFormat(f"Invalid page structure: {e}")

    async def _detect_patient_name_using_prefix(
        self, sorted_words: List[Dict]
    ) -> Optional[PatientName]:
        """Detect patient name using prefixes like Monsieur, Madame, etc."""
        for i, word_obj in enumerate(sorted_words):
            if i + 2 >= len(sorted_words):
                continue

            prefix_text = word_obj["text"].lower()
            if prefix_text not in self.config.name_prefixes:
                continue

            name_parts = [sorted_words[i + 1]["text"], sorted_words[i + 2]["text"]]

            if _is_valid_french_first_name(
                name_parts[0]
            ) and _is_valid_french_family_name(name_parts[1]):
                return PatientName(i + 1, i + 2, name_parts[0], name_parts[1])

            if _is_valid_french_first_name(
                name_parts[1]
            ) and _is_valid_french_family_name(name_parts[0]):
                return PatientName(i + 2, i + 1, name_parts[1], name_parts[0])

        return None

    async def _detect_patient_name_using_keywords(
        self, sorted_words: List[Dict]
    ) -> Optional[PatientName]:
        """Detect patient name using French keywords like Nom: and Prénom: or patient:"""
        words_text = [w["text"].strip(" :") for w in sorted_words if w["text"].strip()]

        result = await self._try_separate_keywords(words_text)
        if result:
            return result

        result = await self._try_patient_keyword(words_text)
        if result:
            return result

        return None

    async def _try_separate_keywords(self, words: List[str]) -> Optional[PatientName]:
        """Try to find separate Nom: and Prénom: keywords"""
        first_name = None
        family_name = None
        first_name_idx = None
        family_name_idx = None

        for i, word in enumerate(words):
            word_lower = word.lower().rstrip(":")

            if word_lower in self.config.nom_keywords and i + 1 < len(words):
                potential_family = words[i + 1]
                if _is_valid_french_family_name(potential_family):
                    family_name = potential_family
                    family_name_idx = i + 1

            elif word_lower in self.config.prenom_keywords and i + 1 < len(words):
                potential_first = words[i + 1]
                if _is_valid_french_first_name(potential_first):
                    first_name = potential_first
                    first_name_idx = i + 1

        if (
            first_name
            and family_name
            and first_name_idx is not None
            and family_name_idx is not None
        ):
            return PatientName(first_name_idx, family_name_idx, first_name, family_name)

        return None

    async def _try_patient_keyword(self, words: List[str]) -> Optional[PatientName]:
        """Try to find patient keyword followed by names"""
        for i, word in enumerate(words):
            word_lower = word.lower().rstrip(":")

            if word_lower not in self.config.patient_keywords:
                continue

            max_search = min(i + self.config.offset_next_line, len(words) - 1)
            for j in range(i + 1, max_search):
                if j + 1 >= len(words):
                    break

                current_word = words[j]
                next_word = words[j + 1]

                if _is_valid_french_first_name(
                    current_word
                ) and _is_valid_french_family_name(next_word):
                    return PatientName(j, j + 1, current_word, next_word)

        return None
