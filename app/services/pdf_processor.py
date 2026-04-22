import pdfplumber
import tempfile
import os
import logging

logger = logging.getLogger(__name__)


def extract_text(file_input):
    """
    Supports:
    - file path (recommended)
    - UploadFile (fallback)
    Returns empty string if extraction fails
    """

    text = ""
    temp_path = None

    try:
        # -------------------------------
        # CASE 1: FILE PATH (BEST)
        # -------------------------------
        if isinstance(file_input, str):
            if not os.path.exists(file_input):
                logger.error(f"PDF file not found: {file_input}")
                return ""

            with pdfplumber.open(file_input) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            return text.strip()

        # -------------------------------
        # CASE 2: UploadFile (Fallback)
        # -------------------------------
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(file_input.file.read())
                temp_path = tmp.name

            with pdfplumber.open(temp_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"

            return text.strip()

    except Exception as e:
        logger.error(f"PDF extraction error: {str(e)}")
        return ""

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception as e:
                logger.warning(f"Could not clean up temp file: {str(e)}")