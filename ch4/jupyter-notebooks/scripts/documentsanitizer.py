from typing import List
from haystack import component, Document

@component
class DocumentSanitizer:
    """
    A Data Quality Gate.
    Filters out documents that have no content (None) or are just empty strings.
    """
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document]):
        # Keep only documents where content is not None and not empty
        valid_documents = [
            doc for doc in documents 
            if doc.content is not None and doc.content.strip() != ""
        ]
        
        # Optional: Log how many were dropped
        dropped_count = len(documents) - len(valid_documents)
        if dropped_count > 0:
            print(f"Sanitizer: Dropped {dropped_count} invalid/empty documents.")
            
        return {"documents": valid_documents}