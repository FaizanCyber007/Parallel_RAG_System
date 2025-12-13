from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.search import RAGRetriever
from src.vectorstore import CHROMAVectorStore
import uvicorn
import os

app = FastAPI(title="RAG Pipeline API")

class ChatRequest(BaseModel):
    query: str
    model_id: str = None  # Optional, not used anymore since LLM is in backend

# Global store instance to avoid reloading on every request
store = None

@app.on_event("startup")
async def startup_event():
    global store
    print("Loading Vector Store...")
    store = CHROMAVectorStore()
    store.load()
    print("Vector Store Loaded.")

@app.post("/retrieve")
async def retrieve(request: ChatRequest):
    global store
    if not store:
        raise HTTPException(status_code=500, detail="Vector store not initialized")
    
    try:
        retriever = RAGRetriever(vector_store=store)
        
        print(f"Retrieving documents for query: {request.query}")
        results = retriever.retrieve(query=request.query)
        
        return {"results": results}
    except Exception as e:
        print(f"Error processing retrieval: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
