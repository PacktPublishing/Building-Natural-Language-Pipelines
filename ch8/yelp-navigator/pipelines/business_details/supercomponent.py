# Add parent directory to path for imports when running as script
from pathlib import Path
import sys


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import custom components from the components module
try:

    from .build_pipeline import build_pipeline
except ImportError:

    from pipelines.business_details.build_pipeline import build_pipeline
    
    

