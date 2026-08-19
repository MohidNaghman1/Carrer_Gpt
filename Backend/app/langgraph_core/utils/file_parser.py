# In Backend/langgraph_core/utils/file_parser.py
import fitz
import docx
from io import BytesIO # Make sure BytesIO is imported

def extract_text_from_file(file_bytes: bytes, filename: str):
    """Extracts text from raw bytes of a PDF or DOCX file."""
    try:
        # Create an in-memory file-like object from the bytes
        file_stream = BytesIO(file_bytes)

        if filename.lower().endswith('.pdf'):
            with fitz.open(stream=file_stream, filetype="pdf") as doc:
                return "".join(page.get_text() for page in doc)
        
        elif filename.lower().endswith('.docx'):
            # python-docx can read the file-like object directly
            doc = docx.Document(file_stream)
            return "\n".join([para.text for para in doc.paragraphs])
        
        else:
            return "Error: Unsupported file type."
            
    except Exception as e:
        return f"Error: Could not read the file content. Reason: {e}"