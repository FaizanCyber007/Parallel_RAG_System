import os
from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEndpointEmbeddings

class CHROMAVectorStore:
    """LangChain-based ChromaDB Vector Store for RAG Pipeline"""
    
    def __init__(self, collection_name: str = 'legal_texts_pipeline', 
                 persistent_directory: str = './src/vectorStore', 
                 embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2', 
                 chunk_size: int = 800, 
                 chunk_overlap: int = 200):
        self.collection_name = collection_name
        self.persistent_directory = persistent_directory
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.embedding_function = None
        self.vectorstore = None
        self.text_splitter = None
        self._initialize_store()

    def _get_hf_token(self) -> str:
        """Read HuggingFace token from backend/.env file"""
        backend_env_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'backend', '.env'
        )
        token = None
        
        if os.path.exists(backend_env_path):
            with open(backend_env_path, 'r') as f:
                for line in f:
                    if line.startswith('HUGGINGFACE_API_KEY='):
                        token = line.strip().split('=', 1)[1]
                        break
        
        if not token:
            raise ValueError("HUGGINGFACE_API_KEY not found in backend/.env file")
        
        return token

    def _initialize_store(self):
        """Initialize ChromaDB vector store using LangChain"""
        print("Initializing ChromaDB vector store with LangChain...")
        
        os.makedirs(self.persistent_directory, exist_ok=True)
        
        # Initialize embedding function
        token = self._get_hf_token()
        self.embedding_function = HuggingFaceEndpointEmbeddings(
            repo_id=self.embedding_model_name,
            huggingfacehub_api_token=token,
        )
        print(f"Embedding model loaded: {self.embedding_model_name}")
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=['\n\n', '\n', ' ', '']
        )
        
        # Initialize or load ChromaDB vector store
        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
            persist_directory=self.persistent_directory
        )
        
        print(f"Vector store initialized. Collection: {self.collection_name}")
        print(f"Existing documents in collection: {self.vectorstore._collection.count()}")
    
    def load(self):
        """Load existing vector store"""
        print(f"Vector store loaded. Collection: {self.collection_name}")
        print(f"Existing documents in collection: {self.vectorstore._collection.count()}")

    def load_and_add_docs(self, documents: List[Any]):
        """Split documents and add to vector store using LangChain"""
        print(f"Processing {len(documents)} documents...")
        
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        print(f"Split into {len(chunks)} chunks")
        
        # Add to vector store
        self.vectorstore.add_documents(documents=chunks)
        
        print(f"Successfully added {len(chunks)} chunks to vector store")
        print(f"Total documents in collection: {self.vectorstore._collection.count()}")
    
    def get_retriever(self, search_type: str = "similarity", k: int = 5):
        """Get LangChain retriever interface"""
        return self.vectorstore.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )
    
    @property
    def collection(self):
        """Backward compatibility: access underlying ChromaDB collection"""
        return self.vectorstore._collection