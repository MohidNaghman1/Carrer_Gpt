import os
import fitz  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.document import Document # Used to store chunks with metadata

# 1. Function to read PDF text (no changes needed)
def read_pdf_text(pdf_path):
    """Reads and extracts all text from a given PDF file."""
    try:
        with fitz.open(pdf_path) as doc:
            full_text = "".join(page.get_text() for page in doc)
        return full_text
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

# 2. Function to process all PDFs in a list of folders
def process_all_folders(folder_paths):
    """
    Reads all PDFs from a list of folders, chunks them, and adds metadata.
    
    Args:
        folder_paths (list): A list of paths to the folders containing PDFs.
        
    Returns:
        list[Document]: A list of LangChain Document objects, ready for embedding.
    """
    all_documents = []
    
    # Initialize the Text Splitter once
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150
    )

    for folder_path in folder_paths:
        if not os.path.isdir(folder_path):
            print(f"Warning: Folder not found at '{folder_path}'. Skipping.")
            continue
        
        print(f"\n--- Processing folder: {folder_path} ---")
        
        for filename in os.listdir(folder_path):
            if filename.lower().endswith('.pdf'):
                file_path = os.path.join(folder_path, filename)
                
                # a. Read the PDF
                print(f"  - Reading '{filename}'...")
                text = read_pdf_text(file_path)
                
                if not text or not text.strip():
                    print(f"    - Could not extract text from '{filename}'. Skipping.")
                    continue
                
                # b. Chunk the text
                chunks = text_splitter.split_text(text)
                
                # c. Create Document objects with metadata for each chunk
                for i, chunk_text in enumerate(chunks):
                    # The metadata is KEY! It tells us the source of the information.
                    metadata = {
                        "source_file": filename,
                        "source_folder": os.path.basename(folder_path) # e.g., 'Roadmap', 'Resume'
                    }
                    doc = Document(page_content=chunk_text, metadata=metadata)
                    all_documents.append(doc)
                
                print(f"    - Success! Created {len(chunks)} chunks.")

    return all_documents


# --- MAIN EXECUTION ---
if __name__ == "__main__":
    # Define the folders your data is in
    base_folder = "carrer_docs"
    folders_to_process = [
        os.path.join(base_folder, "Roadmap"),
        os.path.join(base_folder, "Resume"),
        os.path.join(base_folder, "Courses")
    ]
    
    # Run the main processing function
    documents = process_all_folders(folders_to_process)
    
    # Verification
    print("\n\n==============================================")
    print("✅✅✅ TOTAL PROCESSING COMPLETE ✅✅✅")
    print(f"Total number of document chunks created: {len(documents)}")
    
    if documents:
        print("\n--- Example of a processed document chunk ---")
        # Let's look at the first chunk
        print(f"Content (first 100 chars): {documents[0].page_content[:100]}...")
        print(f"Metadata: {documents[0].metadata}")
        
        print("\n--- Example of another processed document chunk (from the middle) ---")
        # Let's look at a chunk from the middle of the list
        middle_index = len(documents) // 2
        print(f"Content (first 100 chars): {documents[middle_index].page_content[:100]}...")
        print(f"Metadata: {documents[middle_index].metadata}")