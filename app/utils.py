import os
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def load_and_chunk_document(file_path: str, chunk_size=1000, chunk_overlap=100):
    # Absolute path check
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        print(f"ERROR: File does not exist at {abs_path}")
        return []

    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    try:
        if ext == ".txt":
            # Direct reading is safer for simple text files
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    with open(abs_path, 'r', encoding=encoding) as f:
                        text = f.read().strip()
                    if text: break 
                except UnicodeDecodeError:
                    continue
        elif ext == ".pdf":
            loader = PyPDFLoader(abs_path)
            docs = loader.load()
            text = "\n".join([d.page_content for d in docs])
        elif ext == ".docx":
            loader = Docx2txtLoader(abs_path)
            docs = loader.load()
            text = "\n".join([d.page_content for d in docs])
        
        # Diagnostic Print
        print(f"DEBUG: Loaded {len(text)} characters from {file_path}")
        if len(text) < 10:
            print(f"WARNING: Text content is suspiciously short: '{text}'")

    except Exception as e:
        print(f"ERROR loading {file_path}: {str(e)}")
        return []

    if not text:
        return []

    # Create Document object for the splitter
    doc = Document(page_content=text, metadata={"source": file_path})
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    chunks = splitter.split_documents([doc])
    print(f"DEBUG: Created {len(chunks)} chunks.")
    return chunks