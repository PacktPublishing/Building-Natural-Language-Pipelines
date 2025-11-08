"""
Custom components for Pipeline 4: Flexible Business Summarizer

This module contains reusable custom components that can be imported
by both the pipeline builder script and the Hayhooks wrapper.
"""

from haystack import component, Document
from haystack.components.builders import PromptBuilder
from haystack.components.generators import OpenAIGenerator
from haystack.utils import Secret
from typing import List, Dict, Any
import logging
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

import os 
# Prompt template for comprehensive business report generation
BUSINESS_REPORT_TEMPLATE = """
You are an expert business analyst creating comprehensive business reports.

Business Information:
- Name: {{ business_name }}
- Business ID: {{ business_id }}
{% if rating %}- Rating: {{ rating }}/5 ({{ review_count }} reviews){% endif %}
{% if categories %}- Categories: {{ categories }}{% endif %}
{% if price_range %}- Price Range: {{ price_range }}{% endif %}
{% if phone %}- Phone: {{ phone }}{% endif %}
{% if website %}- Website: {{ website }}{% endif %}
{% if location %}- Location: Latitude {{ location.lat }}, Longitude {{ location.lon }}{% endif %}

{% if website_content %}
Website Content Summary:
{{ website_content[:1000] }}
{% endif %}

{% if review_analysis %}
Review Analysis:
- Total Reviews Analyzed: {{ review_analysis.total_reviews }}
- Sentiment Distribution:
  * Positive: {{ review_analysis.positive_count }} ({{ (review_analysis.positive_count / review_analysis.total_reviews * 100) | round(1) }}%)
  * Neutral: {{ review_analysis.neutral_count }} ({{ (review_analysis.neutral_count / review_analysis.total_reviews * 100) | round(1) }}%)
  * Negative: {{ review_analysis.negative_count }} ({{ (review_analysis.negative_count / review_analysis.total_reviews * 100) | round(1) }}%)

Top Positive Reviews:
{% for review in review_analysis.highest_rated_reviews %}
- Rating: {{ review.rating }}/5 | User: {{ review.user }}
  "{{ review.text[:200] }}..."
{% endfor %}

{% if review_analysis.lowest_rated_reviews %}
Notable Negative Reviews:
{% for review in review_analysis.lowest_rated_reviews %}
- Rating: {{ review.rating }}/5 | User: {{ review.user }}
  "{{ review.text[:200] }}..."
{% endfor %}
{% endif %}
{% endif %}

Task: Create a comprehensive business report with the following sections:

1. **BUSINESS OVERVIEW**
   - Provide a clear summary of the business (2-3 sentences)
   - Include location context, pricing level, and type of establishment

{% if website_content %}
2. **OFFERINGS & SERVICES**
   - Summarize what the business offers based on their website content
   - Highlight key products, services, or unique features (3-5 bullet points)
{% endif %}

{% if review_analysis %}
3. **CUSTOMER FEEDBACK HIGHLIGHTS**
   
   **What Customers Love (Positive Highlights):**
   - Extract and summarize the main positive themes (3-5 bullet points)
   - Focus on specific aspects customers appreciate
   
   **Areas of Concern (Negative Highlights):**
   - Extract and summarize any recurring negative themes (2-3 bullet points)
   - Be balanced and factual
   
   **Overall Sentiment:**
   - Provide a one-sentence summary of overall customer satisfaction
{% endif %}

4. **RECOMMENDATION SUMMARY**
   - Brief recommendation on who would enjoy this business most
   - Any important considerations for potential customers

Format the report professionally and concisely. Use the exact section headers shown above.
"""


