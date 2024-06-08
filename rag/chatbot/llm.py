# https://gist.github.com/jvelezmagic/03ddf4c452d011aae36b2a0f73d72f68

from typing import Any, Union
import random
import tiktoken
from pathlib import Path
from dotenv import load_dotenv

# from langchain_community.chat_message_histories import PostgresChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_openai import AzureChatOpenAI
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from rag.config import AzureChatOpenAIConfig
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
)


class LangChainChatbot:
    """
    A class to handle the creation and interaction with a language model chatbot
    using AzureChatOpenAI and LangChain.
    """

    def __init__(self, config_path: Union[Path, str, None]):
        """
        Initializes the chatbot with the given configuration file.

        :param config_path: The path to the configuration file.
        """
        self.config_path = config_path
        self.llm = None
        self.prompt = None

    def _get_llm(self):
        """
        Initializes and returns the language model based on AzureChatOpenAI.

        :return: Initialized AzureChatOpenAI model.
        """
        # Ensure the config_path is a string for splitting
        file_extension = str(self.config_path).split(".")[-1]
        if file_extension == "yml":
            config = AzureChatOpenAIConfig.load_from_yaml(
                file_path=self.config_path
            ).model_dump()
        elif file_extension == "env":
            config = AzureChatOpenAIConfig.load_from_env(
                env_file=self.config_path
            ).model_dump()

        self.llm = AzureChatOpenAI(**config)
        return self.llm

    def _get_prompt(self):
        """
        Creates and returns the chat prompt template.

        :return: ChatPromptTemplate object.
        """
        self.prompt = ChatPromptTemplate(
            messages=[
                SystemMessagePromptTemplate.from_template(SYSTEM_MESSAGE),
                HumanMessagePromptTemplate.from_template(HUMAN_MESSAGE),
            ]
        )
        return self.prompt

    def get_llm_rag_chain(self):
        """
        Creates and returns a ConversationalRetrievalChain with the given retriever.

        :param retriever: The retriever to be used in the chain.
        :return: A ConversationalRetrievalChain object.
        """
        if not self.llm:
            self._get_llm()

        if not self.prompt:
            self._get_prompt()

        chain: LLMChain = LLMChain(llm=self.llm, prompt=self.prompt)

        return chain

    @classmethod
    def get_llm_rag_chain_cls(cls, config_path):
        """
        Class method to create an instance of LangChainChatbot and return a
        ConversationalRetrievalChain.

        :param config_path: The path to the configuration file.
        :param retriever: The retriever to be used in the chain.
        :return: A ConversationalRetrievalChain object.
        """
        chatbot_instance = cls(config_path)
        return chatbot_instance.get_llm_rag_chain()


class DummyConversation:
    def __init__(self, model):
        self.encoding = tiktoken.encoding_for_model(model)
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
        ]

    def count_tokens(self, text):
        num_tokens = len(self.encoding.encode(text))
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
