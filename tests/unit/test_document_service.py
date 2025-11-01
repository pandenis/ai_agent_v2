"""
Unit tests for document service
"""
import pytest
from app.services.document_service import DocumentService


@pytest.mark.asyncio
async def test_add_and_search_documents():
    """Test adding and searching documents"""
    service = DocumentService()
    
    # Add test documents
    await service.add_document(
        doc_id="doc1",
        text="Python is a programming language used for AI and web development",
        metadata={"type": "tutorial"}
    )
    
    await service.add_document(
        doc_id="doc2",
        text="JavaScript is used for web frontend development",
        metadata={"type": "tutorial"}
    )
    
    # Search for Python-related content
    results = await service.search_documents("programming AI Python", n_results=2)
    
    assert len(results) > 0
    assert "Python" in results[0]["text"] or "programming" in results[0]["text"]


@pytest.mark.asyncio
async def test_document_count():
    """Test getting document count"""
    service = DocumentService()
    
    initial_count = await service.get_document_count()
    
    # Add a document with metadata
    await service.add_document(
        doc_id="test-count",
        text="Test document for counting",
        metadata={"source": "test"}
    )
    
    new_count = await service.get_document_count()
    assert new_count >= initial_count


@pytest.mark.asyncio
async def test_delete_document():
    """Test deleting a document"""
    service = DocumentService()
    
    doc_id = "test-delete"
    
    # Add document with metadata
    await service.add_document(
        doc_id=doc_id,
        text="Document to be deleted",
        metadata={"source": "test"}
    )
    
    # Delete it
    await service.delete_document(doc_id)
    
    # Search should not find it
    results = await service.search_documents("Document to be deleted", n_results=10)
    matching = [r for r in results if r["id"] == doc_id]
    assert len(matching) == 0


@pytest.mark.asyncio
async def test_add_document_without_metadata():
    """Test adding document without explicit metadata (should add default)"""
    service = DocumentService()
    
    doc_id = "test-no-metadata"
    
    # Add document without metadata
    await service.add_document(
        doc_id=doc_id,
        text="Document without metadata"
    )
    
    # Search for it
    results = await service.search_documents("Document without metadata", n_results=5)
    
    # Should find it
    matching = [r for r in results if r["id"] == doc_id]
    assert len(matching) > 0
    assert matching[0]["metadata"]["source"] == "user_upload"
