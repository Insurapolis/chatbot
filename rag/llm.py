# https://gist.github.com/jvelezmagic/03ddf4c452d011aae36b2a0f73d72f68

from langchain_openai import AzureChatOpenAI
from langchain.chains import ConversationalRetrievalChain
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)


from langchain.memory import ConversationBufferMemory, ConversationBufferWindowMemory


from rag.config import AzureChatOpenAIConfig
from rag.templates import SYSTEM_MESSAGE, HUMAN_MESSAGE


# def get_llm():

#     config = AzureChatOpenAIConfig.load_from_yaml(
#         file_path="./openai_config.yml"
#     ).model_dump()
#     llm = AzureChatOpenAI(**config)

#     return llm


# def get_prompt():

#     prompt = ChatPromptTemplate(
#         messages=[
#             SystemMessagePromptTemplate.from_template(SYSTEM_MESSAGE),
#             HumanMessagePromptTemplate.from_template(HUMAN_MESSAGE),
#         ]
#     )

#     return prompt


# def get_llm_rag_chain(retriever):

#     llm = get_llm()

#     prompt = get_prompt()

#     # Conversation Memory
#     memory = ConversationBufferWindowMemory(
#         memory_key="chat_history", return_messages=True, k=2
#     )

#     # Create a chain that uses the Chroma vector store
#     chain = ConversationalRetrievalChain.from_llm(
#         llm=llm,
#         chain_type="stuff",
#         retriever=retriever,
#         memory=memory,
#         verbose=True,
#         combine_docs_chain_kwargs={"prompt": prompt},
#     )

#     return chain


class LangChainChatbot:
    """
    A class to handle the creation and interaction with a language model chatbot
    using AzureChatOpenAI and LangChain.
    """

    def __init__(self, config_path="./openai_config.yml"):
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
        config = AzureChatOpenAIConfig.load_from_yaml(
            file_path=self.config_path
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

    def get_llm_rag_chain(self, retriever):
        """
        Creates and returns a ConversationalRetrievalChain with the given retriever.

        :param retriever: The retriever to be used in the chain.
        :return: A ConversationalRetrievalChain object.
        """
        if not self.llm:
            self._get_llm()

        if not self.prompt:
            self._get_prompt()

        # Conversation Memory
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history", return_messages=True, k=2
        )

        # Create a chain using the provided retriever
        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            memory=memory,
            verbose=True,
            combine_docs_chain_kwargs={"prompt": self.prompt},
        )

        return chain

    @classmethod
    def get_llm_rag_chain_cls(cls, config_path, retriever):
        """
        Class method to create an instance of LangChainChatbot and return a
        ConversationalRetrievalChain.

        :param config_path: The path to the configuration file.
        :param retriever: The retriever to be used in the chain.
        :return: A ConversationalRetrievalChain object.
        """
        chatbot_instance = cls(config_path)
        return chatbot_instance.get_llm_rag_chain(retriever)
