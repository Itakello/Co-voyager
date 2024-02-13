from typing import Union

from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI


def get_llm(
    type: str, temperature: int, timeout: int
) -> Union[AzureChatOpenAI, ChatOpenAI]:
    assert type in ["gpt-3.5-turbo", "gpt-4"], "Invalid LLM type"
    if type == "gpt-3.5-turbo":
        llm = ChatOpenAI(
            name="gpt-3.5-turbo",
            temperature=temperature,
            timeout=timeout,
        )
    else:
        # Pylance: Argument missing for parameter "cls"
        llm = AzureChatOpenAI(
            azure_deployment="DISI-GLP-Stefan",
            name="",
            temperature=temperature,
            timeout=timeout,
        )
    return llm
