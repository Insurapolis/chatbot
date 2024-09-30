from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Union
import random
from pathlib import Path
from dotenv import load_dotenv

from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain.llms.base import LLM
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from rag.config import OpenAIConfig, OllamaConfig
from rag.chatbot.templates import (
    SYSTEM_MESSAGE,
    HUMAN_MESSAGE,
)

from rag.chatbot.dummy_answer import (
    ANSWER_1,
    ANSWER_2,
    ANSWER_3,
    ANSWER_4,
    ANSWER_5,
    ANSWER_6,
    ANSWER_7,
    ANSWER_8,
    ANSWER_9,
    ANSWER_10,
    ANSWER_11,
    ANSWER_12,
    ANSWER_14,
)


class BaseChat(ABC):
    def __init__(
        self, llm: LLM | None = None, prompt: ChatPromptTemplate | None = None
    ):

        self.llm = llm
        self.prompt = prompt

    @property
    def prompt(self):
        if self._prompt is None:
            self._prompt = self._create_prompt()
        return self._prompt

    @prompt.setter
    def prompt(self, value):
        self._prompt = value

    def _create_prompt(self) -> ChatPromptTemplate:
        return ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(SYSTEM_MESSAGE),
                HumanMessagePromptTemplate.from_template(HUMAN_MESSAGE),
            ]
        )

    def get_chain(self):
        return self.prompt | self.llm

    @classmethod
    def chain_from_config(cls, config: str | Path | dict):
        if isinstance(config, (str, Path)):
            config_dict = cls._load_config(config)
        elif isinstance(config, dict):
            config_dict = config
        else:
            raise ValueError("Config must be a path, string, or dictionary.")

        llm = cls._get_llm(config_dict)
        instance = cls(llm=llm)
        return instance.get_chain()

    @staticmethod
    @abstractmethod
    def _load_config(path: Union[str, Path]) -> dict:
        pass

    @staticmethod
    @abstractmethod
    def _get_llm(config: dict):
        pass


class OpenaiChatbot(BaseChat):
    @staticmethod
    def _load_config(path: Union[str, Path]) -> dict:
        file_extension = str(path).split(".")[-1]

        if file_extension == "yml":
            return OpenAIConfig.load_from_yaml(file_path=path).model_dump()
        elif file_extension == "env":
            return OpenAIConfig.load_from_env(env_file=path).model_dump()
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")

    @staticmethod
    def _get_llm(config: dict):
        return ChatOpenAI(**config)


class OllamaChatbot(BaseChat):
    @staticmethod
    def _load_config(path: Union[str, Path]) -> dict:
        file_extension = str(path).split(".")[-1]

        if file_extension == "yml":
            return OllamaConfig.load_from_yaml(file_path=path).model_dump()
        elif file_extension == "env":
            return OllamaConfig.load_from_env(env_file=path).model_dump()
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}")

    @staticmethod
    def _get_llm(config: dict):
        return ChatOllama(**config)


class DummyConversation:
    def __init__(
        self,
    ):
        self.total_tokens = 0
        self.list_answer = [
            ANSWER_1,
            ANSWER_2,
            ANSWER_3,
            ANSWER_4,
            ANSWER_5,
            ANSWER_6,
            ANSWER_7,
            ANSWER_8,
            ANSWER_9,
            ANSWER_10,
            ANSWER_11,
            ANSWER_12,
            ANSWER_14,
        ]

    def count_tokens(self, text):
        num_tokens = 10
        return num_tokens

    def response(self):
        if self.list_answer:
            # Randomly choose an answer
            selected_answer = random.choice(self.list_answer)
            # Remove the chosen answer from the list
            self.list_answer.remove(selected_answer)
            return selected_answer
        else:
            return "No more answers available."

    def __call__(self, text: str):
        response = self.response()
        prompt_tokens = self.count_tokens(text=text)
        completion_tokens = self.count_tokens(text=response)

        return {
            "answer": response,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
