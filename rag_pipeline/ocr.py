import os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
import pytesseract
from PIL import Image

def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from a single image using OCR.
    """
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        print(f"Error OCR'ing {image_path}: {e}")
        return ""

def process_single_file(file_path: Path) -> list:
    """
    Process a single file (PDF or image) and return a list of Document objects.
    """
    if file_path.suffix.lower() == '.pdf':
        try:
            loader = PyPDFLoader(str(file_path))
            docs = loader.load()
            for doc in docs:
                doc.metadata['source_file'] = file_path.name
                doc.metadata['source_type'] = 'pdf'
            return docs
        except Exception as e:
            print(f"Error loading PDF {file_path.name}: {e}")
            return []
    elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
        try:
            text = extract_text_from_image(str(file_path))
            if text:
                doc = Document(page_content=text, metadata={'source_file': file_path.name, 'source_type': 'image'})
                return [doc]
            else:
                print(f"No text extracted from {file_path.name}")
                return []
        except Exception as e:
            print(f"Error processing image {file_path.name}: {e}")
            return []
    else:
        print(f"Unsupported file type: {file_path.name}")
        return []

def process_files_parallel(file_paths: list, max_workers: int = None) -> list:
    """
    Process multiple files in parallel and return a combined list of Document objects.
    """
    if max_workers is None:
        max_workers = os.cpu_count() or 4  # Default to CPU count or 4

    all_documents = []

    # OPTIMIZATION: If only one file, bypass the overhead of ProcessPoolExecutor
    if len(file_paths) == 1:
        print(f"Processing single file directly: {file_paths[0].name}")
        return process_single_file(file_paths[0])

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_file, file_path): file_path for file_path in file_paths}
        for future in as_completed(futures):
            docs = future.result()
            all_documents.extend(docs)
            print(f"Processed {futures[future].name}: {len(docs)} documents")

    return all_documents