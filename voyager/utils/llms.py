from typing import Union

from langchain_community.chat_models import ChatOllama
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI


def get_llm(
    type: str, temperature: int, timeout: int
) -> Union[AzureChatOpenAI, ChatOpenAI, ChatOllama]:
    assert type in ["gpt-3.5-turbo", "gpt-4", "mistral"], "Invalid LLM type"
    if type == "gpt-3.5-turbo":
        llm = ChatOpenAI(
            name="gpt-3.5-turbo",
            temperature=temperature,
            timeout=timeout,
        )
    elif type == "gpt-4":
        llm = AzureChatOpenAI(
            azure_deployment="DISI-GLP-Stefan",
            name="",
            temperature=temperature,
            timeout=timeout,
        )
    else:
        llm = ChatOllama(model="mistral", temperature=temperature, timeout=timeout)
    return llm