@component
class FlexibleInputParser:
    """
    Parses outputs from Pipeline 1, 2, and/or 3 to extract business information.
    
    This component:
    1. Accepts optional outputs from any combination of pipelines
    2. Extracts business data from each available source
    3. Consolidates information by business ID
    4. Determines information depth level (1, 2, or 3)
    
    Input:
        - pipeline1_output (Dict, optional): Output from Pipeline 1 (Yelp search)
        - pipeline2_output (Dict, optional): Output from Pipeline 2 (website details)
        - pipeline3_output (Dict, optional): Output from Pipeline 3 (reviews)
    
    Output:
        - business_data (List[Dict]): Consolidated business information
        - depth_level (int): Information depth (1=basic, 2=detailed, 3=with reviews)
    """
    
    def __init__(self):
        """Initialize the component with a logger."""
        self.logger = logging.getLogger(__name__ + ".FlexibleInputParser")
    
    @component.output_types(business_data=List[Dict], depth_level=int)
    def run(
        self, 
        pipeline1_output: Dict = None,
        pipeline2_output: Dict = None,
        pipeline3_output: Dict = None
    ) -> Dict[str, Any]:
        """
        Parse and consolidate outputs from available pipelines.
        
        Args:
            pipeline1_output: Yelp search results with basic business info
            pipeline2_output: Website content and enriched metadata
            pipeline3_output: Review aggregations with sentiment analysis
            
        Returns:
            Dictionary with consolidated business_data and depth_level
        """
        business_map = {}
        
        # Determine depth level based on available inputs
        depth_level = 0
        if pipeline1_output:
            depth_level = 1
        if pipeline2_output:
            depth_level = 2
        if pipeline3_output:
            depth_level = 3
        
        self.logger.info(f"Processing pipeline outputs at depth level {depth_level}")
        
        # Parse Pipeline 1 output (basic business info)
        if pipeline1_output:
            try:
                results = pipeline1_output.get('yelp_search', {}).get('results', {}).get('results', [])
                for business in results:
                    biz_id = business.get('bizId')
                    if biz_id:
                        business_map[biz_id] = {
                            'business_id': biz_id,
                            'name': business.get('name'),
                            'alias': business.get('alias'),
                            'rating': business.get('rating'),
                            'review_count': business.get('reviewCount'),
                            'categories': business.get('categories', []),
                            'price_range': business.get('priceRange'),
                            'phone': business.get('phone'),
                            'website': business.get('website'),
                            'location': {
                                'lat': business.get('lat'),
                                'lon': business.get('lon')
                            },
                            'images': business.get('images', [])
                        }
                self.logger.info(f"Parsed {len(results)} businesses from Pipeline 1")
            except Exception as e:
                self.logger.error(f"Error parsing Pipeline 1 output: {e}")
        
        # Parse Pipeline 2 output (website details)
        if pipeline2_output:
            try:
                documents = pipeline2_output.get('metadata_enricher', {}).get('documents', [])
                for doc in documents:
                    biz_id = doc.meta.get('business_id')
                    if biz_id:
                        if biz_id not in business_map:
                            # Initialize from Pipeline 2 if Pipeline 1 wasn't run
                            business_map[biz_id] = {
                                'business_id': biz_id,
                                'name': doc.meta.get('business_name'),
                                'alias': doc.meta.get('business_alias'),
                                'rating': doc.meta.get('rating'),
                                'review_count': doc.meta.get('review_count'),
                                'categories': doc.meta.get('categories', []),
                                'price_range': doc.meta.get('price_range'),
                                'phone': doc.meta.get('phone'),
                                'website': doc.meta.get('website'),
                                'location': {
                                    'lat': doc.meta.get('latitude'),
                                    'lon': doc.meta.get('longitude')
                                },
                                'images': doc.meta.get('images', [])
                            }
                        
                        # Add website content
                        business_map[biz_id]['website_content'] = doc.content
                        business_map[biz_id]['website_url'] = doc.meta.get('url')
                self.logger.info(f"Parsed {len(documents)} website documents from Pipeline 2")
            except Exception as e:
                self.logger.error(f"Error parsing Pipeline 2 output: {e}")
        
        # Parse Pipeline 3 output (review analysis)
        if pipeline3_output:
            try:
                documents = pipeline3_output.get('reviews_aggregator', {}).get('documents', [])
                for doc in documents:
                    biz_id = doc.meta.get('business_id')
                    if biz_id:
                        if biz_id not in business_map:
                            # Initialize minimal data if only Pipeline 3 was run
                            business_map[biz_id] = {'business_id': biz_id}
                        
                        # Add review analysis
                        business_map[biz_id]['review_analysis'] = {
                            'total_reviews': doc.meta.get('total_reviews', 0),
                            'positive_count': doc.meta.get('positive_count', 0),
                            'neutral_count': doc.meta.get('neutral_count', 0),
                            'negative_count': doc.meta.get('negative_count', 0),
                            'highest_rated_reviews': doc.meta.get('highest_rated_reviews', []),
                            'lowest_rated_reviews': doc.meta.get('lowest_rated_reviews', [])
                        }
                self.logger.info(f"Parsed {len(documents)} review documents from Pipeline 3")
            except Exception as e:
                self.logger.error(f"Error parsing Pipeline 3 output: {e}")
        
        # Convert to list
        business_data = list(business_map.values())
        
        self.logger.info(f"✓ Parsed {len(business_data)} business(es) at depth level {depth_level}")
        
        return {
            "business_data": business_data,
            "depth_level": depth_level
        }


