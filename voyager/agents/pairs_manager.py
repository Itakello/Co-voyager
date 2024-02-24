from dataclasses import dataclass
from typing import Union

from langchain_community.chat_models import ChatOllama
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI

import voyager.utils as U
from voyager.utils.llms import get_llm


@dataclass
class PairsManager:

    # llm: Union[AzureChatOpenAI, ChatOpenAI, ChatOllama]
    file_path: str
    pairs: dict

    def __init__(
        self, dir: str
    ) -> None:  # ,llm_type: str, temperature: int, request_timeout: int):
        # self.llm = get_llm(llm_type, temperature, request_timeout)
        self.file_path = f"{dir}/pairs.json"
        if U.f_exists(self.file_path):
            self.pairs = U.load_json(self.file_path)
        else:
            self.pairs = {}
            U.dump_json(self.pairs, self.file_path)

    def add_new_pair(self, task: str, skill: str) -> None:
        self.pairs[task] = skill
        U.dump_json(self.pairs, self.file_path)

    def get_skill_name(self, task: str) -> str:
        if task not in self.pairs:
            raise ValueError(f"Task {task} not found in pairs")
        return self.pairs[task]
