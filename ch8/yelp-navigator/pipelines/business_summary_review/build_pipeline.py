"""
Pipeline 4: Flexible Business Summarizer

This script creates a Haystack pipeline that generates comprehensive business 
reports from outputs of Pipeline 1, 2, and/or 3, adapting to the available data.

Usage:
    python build_pipeline.py

Output:
    - pipeline4_summary_recommendations.yaml (serialized pipeline)
"""

from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from haystack import Pipeline
from haystack.utils import Secret
# Add parent directory to path for imports when running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import custom components from the components module
try:
    from .components import (
        FlexibleInputParser,
        BusinessReportGenerator
    )
except ImportError:
    # Fallback for when run as a script
    from pipelines.business_summary_review.components import (
        FlexibleInputParser,
        BusinessReportGenerator
    )

# Load environment variables
load_dotenv(".env")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def build_pipeline():
    """Build and return the Pipeline 4 instance."""
    # Initialize pipeline
    pipeline = Pipeline()
    
    # Initialize components
    input_parser = FlexibleInputParser()
    report_generator = BusinessReportGenerator()
    
    # Add components to pipeline
    pipeline.add_component("input_parser", input_parser)
    pipeline.add_component("report_generator", report_generator)
    
    # Connect components
    pipeline.connect("input_parser.business_data", "report_generator.business_data")
    pipeline.connect("input_parser.depth_level", "report_generator.depth_level")
    
    print("✓ Pipeline built successfully")
    print("\nPipeline structure:")
    print("Pipeline Outputs (1/2/3) → FlexibleInputParser → BusinessReportGenerator → Business Reports")
    
    return pipeline


if __name__ == "__main__":
    # Build the pipeline
    pipeline = build_pipeline()
    
    # draw pipeline
    pipeline.draw(path = f"pipeline4_summary_recommendations.png")
    
    # Serialize the pipeline to YAML
    output_path = "pipeline4_summary_recommendations.yaml"
    with open(output_path, "w") as file:
        pipeline.dump(file)
        
    print(f"\n✓ Pipeline serialized to: {output_path}")
    print("\nThe pipeline is now ready to be deployed with Hayhooks!")
