"""

"""

from typing import List, Optional
from haystack import component, logging
from langchain_core.documents import Document as LangChainDocument
from typing import List, Optional, Dict, Any

from haystack import component, logging
from haystack.dataclasses import Document as HaystackDocument

logger = logging.getLogger(__name__)


@component
class DocumentToLangChainConverter:
    """
    Haystack 2.0 component to convert Haystack Documents to LangChain Documents.
    
    This bridge component allows Haystack document processing pipelines to work
    with Ragas components that expect LangChain document format.
    """
    
    @component.output_types(langchain_documents=List[LangChainDocument], document_count=int)
    def run(self, documents: List[HaystackDocument]) -> Dict[str, Any]:
        """
        Convert Haystack Documents to LangChain Documents.
        
        Args:
            documents (List[HaystackDocument]): Haystack documents to convert.
            
        Returns:
            Dict containing converted documents and count.
        """
        if not documents:
            return {"langchain_documents": [], "document_count": 0}
        
        try:
            langchain_docs = []
            
            for doc in documents:
                langchain_doc = LangChainDocument(
                    page_content=doc.content,
                    metadata=doc.meta or {}
                )
                langchain_docs.append(langchain_doc)
            
            logger.info(f"Converted {len(langchain_docs)} Haystack documents to LangChain format")
            
            return {
                "langchain_documents": langchain_docs,
                "document_count": len(langchain_docs)
            }
            
        except Exception as e:
            logger.error(f"Failed to convert documents: {e}")
            return {"langchain_documents": [], "document_count": 0}
        



