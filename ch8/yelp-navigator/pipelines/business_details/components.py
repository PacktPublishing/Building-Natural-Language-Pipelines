"""
Custom components for Pipeline 2: Business Details with Website Content

This module contains reusable custom components for creating a document store
from Pipeline 1 business search results, including website content extraction
and metadata enrichment.
"""

from haystack import component, Document
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@component
class Pipeline1ResultParser:
    """
    Parses the full Pipeline 1 output to extract business results.
    
    This component:
    1. Accepts the complete Pipeline 1 output dictionary
    2. Navigates the nested structure to find business results
    3. Returns the business results list for downstream processing
    
    Input:
        - pipeline1_output (Dict): Complete output from Pipeline 1
    
    Output:
        - business_results (List[Dict]): List of business dictionaries
    """
    
    def __init__(self):
        """Initialize the component with a logger."""
        self.logger = logging.getLogger(__name__ + ".Pipeline1ResultParser")
    
    @component.output_types(business_results=List[Dict])
    def run(self, pipeline1_output: Dict) -> Dict[str, List[Dict]]:
        """
        Parse Pipeline 1 output to extract business results.
        
        Args:
            pipeline1_output: Full output dictionary from Pipeline 1
                Expected structure: {'result': {'businesses': [...]}}
            
        Returns:
            Dictionary with business_results key containing list of businesses
        """
        self.logger.info("Parsing Pipeline 1 output")
        
        try:
            # Navigate the nested structure
            result = pipeline1_output.get('result', {})
            business_results = result.get('businesses', [])
            
            result_count = result.get('result_count', 0)
            extracted_location = result.get('extracted_location', '')
            extracted_keywords = result.get('extracted_keywords', [])
            
            self.logger.info(f"Extracted {len(business_results)} businesses from Pipeline 1")
            self.logger.debug(f"Result count: {result_count}, Location: {extracted_location}, Keywords: {extracted_keywords}")
            
            return {"business_results": business_results}
            
        except Exception as e:
            self.logger.error(f"Error parsing Pipeline 1 output: {e}", exc_info=True)
            return {"business_results": []}


@component
class WebsiteURLExtractor:
    """
    Extracts website URLs from business results.
    
    This component:
    1. Accepts business results list from Pipeline1ResultParser
    2. Extracts website URLs for each business with a website
    3. Prepares business metadata for document enrichment
    4. Returns URLs to fetch and corresponding metadata
    
    Input:
        - business_results (List[Dict]): Business data from parser
    
    Output:
        - urls (List[str]): Website URLs to fetch
        - business_metadata (List[Dict]): Associated business information
    """
    
    def __init__(self):
        """Initialize the component with a logger."""
        self.logger = logging.getLogger(__name__ + ".WebsiteURLExtractor")
    
    @component.output_types(
        urls=List[str],
        business_metadata=List[Dict]
    )
    def run(self, business_results: List[Dict]) -> Dict[str, Any]:
        """
        Extract website URLs and prepare metadata from business results.
        
        Args:
            business_results: List of business dictionaries
            
        Returns:
            Dictionary with urls and business_metadata
        """
        if not business_results:
            self.logger.warning("No business results provided")
            return {"urls": [], "business_metadata": []}
        
        self.logger.info(f"Processing {len(business_results)} business results")
        
        urls = []
        metadata_list = []
        
        for business in business_results:
            website = business.get('website')
            business_name = business.get('name', 'Unknown')
            
            if website and website.strip() and website != 'N/A' and website.lower() != 'none':
                urls.append(website)
                self.logger.info(f"Extracted website for '{business_name}': {website}")
                
                # Prepare metadata from Pipeline 1 data
                # Updated field names to match new Pipeline 1 structure
                location = business.get('location', {})
                meta = {
                    "business_id": business.get('business_id', ''),
                    "business_name": business_name,
                    "business_alias": business.get('alias', ''),
                    "price_range": business.get('price_range', 'N/A'),
                    "latitude": location.get('lat', 0.0),
                    "longitude": location.get('lon', 0.0),
                    "rating": business.get('rating', 0.0),
                    "review_count": business.get('review_count', 0),
                    "phone": business.get('phone', ''),
                    "categories": business.get('categories', []),
                    "website": website,
                    "images": business.get('images', [])
                }
                metadata_list.append(meta)
                self.logger.debug(f"Prepared metadata for '{business_name}'")
            else:
                self.logger.warning(f"No website found for business: '{business_name}'")
        
        self.logger.info(f"Successfully extracted {len(urls)} website URLs")
        
        return {
            "urls": urls,
            "business_metadata": metadata_list
        }


@component
class DocumentMetadataEnricher:
    """
    Enriches documents with business metadata.
    
    This component:
    1. Receives documents from HTMLToDocument converter
    2. Matches documents with corresponding business metadata
    3. Enriches document metadata with business information
    4. Returns fully enriched Haystack Documents
    
    Input:
        - documents (List[Document]): Documents from HTMLToDocument
        - business_metadata (List[Dict]): Business metadata from extractor
    
    Output:
        - documents (List[Document]): Enriched documents with full metadata
    """
    
    def __init__(self):
        """Initialize the component with a logger."""
        self.logger = logging.getLogger(__name__ + ".DocumentMetadataEnricher")
    
    @component.output_types(documents=List[Document])
    def run(self, documents: List[Document], business_metadata: List[Dict]) -> Dict[str, List[Document]]:
        """
        Enrich documents with business metadata.
        
        Args:
            documents: Documents containing website content
            business_metadata: Business information to add to documents
            
        Returns:
            Dictionary with enriched documents
        """
        # Handle None documents
        if documents is None:
            self.logger.warning("Received None for documents, using empty list")
            documents = []
        
        self.logger.info(f"Enriching {len(documents)} documents with business metadata")
        
        enriched_documents = []
        
        # Match documents with metadata by URL
        for i, doc in enumerate(documents):
            if i < len(business_metadata):
                # Get corresponding business metadata
                meta = business_metadata[i]
                business_name = meta.get('business_name', 'Unknown')
                
                self.logger.debug(f"Enriching document {i+1} for business: '{business_name}'")
                
                # Handle None content
                content = doc.content if doc.content is not None else ""
                
                # Create enriched document
                enriched_doc = Document(
                    content=content,
                    meta={
                        **doc.meta,  # Keep original metadata (URL, etc.)
                        **meta       # Add business metadata
                    }
                )
                enriched_documents.append(enriched_doc)
                
                content_length = len(content)
                self.logger.info(f"Successfully enriched document for '{business_name}' (content length: {content_length} chars)")
            else:
                # If no matching metadata, keep original document
                self.logger.warning(f"No metadata available for document {i+1}, keeping original")
                enriched_documents.append(doc)
        
        self.logger.info(f"Completed enrichment of {len(enriched_documents)} documents")
        
        return {"documents": enriched_documents}
