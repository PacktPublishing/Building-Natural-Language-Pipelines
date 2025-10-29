from pathlib import Path

# --- 1. Create Sample Data Files ---
# Create a directory to hold our source files
data_dir = Path("data_for_indexing")
data_dir.mkdir(exist_ok=True)

# Create a sample text file
text_file_path = data_dir / "haystack_intro.txt"
text_file_path.write_text(
    "Haystack is an open-source framework by deepset for building production-ready LLM applications. "
    "It enables developers to create retrieval-augmented generative pipelines and state-of-the-art search systems."
)

# Create a sample PDF file (requires PyPDF installation: pip install pypdf)
# For this example, we'll skip the actual PDF creation and assume one exists.
# You can place any PDF file in the 'data_for_indexing' directory and name it 'sample.pdf'.
# For a runnable example, we will simulate its path.
pdf_file_path = data_dir / "howpeopleuseai.pdf"
# In a real scenario, you would have this file. For this script to run, we'll check for it.
if not pdf_file_path.exists():
    print(f"Warning: PDF file not found at {pdf_file_path}. The PDF processing branch will not run.")
    # Create a dummy file to avoid path errors, but it won't be processed as PDF
    pdf_file_path.touch()


# Create a sample CSV file with some empty rows/columns for cleaning
csv_content = """Company,Model,Release Year,,Notes
OpenAI,GPT-4,2023,,Generative Pre-trained Transformer 4
,,,
Google,Gemini,2023,,A family of multimodal models
Anthropic,Claude 3,2024,,Includes Opus, Sonnet, and Haiku models
"""
csv_file_path = data_dir / "llm_models.csv"
csv_file_path.write_text(csv_content)

# Define a sample URL to fetch
web_url = "https://haystack.deepset.ai/blog/haystack-2-release"