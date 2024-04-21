# import os
# import pandas as pd
# import chromadb
# from langchain_community.vectorstores import Chroma

# from rag.schema import InsuranceData
# from rag.utils import MODEL_NAME_RETRIEVER
# from rag.constants import (
#     FILENAME_DATASET_RAG,
#     COL_INDEX,
#     COL_TEXT,
#     COL_TYPE,
#     COL_CATEGORY,
#     COL_PACKAGE,
#     COL_ARTICLE,
#     COL_COMPANY,
#     COL_EMBEDDINGS,
# )


# class VectorDBClient:
#     def __init__(self, db_path: str, collection_name: str) -> None:
#         """
#         Initialize the VectorDBClient instance.

#         :param db_path: The path to the database.
#         :param collection_name: The name of the collection.
#         """
#         self._db_path = db_path
#         self._collection_name = collection_name
#         self._chroma_client = self._init_chroma_client()

#     def _init_chroma_client(self) -> chromadb.PersistentClient:
#         """
#         Initialize the ChromaDB PersistentClient.

#         :return: A PersistentClient instance.
#         """
#         try:
#             return chromadb.PersistentClient(path=self._db_path)
#         except Exception as e:
#             raise ConnectionError(
#                 f"Failed to connect to database at {self._db_path}: {e}"
#             )

#     @property
#     def db_path(self) -> str:
#         """Return the database path."""
#         return self._db_path

#     def collection_exists(self) -> bool:
#         """
#         Check if the collection exists in the database.

#         :return: True if the collection exists, False otherwise.
#         """
#         try:
#             return self._collection_name in [
#                 collection.name for collection in self._chroma_client.list_collections()
#             ]
#         except Exception as e:
#             print(f"Error checking collection existence: {e}")
#             return False

#     @classmethod
#     def get_chroma_collection_client(cls, db_path: str, collection_name: str):
#         """
#         Get a Chroma client instance if the collection exists.

#         :param db_path: The path to the database.
#         :param collection_name: The name of the collection.
#         :return: A Chroma client instance or raise a ValueError if the collection does not exist.
#         """
#         instance = cls(db_path, collection_name)
#         if instance.collection_exists():
#             try:
#                 return Chroma(
#                     persist_directory=instance.db_path,
#                     embedding_function=MODEL_NAME_RETRIEVER,
#                     collection_name=instance._collection_name,
#                 )
#             except Exception as e:
#                 raise RuntimeError(f"Failed to create Chroma client: {e}")
#         else:
#             raise ValueError("The collection was not found")


# class VectorDBCreator:
#     def __init__(self, db_path: str, collection_name: str):
#         self._set_db_path(db_path)
#         self._set_collection_name(collection_name)
#         self._chroma_client = chromadb.PersistentClient(path=self.db_path)

#     @property
#     def db_path(self):
#         return self._db_path

#     @db_path.setter
#     def db_path(self, value):
#         self._set_db_path(value)

#     @property
#     def collection_name(self):
#         return self._collection_name

#     @collection_name.setter
#     def collection_name(self, value):
#         self._set_collection_name(value)

#     def _set_db_path(self, value):
#         if not os.path.isdir(value):
#             raise ValueError(f"The directory {value} does not exist")
#         self._db_path = value

#     def _set_collection_name(self, value):
#         if not value:
#             raise ValueError("Collection name cannot be empty")
#         self._collection_name = value

#     @staticmethod
#     def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
#         """Validates a DataFrame against the InsuranceData schema."""
#         return InsuranceData.validate(df)

#     @classmethod
#     def create_collection_from_excel(
#         cls, db_path: str, collection_name: str, filepath: str
#     ):
#         """Creates a collection from an Excel file."""
#         df = pd.read_excel(filepath)
#         validated_df = cls.validate_dataframe(df)
#         creator = cls(db_path, collection_name)
#         creator.initialize_collection()
#         creator.add_insurance_data_to_collection(validated_df)

#     def initialize_collection(self):
#         """Initializes the collection in ChromaDB."""
#         if self.collection_name not in self._chroma_client.list_collections():
#             self._chroma_client.create_collection(self.collection_name)

#     def add_insurance_data_to_collection(self, df: pd.DataFrame):
#         """Adds insurance data to the collection."""
#         collection = self._chroma_client.get_collection(self.collection_name)
#         collection.add(
#             ids=df[COL_INDEX].tolist(),
#             embeddings=df[COL_EMBEDDINGS].tolist(),
#             metadatas=df[
#                 [COL_TYPE, COL_CATEGORY, COL_PACKAGE, COL_ARTICLE, COL_COMPANY]
#             ].to_dict("records"),
#             documents=df[COL_TEXT].tolist(),
#         )
