from typing import List, Optional
from pathlib import Path
import os
from fastapi import UploadFile
from haystack.dataclasses import ByteStream
import mimetypes

from hayhooks import BasePipelineWrapper, log

from haystack import Pipeline


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        """Initialize the indexing pipeline"""
        log.info("Setting up indexing pipeline...")
        
        pipeline_yaml = (Path(__file__).parent / "indexing.yml").read_text()
        self.pipeline = Pipeline.loads(pipeline_yaml)
        log.info("Indexing pipeline setup complete")
    
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