# langgraph_core/utils/file_parser.py
import fitz
import docx

def extract_text_from_file(file_input):
    """Extracts text from a PDF or DOCX file-like object."""
    try:
        # --- THIS IS THE CRITICAL FIX ---
        # Rewind the file-like object's cursor to the beginning (position 0)
        # This ensures that we can read it even if it has been read before.
        file_input.seek(0)
        # --- END OF FIX ---

        if file_input.name.endswith('.pdf'):
            # Read the raw bytes from the file-like object for fitz
            pdf_bytes = file_input.read()
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                return "".join(page.get_text() for page in doc)
        
        elif file_input.name.endswith('.docx'):
            # python-docx can read the file-like object directly
            doc = docx.Document(file_input)
            return "\n".join([para.text for para in doc.paragraphs])
        
        else:
            return "Error: Unsupported file type."
            
    except Exception as e:
        return f"Error: Could not read the file content. Reason: {e}"