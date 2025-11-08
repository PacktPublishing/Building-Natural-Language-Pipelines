"""
Pipeline 4 Wrapper for Hayhooks

This wrapper loads the serialized Pipeline 4 (Flexible Business Summarizer) 
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

# Import custom components from the components module
try:
    from .components import (
        FlexibleInputParser,
        BusinessReportGenerator
    )
except ImportError:
    # Fallback for when loaded by hayhooks
    from pipelines.business_summary_review.components import (
        FlexibleInputParser,
        BusinessReportGenerator
    )


class PipelineWrapper(BasePipelineWrapper):
    def setup(self) -> None:
        """Initialize Pipeline 4: Flexible Business Summarizer"""
        log.info("Setting up Pipeline 4: Flexible Business Summarizer...")
        
        # Load the serialized pipeline
        pipeline_yaml = (Path(__file__).parent / "pipeline4_summary_recommendations.yaml").read_text()
        self.pipeline = Pipeline.loads(pipeline_yaml)
        
        log.info("Pipeline 4 setup complete")
    
    def run_api(
        self, 
        pipeline1_output: Dict = None,
        pipeline2_output: Dict = None,
        pipeline3_output: Dict = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive business reports from pipeline outputs.
        
        This API endpoint:
        1. Accepts outputs from Pipeline 1, 2, and/or 3 (any combination)
        2. Consolidates business information from available sources
        3. Generates comprehensive reports with appropriate depth:
           - Level 1: Basic business info (Pipeline 1 only)
           - Level 2: With website details (Pipelines 1+2)
           - Level 3: Complete with reviews (All pipelines)
        4. Returns formatted business reports
        
        Args:
            pipeline1_output: Optional output from Pipeline 1 (business search)
            pipeline2_output: Optional output from Pipeline 2 (website details)
            pipeline3_output: Optional output from Pipeline 3 (review analysis)
            
        Returns:
            Dictionary with business reports and metadata
        """
        log.info("Processing business summarization request")
        
        # Determine which pipelines were provided
        provided_pipelines = []
        if pipeline1_output:
            provided_pipelines.append("Pipeline 1 (Search)")
        if pipeline2_output:
            provided_pipelines.append("Pipeline 2 (Website)")
        if pipeline3_output:
            provided_pipelines.append("Pipeline 3 (Reviews)")
        
        log.info(f"Available pipeline outputs: {', '.join(provided_pipelines) if provided_pipelines else 'None'}")
        
        try:
            # Run the pipeline with provided inputs
            pipeline_inputs = {
                "input_parser": {
                    "pipeline1_output": pipeline1_output,
                    "pipeline2_output": pipeline2_output,
                    "pipeline3_output": pipeline3_output
                }
            }
            
            log.info("Running Pipeline 4...")
            result = self.pipeline.run(
                pipeline_inputs,
                include_outputs_from={"input_parser", "report_generator"}
            )
            
            # Extract results
            parser_output = result.get("input_parser", {})
            depth_level = parser_output.get("depth_level", 0)
            
            report_output = result.get("report_generator", {})
            documents = report_output.get("documents", [])
            
            # Format the response
            reports = []
            for doc in documents:
                report = {
                    "business_id": doc.meta.get("business_id"),
                    "business_name": doc.meta.get("business_name"),
                    "report": doc.content,
                    "metadata": {
                        "depth_level": doc.meta.get("depth_level"),
                        "rating": doc.meta.get("rating"),
                        "price_range": doc.meta.get("price_range"),
                        "website": doc.meta.get("website"),
                        "phone": doc.meta.get("phone"),
                        "categories": doc.meta.get("categories"),
                        "has_website_summary": doc.meta.get("has_website_summary", False),
                        "has_review_analysis": doc.meta.get("has_review_analysis", False),
                        "error": doc.meta.get("error", False)
                    }
                }
                reports.append(report)
            
            response = {
                "depth_level": depth_level,
                "depth_description": self._get_depth_description(depth_level),
                "report_count": len(reports),
                "reports": reports
            }
            
            log.info(f"Generated {len(reports)} business report(s) at depth level {depth_level}")
            return response
            
        except Exception as e:
            log.error(f"Error generating reports: {str(e)}")
            return {
                "error": str(e),
                "depth_level": 0,
                "report_count": 0,
                "reports": []
            }
    
    def _get_depth_description(self, depth_level: int) -> str:
        """Get a human-readable description of the depth level."""
        descriptions = {
            0: "No data provided",
            1: "Basic business information only",
            2: "Business information with website details",
            3: "Complete analysis with business info, website, and reviews"
        }
        return descriptions.get(depth_level, "Unknown depth level")
    
    def run_chat_completion(self, model: str, messages: list, body: dict) -> str:
        """
        OpenAI-compatible chat completion endpoint.
        
        This allows the pipeline to be used in chat interfaces by converting
        the business reports into a natural language response.
        
        Note: For chat completion, the pipeline outputs should be provided 
        in the body under 'pipeline_outputs' key.
        """
        # Extract pipeline outputs from body if provided
        pipeline_outputs = body.get("pipeline_outputs", {})
        pipeline1_output = pipeline_outputs.get("pipeline1")
        pipeline2_output = pipeline_outputs.get("pipeline2")
        pipeline3_output = pipeline_outputs.get("pipeline3")
        
        if not any([pipeline1_output, pipeline2_output, pipeline3_output]):
            return "No pipeline outputs provided. Please include pipeline outputs in the request body under 'pipeline_outputs' key."
        
        # Run the pipeline
        result = self.run_api(
            pipeline1_output=pipeline1_output,
            pipeline2_output=pipeline2_output,
            pipeline3_output=pipeline3_output
        )
        
        # Format as natural language response
        if result.get("error"):
            return f"I encountered an error generating business reports: {result['error']}"
        
        report_count = result.get("report_count", 0)
        depth_level = result.get("depth_level", 0)
        depth_description = result.get("depth_description", "")
        reports = result.get("reports", [])
        
        if report_count == 0:
            return "I couldn't generate any business reports from the provided data."
        
        # Create a natural language response
        response_lines = [
            f"I've generated {report_count} comprehensive business report(s) ({depth_description}):",
            ""
        ]
        
        for i, report_data in enumerate(reports, 1):
            if report_data["metadata"].get("error"):
                response_lines.append(f"{i}. **Error**: {report_data['report']}")
                response_lines.append("")
                continue
            
            response_lines.append(f"{'=' * 80}")
            response_lines.append(f"**BUSINESS REPORT {i}: {report_data['business_name']}**")
            response_lines.append(f"{'=' * 80}")
            response_lines.append("")
            response_lines.append(report_data['report'])
            response_lines.append("")
        
        return "\n".join(response_lines)
