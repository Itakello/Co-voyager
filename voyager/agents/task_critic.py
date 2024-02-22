from dataclasses import dataclass
from typing import Union

from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI

from voyager.prompts import load_prompt
from voyager.utils.llms import get_llm


@dataclass
class TaskCritic:

    llm: Union[AzureChatOpenAI, ChatOpenAI, ChatOllama]
    mode: str

    def __init__(
        self, llm_type: str, mode: str, temperature: int = 0, request_timeout: int = 240
    ):
        self.llm = get_llm(llm_type, temperature, request_timeout)
        self.mode = mode
        assert self.mode in ["auto", "manual"]

    def get_critique(
        self, content: str, old_sub_tasks: list[dict], error: Exception
    ) -> str:
        if self.mode == "auto":
            messages = [
                SystemMessage(load_prompt("task_critic")),
                HumanMessage(
                    content=f"Previous subdivision:\n{old_sub_tasks}\n\nError: {error}\n\nTask: {content}\n\nCritique:"
                ),
            ]
            critique = self.llm.invoke(messages).content.strip()
        else:
            critique = input(
                f"Please provide a critique for the following error: {error}\n\nTask: {content}\n\nPrevious subdivision:\n{old_sub_tasks}\n\nCritique: "
            )
        return critique
