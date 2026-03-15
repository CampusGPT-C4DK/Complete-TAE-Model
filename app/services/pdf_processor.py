import pdfplumber
import tempfile
import os


def extract_text(upload_file):

    # ⭐ save UploadFile to temp file first
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:

        tmp.write(upload_file.file.read())

        temp_path = tmp.name

    text = ""

    try:
        with pdfplumber.open(temp_path) as pdf:

            for page in pdf.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

    finally:
        os.remove(temp_path)

    return text.strip()