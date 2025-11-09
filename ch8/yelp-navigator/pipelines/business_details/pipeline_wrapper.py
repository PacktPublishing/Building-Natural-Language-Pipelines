"""
Pipeline 2 Wrapper for Hayhooks

This wrapper loads the serialized Pipeline 2 (Business Details with Website Content)
and provides API endpoints for use with Hayhooks.
"""

from typing import List, Dict, Any
import os
import sys
from pathlib import Path

from hayhooks import BasePipelineWrapper, log, get_last_user_message
from haystack import Pipeline

# Add parent directory to path for imports
current_dir = Path(__file__).parent
if str(current_dir.parent.parent) not in sys.path:
    sys.path.insert(0, str(current_dir.parent.parent))



class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        """Initialize Pipeline 2: Business Details with Website Content"""
        log.info("Setting up Pipeline 2: Business Details with Website Content...")
        
        # Load the serialized pipeline
        pipeline_yaml = (Path(__file__).parent / "pipeline2_business_details.yaml").read_text()
        self.pipeline = Pipeline.loads(pipeline_yaml)
        
        log.info("Pipeline 2 setup complete")
    
    def run_api(self, pipeline1_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create document store from Pipeline 1 business results with website content.
        
        This API endpoint:
        1. Accepts the complete Pipeline 1 output
        2. Extracts website URLs from business results
        3. Fetches and converts website content to documents
        4. Enriches documents with business metadata
        5. Returns enriched documents for document store
        
        Args:
            pipeline1_output: Complete output dictionary from Pipeline 1
            
        Returns:
            Dictionary with enriched documents and metadata
        """
        log.info("Processing Pipeline 1 output for document store creation")
        
        try:
            # Run the pipeline with Pipeline 1 output
            pipeline_inputs = {
                "parser": {"pipeline1_output": pipeline1_output}
            }
            
            log.info("Running Pipeline 2...")
            result = self.pipeline.run(
                pipeline_inputs,
                include_outputs_from={"parser", "url_extractor", "metadata_enricher"}
            )
            
            # Extract results
            parser_output = result.get("parser", {})
            url_extractor_output = result.get("url_extractor", {})
            enricher_output = result.get("metadata_enricher", {})
            
            documents = enricher_output.get("documents", [])
            business_results = parser_output.get("business_results", [])
            
            # Format the response
            response = {
                "document_count": len(documents),
                "business_count": len(business_results),
                "urls_fetched": url_extractor_output.get("urls", []),
                "documents": [
                    {
                        "content_length": len(doc.content),
                        "content_preview": doc.content[:500] if doc.content else "",
                        "metadata": {
                            "business_id": doc.meta.get("business_id"),
                            "business_name": doc.meta.get("business_name"),
                            "business_alias": doc.meta.get("business_alias"),
                            "rating": doc.meta.get("rating"),
                            "review_count": doc.meta.get("review_count"),
                            "price_range": doc.meta.get("price_range"),
                            "categories": doc.meta.get("categories", []),
                            "phone": doc.meta.get("phone"),
                            "website": doc.meta.get("website"),
                            "location": {
                                "lat": doc.meta.get("latitude"),
                                "lon": doc.meta.get("longitude")
                            },
                            "services": doc.meta.get("services", []),
                            "business_highlights": doc.meta.get("business_highlights", []),
                            "images": doc.meta.get("images", [])
                        }
                    }
                    for doc in documents
                ],
                "raw_documents": documents  # Include full Document objects for downstream use
            }
            
            log.info(f"Pipeline 2 processed successfully - {len(documents)} documents created")
            return response
            
        except Exception as e:
            log.error(f"Error processing Pipeline 1 output: {str(e)}")
            return {
                "error": str(e),
                "document_count": 0,
                "documents": []
            }
    
    def run_chat_completion(self, model: str, messages: list, body: dict) -> str:
        """
        OpenAI-compatible chat completion endpoint.
        
        This allows the pipeline to be used in chat interfaces by converting
        the document store creation results into a natural language response.
        """
        # For Pipeline 2, this would typically receive Pipeline 1 output
        # Since chat completion expects messages, we'll return a helpful message
        question = get_last_user_message(messages)
        
        return (
            "Pipeline 2 creates enriched documents from Pipeline 1 business search results. "
            "To use this pipeline, pass the complete Pipeline 1 output to the run_api endpoint. "
            "This pipeline extracts website content and enriches documents with business metadata "
            "for use in a document store or RAG system."
        )


def extract_document_metadata(documents: List[Any]) -> List[Dict[str, Any]]:
    """
    Extract key metadata from enriched documents.
    
    Utility function for downstream processing.
    
    Args:
        documents: List of enriched Haystack Documents
    
    Returns:
        List of metadata dictionaries with key business information
    """
    metadata_list = []
    
    for doc in documents:
        metadata = {
            "business_id": doc.meta.get("business_id"),
            "business_name": doc.meta.get("business_name"),
            "business_alias": doc.meta.get("business_alias"),
            "price_range": doc.meta.get("price_range"),
            "rating": doc.meta.get("rating"),
            "review_count": doc.meta.get("review_count"),
            "latitude": doc.meta.get("latitude"),
            "longitude": doc.meta.get("longitude"),
            "phone": doc.meta.get("phone"),
            "categories": doc.meta.get("categories"),
            "website": doc.meta.get("website"),
            "has_website_content": len(doc.content) > 0
        }
        metadata_list.append(metadata)
    
    return metadata_list
