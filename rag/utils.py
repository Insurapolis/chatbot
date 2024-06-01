import yaml
from typing import ChainMap
from langchain_community.embeddings import SentenceTransformerEmbeddings
from rag.constants import MODEL_NAME


MODEL_NAME_RETRIEVER = SentenceTransformerEmbeddings(model_name=MODEL_NAME)


def load_conf(*file_paths: list[str]) -> ChainMap:
    """Load configuration from a YAML file. Multiple configuration files will
    be chained using `collections.ChainMap`.

    Args:
        file_paths (str): list of paths to the YAML configuration files as
        positional arguments.
    """
    configuration = ChainMap()

    for fpath in file_paths:
        with open(fpath) as fo:
            configuration = configuration.new_child(yaml.safe_load(fo.read()))

    return configuration
