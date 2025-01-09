from haystack import Pipeline, Document
from haystack_integrations.document_stores.elasticsearch import ElasticsearchDocumentStore
from haystack.components.writers import DocumentWriter
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
import pandas as pd
from haystack.components.preprocessors import DocumentCleaner
from haystack.document_stores.types import DuplicatePolicy
import os 

def preprocess_documents(df_file_path: str):
    # Check if file exists
    if not os.path.exists(df_file_path):
        print(f"Error: The file '{df_file_path}' does not exist.")
        return []  # Gracefully exit with an empty list

    try:
        df = pd.read_csv(df_file_path)
    except Exception as e:
        print(f"Error reading the file '{df_file_path}': {e}")
        return []  # Gracefully exit with an empty list if reading fails

    # Check if 'Text' column exists
    if 'Text' not in df.columns:
        print(f"Error: The file '{df_file_path}' does not contain a 'Text' column.")
        return []

    list_of_news = df['Text'].to_list()
    documents = [Document(id=str(i), content=list_of_news[i]) for i in range(len(list_of_news))]

    return documents

class IndexingPipeline:
    def __init__(self):
        """Initialize Indexing pipeline"""
        # Initialize document store
        document_store = ElasticsearchDocumentStore(hosts = "http://localhost:9200",
                                            embedding_similarity_function='cosine')
        # Initialize components
        embedder = SentenceTransformersDocumentEmbedder(model="sentence-transformers/all-MiniLM-L6-v2")
        document_cleaner = DocumentCleaner(
                                        remove_empty_lines=True,
                                        remove_extra_whitespaces=True,
                                        remove_repeated_substrings=True,
                                        remove_substrings=['\n']
                                    )
        document_writer = DocumentWriter(document_store=document_store,
                                        policy=DuplicatePolicy.OVERWRITE )

        # Initialize pipeline
        self.indexing_pipeline = Pipeline()
        # Add components
        self.indexing_pipeline.add_component(instance=embedder, name="doc_embedder")
        self.indexing_pipeline.add_component(instance=document_cleaner, name='doc_cleaner')
        self.indexing_pipeline.add_component(instance=document_writer, name="doc_writer")
        # Connect components
        self.indexing_pipeline.connect("doc_cleaner.documents", "doc_embedder.documents")
        self.indexing_pipeline.connect("doc_embedder.documents", "doc_writer.documents")

    def run(self, documents):
        """Execute indexing pipeline on a list of documents"""
        self.indexing_pipeline.run({"doc_cleaner": {"documents": documents}})


if __name__=="__main__":
    documents = preprocess_documents("df_file.csv")
    indexing_pipeline = IndexingPipeline()
    indexing_pipeline.run(documents)