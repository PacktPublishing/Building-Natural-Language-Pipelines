# %%
from haystack import Pipeline
from haystack.components.preprocessors import DocumentCleaner
from haystack.components.websearch import SerperDevWebSearch
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.converters import HTMLToDocument
from haystack.components.writers import DocumentWriter
from haystack import Pipeline
from haystack.components.extractors import NamedEntityExtractor
from haystack import component, Document
from typing import Any, Dict, List, Union

from dotenv import load_dotenv
import os

load_dotenv(".env")
open_ai_key = os.getenv("OPENAI_API_KEY")
serper_api_key = os.getenv("SERPERDEV_API_KEY")


# %% [markdown]
# ### Define custom component

# %%
@component
class NERPopulator():
    """This function extracts named entities from a list of
    documents and returns the result in a structured format.

    Args:
        documents (list): List of Haystack Document objects

    Returns:
        extracted_data (list): A list of dictionaries containing the extracted entities, 
        to make it Haystack-compatible we will return this list as a dictionary with the key 'documents'
    """
    
    @component.output_types(documents=List[Document])
    def run(self, sources: List[Document]) -> None:
        extracted_data = []

        for document in sources:
            content = document.content
            doc_id = document.id
            named_entities = document.meta.get('named_entities', [])
            url = document.meta.get('url', 'N/A')  # Default to 'N/A' if URL is not available

            # Sets to store unique entities by type
            entities_by_type = {
                "LOC": set(),
                "PER": set(),
                "ORG": set(),
                "MISC": set()
            }
            
            # Loop through the entities and filter by score and type
            for entity in named_entities:
                if float(entity.score) < 0.8:
                    continue
                
                word = content[entity.start:entity.end]
                if entity.entity in entities_by_type:
                    entities_by_type[entity.entity].add(word)  # Use set to ensure uniqueness
            
            # Prepare the meta field with comma-separated values
            meta = {
                "LOC": ",".join(entities_by_type["LOC"]),
                "PER": ",".join(entities_by_type["PER"]),
                "ORG": ",".join(entities_by_type["ORG"]),
                "MISC": ",".join(entities_by_type["MISC"]),
                "url": url
            }
            
            # Append the result for this document
            extracted_data.append({
                'document_id': doc_id,
                'content': content,
                'meta': meta
            })
        

        return {"documents": extracted_data}


# %% [markdown]
# ### Build Haystack pipeline with custom component

# %%

# Initialize pipeline
pipeline = Pipeline()
web_search = SerperDevWebSearch(top_k=5,
                                allowed_domains=["https://www.britannica.com/"])
link_content = LinkContentFetcher(retry_attempts=3,
                                  timeout=10)
html_to_doc = HTMLToDocument()
document_cleaner = DocumentCleaner(
                                remove_empty_lines=True,
                                remove_extra_whitespaces=True,
                                remove_repeated_substrings=False,
                                remove_substrings=['\n-']
                            )
extractor = NamedEntityExtractor(backend="hugging_face", model="dslim/bert-base-NER")
extractor.warm_up()

ner_component = NERPopulator()

# Add components
pipeline.add_component(name='search', instance=web_search)
pipeline.add_component(name ='fetcher' , instance= link_content)
pipeline.add_component(name='htmldocument', instance=html_to_doc)
pipeline.add_component(name='cleaner', instance=document_cleaner)
pipeline.add_component(name='extractor', instance=extractor)
pipeline.add_component(name='ner', instance=ner_component)

# Connect components to one another
pipeline.connect("search.links", "fetcher.urls")
pipeline.connect("fetcher", "htmldocument")
pipeline.connect("htmldocument", "cleaner")
pipeline.connect("cleaner", "extractor")
pipeline.connect("extractor", "ner")


# %% [markdown]
# ### Use pipeline to search Encyclopedia Britannica for all articles related to Elon Musk and extract entities

# %%
query = "Elon Musk"
output = pipeline.run(data={"search":{"query":query}})

# %%
extracted_documents = output['ner']['documents']

# %%
extracted_documents

# %%



