"""
Document service for vector search with ChromaDB
"""

import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings

from app.core.config import settings

# Security import
from security.input_validation import validate_input


class DocumentService:
    """Service for document indexing and semantic search"""

    def __init__(self):
        # Initialize ChromaDB
        self.chroma_path = Path("data/chroma")
        self.chroma_path.mkdir(parents=True, exist_ok=True)

        self.client = chromadb.PersistentClient(path=str(self.chroma_path), settings=Settings(anonymized_telemetry=False))

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="documents", metadata={"description": "User document embeddings"}
        )

    async def add_document(self, doc_id: str, text: str, metadata: Optional[Dict] = None):
        """Add document to vector store"""

        # Security: Validate document text
        is_valid, sanitized_text, error = validate_input(text)
        if not is_valid:
            raise ValueError(f"Invalid document text: {error}")

        # ChromaDB requires non-empty metadata or None
        if metadata is not None and len(metadata) == 0:
            metadata = None

        # Add default metadata if None
        if metadata is None:
            metadata = {"source": "user_upload"}

        self.collection.add(ids=[doc_id], documents=[sanitized_text], metadatas=[metadata])

    async def search_documents(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search documents by semantic similarity"""

        # Security: Validate search query
        is_valid, sanitized_query, error = validate_input(query)
        if not is_valid:
            raise ValueError(f"Invalid search query: {error}")

        results = self.collection.query(query_texts=[query], n_results=n_results)

        # Format results
        formatted_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append(
                    {
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if results.get("distances") else None,
                    }
                )

        return formatted_results

    async def delete_document(self, doc_id: str):
        """Delete document from vector store"""
        try:
            self.collection.delete(ids=[doc_id])
        except Exception:
            pass  # Document may not exist

    async def get_document_count(self) -> int:
        """Get total number of documents"""
        return self.collection.count()
