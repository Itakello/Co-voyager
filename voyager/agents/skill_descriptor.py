from dataclasses import dataclass
from typing import Union

from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI

import voyager.utils as U
from voyager.control_primitives import load_control_primitives
from voyager.prompts import load_prompt
from voyager.utils.llms import get_llm


@dataclass
class SkillDescriptor:

    llm: Union[AzureChatOpenAI, ChatOpenAI, ChatOllama]
    skills: dict
    control_primitives: list[str]
    file_path: str

    def __init__(
        self, dir: str, llm_type: str, temperature: int = 0, request_timeout: int = 240
    ):
        self.llm = get_llm(llm_type, temperature, request_timeout)
        self.file_path = f"{dir}/skills.json"
        if U.f_exists(self.file_path):
            self.skills = self._get_skills(self.file_path)
        else:
            self.skills = {}
            U.dump_json(self.skills, self.file_path)

        self.control_primitives = load_control_primitives()

    @property
    def programs(self):
        programs = ""
        for skill_name, entry in self.skills.items():
            programs += f"{entry['code']}\n\n"
        for primitives in self.control_primitives:
            programs += f"{primitives}\n\n"
        return programs

    def _get_skills(self, file_path) -> dict:
        skills_dict = U.load_json(file_path)
        skills = {}
        for skill_name, skill in skills_dict.items():
            skills[skill_name] = {
                "executable_code": skill["executable_code"],
                "code": skill["code"],
            }
        return skills

    def add_new_skill(
        self, program_name: str, program_code: str, full_code: str
    ) -> None:
        # skill_description = self._generate_skill_description(program_name, program_code)
        # print(
        #    f"\033[33mSkill Manager generated description for {program_name}:\n{skill_description}\033[0m"
        # )
        self.skills[program_name] = {
            "code": program_code,
            # "description": skill_description,
            "executable_code": full_code,
        }
        U.dump_json(self.skills, self.file_path)

    def _generate_skill_description(self, program_name: str, program_code: str) -> str:
        messages = [
            SystemMessage(content=load_prompt("skill")),
            HumanMessage(
                content=program_code
                + "\n\n"
                + f"The main function is `{program_name}`."
            ),
        ]
        skill_description = f"    // {self.llm.invoke(messages).content}"
        return f"async function {program_name}(bot) {{\n{skill_description}\n}}"