@component
class BusinessReportGenerator:
    """
    Generates comprehensive business reports using an LLM.
    
    This component:
    1. Takes consolidated business data from FlexibleInputParser
    2. Constructs prompts with all available information
    3. Generates structured, professional business reports
    4. Returns documents containing formatted reports
    
    Input:
        - business_data (List[Dict]): Consolidated business information
        - depth_level (int): Information depth (1, 2, or 3)
    
    Output:
        - documents (List[Document]): Business report documents
    """
    
    def __init__(self):
        """
        Initialize the business report generator.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.logger = logging.getLogger(__name__ + ".BusinessReportGenerator")
        self.prompt_builder = PromptBuilder(template=BUSINESS_REPORT_TEMPLATE)
        self.generator = OpenAIGenerator(
            api_key=Secret.from_env_var("OPENAI_API_KEY"),
            model="gpt-4o-mini",
            generation_kwargs={"temperature": 0.7, "max_tokens": 1500}
        )
    
    @component.output_types(documents=List[Document])
    def run(self, business_data: List[Dict], depth_level: int) -> Dict[str, List[Document]]:
        """
        Generate business reports for each business.
        
        Args:
            business_data: Consolidated business information
            depth_level: Information depth level (1, 2, or 3)
            
        Returns:
            Dictionary with documents containing business reports
        """
        report_documents = []
        
        self.logger.info(f"Generating reports for {len(business_data)} businesses at depth level {depth_level}")
        
        for data in business_data:
            try:
                # Prepare data for prompt
                prompt_data = {
                    'business_id': data.get('business_id'),
                    'business_name': data.get('name', 'Unknown Business'),
                    'rating': data.get('rating'),
                    'review_count': data.get('review_count'),
                    'categories': ', '.join(data.get('categories', [])) if isinstance(data.get('categories'), list) else data.get('categories'),
                    'price_range': data.get('price_range'),
                    'phone': data.get('phone'),
                    'website': data.get('website'),
                    'location': data.get('location')
                }
                
                # Add website content if available (depth level 2+)
                if depth_level >= 2 and 'website_content' in data:
                    prompt_data['website_content'] = data['website_content']
                
                # Add review analysis if available (depth level 3)
                if depth_level >= 3 and 'review_analysis' in data:
                    prompt_data['review_analysis'] = data['review_analysis']
                
                # Build prompt
                prompt_result = self.prompt_builder.run(**prompt_data)
                
                # Generate report
                llm_result = self.generator.run(prompt=prompt_result['prompt'])
                
                report_content = llm_result['replies'][0] if llm_result['replies'] else "Report generation failed"
                
                # Create document with report
                doc = Document(
                    content=report_content,
                    meta={
                        'business_id': data.get('business_id'),
                        'business_name': data.get('name'),
                        'depth_level': depth_level,
                        'rating': data.get('rating'),
                        'price_range': data.get('price_range'),
                        'website': data.get('website'),
                        'phone': data.get('phone'),
                        'categories': data.get('categories'),
                        'has_website_summary': 'website_content' in data,
                        'has_review_analysis': 'review_analysis' in data
                    }
                )
                report_documents.append(doc)
                
                self.logger.info(f"Generated report for business: {data.get('name')}")
                
            except Exception as e:
                self.logger.error(f"Error generating report for business {data.get('business_id')}: {e}")
                # Create error document
                error_doc = Document(
                    content=f"Error generating report: {str(e)}",
                    meta={'business_id': data.get('business_id'), 'error': True}
                )
                report_documents.append(error_doc)
        
        self.logger.info(f"✓ Generated {len(report_documents)} business reports")
        
        return {"documents": report_documents}
