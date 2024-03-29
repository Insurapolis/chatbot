from pydantic import BaseModel, Field, model_serializer
from rag.utils import load_conf
from typing import List
# from pydantic import BaseModel
import os
from dotenv import load_dotenv
from dataclasses import dataclass

load_dotenv()


class Query(BaseModel):
    question: str


class BaseOpenAIConfig(BaseModel):
    model_name: str = Field(...)
    temperature: float = Field(default=0, ge=0.0, le=1.0)
    openai_api_key: str = Field(...)

    @classmethod
    def load_from_yaml(
        cls,
        file_path: str,
    ):
        """Alternative constructor to load the config from a file.

        Args:
            file_path (str): path to the YAML file containing the configuration.
            Defaults to `None`.

        Returns:
            BaseOpenAIConfig: instance of the configuration
        """
        return cls(**dict(load_conf(file_path)))


class AzureChatOpenAIConfig(BaseOpenAIConfig):

    azure_endpoint: str = Field(...)  # required
    azure_deployment: str = Field(...)
    api_version: str = Field(...)

    @model_serializer
    def serialize_model(self):
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "openai_api_key": self.openai_api_key,
            "azure_endpoint": self.azure_endpoint,
            "api_version": self.api_version,
            "azure_deployment": self.azure_deployment,
        }


class VectorDatabaseFilter(BaseModel):
    company: str = None
    category: List = None
    type: List = None

    @model_serializer
    def serialize_model(self):

        return {
            "company": self.company,
            "category": {"$in": self.category},
            "type": {"$in": self.type},
        }
        

@dataclass
class Postgres:
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "maicolrodrigues")
    POSTGRES_URL: str = (
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
        if (POSTGRES_USER != None and POSTGRES_PASSWORD != None)
        else f"postgresql://{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
