"""
Pipeline Wrapper Script - SuperComponents and Tools

This script demonstrates how to:
1. Wrap Haystack pipelines as SuperComponents with simplified interfaces
2. Convert SuperComponents into ComponentTools for use by AI agents
3. Build an intelligent agent that can use multiple tools

SuperComponents simplify complex pipelines by:
- Mapping multiple internal inputs to a single external parameter
- Exposing only relevant outputs
- Providing a cleaner interface for end users

ComponentTools enable agents to:
- Choose the appropriate tool based on user queries
- Execute pipelines with natural language inputs
- Synthesize results into coherent responses

TODO: Complete the wrapper functions following the instructions.
"""

from haystack import SuperComponent
from haystack.tools.component_tool import ComponentTool
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage
from haystack.utils import Secret

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv(".env")


from typing import List, Dict, Any
import os
import sys
from pathlib import Path

from hayhooks import BasePipelineWrapper, log
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
        pipeline_yaml = (Path(__file__).parent / "<your-serialized-file>.yaml").read_text()
        self.pipeline = Pipeline.loads(pipeline_yaml)
        
        log.info("Pipeline setup complete")
    
    def run_api(self, pipeline_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create document store from Pipeline 1 business results with website content.
        
        This API endpoint:
        1. Accepts the complete Pipeline output

        Args:
            pipeline_output: Complete output dictionary from Pipeline

        Returns:
            Dictionary with enriched documents and metadata
        """
        log.info("Processing Pipeline output for document store creation")

        try:
            # Run the pipeline with Pipeline output
            pipeline_inputs = {
                "parser": {"pipeline_output": pipeline_input}
            }
        except Exception as e:
            log.error(f"Error running pipeline: {e}")
            raise e