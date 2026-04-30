from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List
from pathlib import Path
import uvicorn
import os
import shutil
import tempfile

# RAG imports
from src.search import RAGRetriever
from src.vectorstore import CHROMAVectorStore
from src.re_ranking import parallel_rerank, load_config

# OCR import
from ocr import process_files_parallel

app = FastAPI(title="RAG Pipeline API")

# -------------------------
# Request Model
# -------------------------
class ChatRequest(BaseModel):
    query: str
    model_id: str = None
    rerank: bool = False
    rerank_k: int = None

# -------------------------
# Global Vector Store
# -------------------------
store = None

@app.on_event("startup")
async def startup_event():
    global store
    print("Loading Vector Store...")
    store = CHROMAVectorStore()
    store.load()
    print("Vector Store Loaded.")

# -------------------------
# RAG RETRIEVAL (UNCHANGED)
# -------------------------
@app.post("/retrieve")
async def retrieve(request: ChatRequest):
    global store
    if not store:
        raise HTTPException(status_code=500, detail="Vector store not initialized")

    try:
        retriever = RAGRetriever(vector_store=store)

        print(f"Retrieving documents for query: {request.query}")

        # Default retrieval
        top_k = 5

        # Expand pool when reranking
        if request.rerank:
            cfg = load_config()
            top_k = cfg.get("top_n", 50)

        results = retriever.retrieve(query=request.query, top_k=top_k)

        if request.rerank:
            print("Running parallel re-ranking...")
            reranked = parallel_rerank(request.query, results)
            return {"results": reranked}

        return {"results": results}

    except Exception as e:
        print(f"Error processing retrieval: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# -------------------------
# OCR + INDEXING ENDPOINT
# -------------------------
@app.post("/extract-text")
async def extract_text(files: List[UploadFile] = File(...)):
    global store
    if not store:
        raise HTTPException(status_code=500, detail="Vector store not initialized")

    temp_dir = tempfile.mkdtemp()
    saved_file_paths = []

    try:
        # Save uploaded files
        for file in files:
            file_path = Path(temp_dir) / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            saved_file_paths.append(file_path)

        print(f"Processing {len(saved_file_paths)} files using OCR...")

        # OCR + PDF extraction
        documents = process_files_parallel(saved_file_paths)

        if not documents:
            return {
                "extracted_text": "No readable text found in uploaded files.",
                "document_count": 0,
                "status": "no_text"
            }

        # Index into vector store
        print(f"Indexing {len(documents)} documents into vector store...")
        store.load_and_add_docs(documents)

        # Combine extracted text (for frontend preview)
        extracted_texts = []
        for doc in documents:
            source = doc.metadata.get("source_file", "unknown")
            extracted_texts.append(
                f"--- Content from {source} ---\n{doc.page_content}"
            )

        return {
            "extracted_text": "\n\n".join(extracted_texts),
            "document_count": len(documents),
            "status": "indexed"
        }

    except Exception as e:
        print(f"OCR error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# -------------------------
# RUN SERVER
# -------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
