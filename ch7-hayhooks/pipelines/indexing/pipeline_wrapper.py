from typing import List, Optional
from pathlib import Path
import os
from fastapi import UploadFile
from haystack.dataclasses import ByteStream
import mimetypes

from hayhooks import BasePipelineWrapper, log
from haystack import Pipeline
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import HTMLToDocument, PyPDFToDocument
from haystack.components.routers import FileTypeRouter
from haystack.components.joiners import DocumentJoiner
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.embedders import OpenAIDocumentEmbedder
from haystack.components.writers import DocumentWriter
from haystack.utils import Secret
from haystack.document_stores.types import DuplicatePolicy
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        """Initialize the indexing pipeline"""
        log.info("Setting up indexing pipeline...")
        
        # Initialize document store
        document_store = ElasticsearchDocumentStore(
            hosts=os.getenv("ELASTICSEARCH_HOST", "http://localhost:9200"),
            index="small_embeddings"
        )
        
        # Build the pipeline exactly as in your IndexingPipelineSuperComponent
        self.pipeline = self._build_indexing_pipeline(document_store)
        log.info("Indexing pipeline setup complete")
    
    def _build_indexing_pipeline(self, document_store):
        """Build the indexing pipeline with all components"""
        pipeline = Pipeline()
        
        # Core components
        file_router = FileTypeRouter(mime_types=["text/plain", "application/pdf", "text/html"])
        doc_joiner = DocumentJoiner(sort_by_score=False)
        pdf_converter = PyPDFToDocument()
        html_converter = HTMLToDocument()  # For URL content
        html_file_converter = HTMLToDocument()  # For HTML files
        link_fetcher = LinkContentFetcher()
        cleaner = DocumentCleaner(
            remove_empty_lines=True,
            remove_extra_whitespaces=True
        )
        splitter = DocumentSplitter(
            split_by='sentence',
            split_length=50,
            split_overlap=5
        )
        doc_embedder = OpenAIDocumentEmbedder(
            api_key=Secret.from_env_var("OPENAI_API_KEY"),
            model="text-embedding-3-small"
        )
        writer = DocumentWriter(
            document_store=document_store,
            policy=DuplicatePolicy.OVERWRITE
        )
        
        # Add components
        pipeline.add_component("link_fetcher", link_fetcher)
        pipeline.add_component("html_converter", html_converter)
        pipeline.add_component("html_file_converter", html_file_converter)
        pipeline.add_component("file_type_router", file_router)
        pipeline.add_component("pdf_converter", pdf_converter)
        pipeline.add_component("doc_joiner", doc_joiner)
        pipeline.add_component("cleaner", cleaner)
        pipeline.add_component("doc_splitter", splitter)
        pipeline.add_component("doc_embedder", doc_embedder)
        pipeline.add_component("writer", writer)
        
        # Connect components
        # URL content branch
        pipeline.connect("link_fetcher.streams", "html_converter.sources")
        pipeline.connect("html_converter.documents", "doc_joiner.documents")
        
        # File type routing branches
        pipeline.connect("file_type_router.application/pdf", "pdf_converter.sources")
        pipeline.connect("pdf_converter.documents", "doc_joiner.documents")
        
        # HTML files from file router go to separate HTML converter
        pipeline.connect("file_type_router.text/html", "html_file_converter.sources")
        pipeline.connect("html_file_converter.documents", "doc_joiner.documents")
        
        # Main processing path
        pipeline.connect("doc_joiner", "cleaner")
        pipeline.connect("cleaner", "doc_splitter")
        pipeline.connect("doc_splitter", "doc_embedder")
        pipeline.connect("doc_embedder", "writer")
        
        return pipeline
    
    def run_api(self, urls: Optional[List[str]] = None, files: Optional[List[UploadFile]] = None) -> dict:
        """
        Index documents from URLs and/or uploaded files.
        
        Args:
            urls: List of URLs to fetch and index
            files: List of uploaded files to index
            
        Returns:
            Dictionary with indexing results
        """
        log.info(f"Starting indexing - URLs: {len(urls) if urls else 0}, Files: {len(files) if files else 0}")
        
        results = {}
        total_indexed = 0
        
        # Convert UploadFile objects to ByteStream for file processing
        file_sources = []
        if files:
            file_sources = []
        if files:
            for file in files:
                # Determine MIME type from filename
                mime_type, _ = mimetypes.guess_type(file.filename)
                if not mime_type and file.filename and file.filename.lower().endswith('.pdf'):
                    mime_type = "application/pdf"
                elif not mime_type and file.filename and file.filename.lower().endswith(('.txt', '.text')):
                    mime_type = "text/plain"
                elif not mime_type and file.filename and file.filename.lower().endswith(('.html', '.htm')):
                    mime_type = "text/html"
                    
                file_sources.append(ByteStream(
                    data=file.file.read(), 
                    meta={"file_path": file.filename},
                    mime_type=mime_type
                ))
        
        pipeline_inputs = {}
        
        # Add URLs for link fetcher if provided
        if urls:
            pipeline_inputs["link_fetcher"] = {"urls": urls}
            
        # Add file sources for file router if provided  
        if file_sources:
            pipeline_inputs["file_type_router"] = {"sources": file_sources}

        log.info(f"Running pipeline with inputs: {list(pipeline_inputs.keys())}")
        
        try:
            result = self.pipeline.run(pipeline_inputs)
            
            # Extract meaningful results from the pipeline execution
            documents_written = result.get("writer", {}).get("documents_written", 0)
            
            results = {
                "status": "success",
                "documents_processed": documents_written,
                "urls_processed": len(urls) if urls else 0,
                "files_processed": len(files) if files else 0,
                "pipeline_result": {
                    "writer": result.get("writer", {}),
                    "doc_embedder": result.get("doc_embedder", {}).get("meta", {}) if result.get("doc_embedder") else {}
                }
            }
            
            log.info(f"Indexing completed successfully - {documents_written} documents written")
            return results
            
        except Exception as e:
            log.error(f"Pipeline execution failed: {str(e)}")
            results = {
                "status": "error",
                "error": str(e),
                "documents_processed": 0,
                "urls_processed": len(urls) if urls else 0,
                "files_processed": len(files) if files else 0
            }
            return results