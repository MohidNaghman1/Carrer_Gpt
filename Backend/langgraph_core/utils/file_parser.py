# utils/file_parser.py
import fitz  # PyMuPDF
import docx

def extract_text_from_file(file_input):
    """Extracts text from a PDF or DOCX file-like object."""
    try:
        # The 'name' attribute helps determine the file type
        if file_input.name.endswith('.pdf'):
            with fitz.open(stream=file_input.read(), filetype="pdf") as doc:
                return "".join(page.get_text() for page in doc)
        elif file_input.name.endswith('.docx'):
            doc = docx.Document(file_input)
            return "\n".join([para.text for para in doc.paragraphs])
        else:
            return "Error: Unsupported file type."
    except Exception as e:
        return f"Error: Could not read the file content. Reason: {e}"