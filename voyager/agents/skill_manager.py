import re
import time
from dataclasses import dataclass, field
from typing import Union

from javascript import require
from langchain.prompts import SystemMessagePromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI

import voyager.utils as U
from voyager.classes.subtask import SubTask
from voyager.control_primitives_context import load_control_primitives_context
from voyager.prompts import load_prompt
from voyager.utils.llms import get_llm

from .skill_critic import SkillCritic
from .skill_descriptor import SkillDescriptor


@dataclass
class SkillManager:

    llm: Union[AzureChatOpenAI, ChatOpenAI, ChatOllama]
    critic: SkillCritic
    descriptor: SkillDescriptor
    skills_path: str
    file_path: str
    chest_memory: dict = field(default_factory=dict)
    MAX_RETRIES: int = 4

    def __init__(
        self,
        dir: str,
        critic: SkillCritic,
        descriptor: SkillDescriptor,
        llm_type: str,
        resume: bool,
        temperature: int = 0,
        request_timeout: int = 240,
    ):
        self.llm = get_llm(llm_type, temperature, request_timeout)
        self.critic = critic
        self.descriptor = descriptor
        self.file_path = f"{dir}/chest_memory.json"
        if U.f_exists(self.file_path) and resume:
            self.chest_memory = U.load_json(self.file_path)
        else:
            self.chest_memory = {}
            U.dump_json(self.chest_memory, self.file_path)

    def update_chest_memory(self, chests) -> None:
        for position, chest in chests.items():
            if position in self.chest_memory:
                if isinstance(chest, dict):
                    self.chest_memory[position] = chest
                if chest == "Invalid":
                    print(
                        f"\033[32mAction Agent removing chest {position}: {chest}\033[0m"
                    )
                    self.chest_memory.pop(position)
            else:
                if chest != "Invalid":
                    print(
                        f"\033[32mAction Agent saving chest {position}: {chest}\033[0m"
                    )
                    self.chest_memory[position] = chest
        U.dump_json(self.chest_memory, self.file_path)

    def render_chest_observation(self) -> str:
        chests = []
        for chest_position, chest in self.chest_memory.items():
            if isinstance(chest, dict) and len(chest) > 0:
                chests.append(f"{chest_position}: {chest}")
        for chest_position, chest in self.chest_memory.items():
            if isinstance(chest, dict) and len(chest) == 0:
                chests.append(f"{chest_position}: Empty")
        for chest_position, chest in self.chest_memory.items():
            if isinstance(chest, str):
                assert chest == "Unknown"
                chests.append(f"{chest_position}: Unknown items inside")
        assert len(chests) == len(self.chest_memory)
        chests_content = "\n" + "\n".join(chests) if chests else "None"
        return f"Chests:{chests_content}\n\n"

    def _get_skills_message(self) -> SystemMessage:
        system_template = load_prompt("skill_template")
        base_skills = [
            "exploreUntil",
            "mineBlock",
            "craftItem",
            "placeItem",
            "smeltItem",
            "useChest",
            "mineflayer",
        ]
        programs = "\n\n".join(load_control_primitives_context(base_skills))
        response_format = load_prompt("skill_response_format")
        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        system_message = system_message_prompt.format(
            programs=programs, response_format=response_format
        )
        return system_message

    def get_status_message(
        self, events, subtask: SubTask, code="", critique: str = ""
    ) -> HumanMessage:
        chat_messages = []
        error_messages = []
        # FIXME: damage_messages is not used
        damage_messages = []
        assert events[-1][0] == "observe", "Last event must be observe"
        for i, (event_type, event) in enumerate(events):
            if event_type == "onChat":
                chat_messages.append(event["onChat"])
            elif event_type == "onError":
                error_messages.append(event["onError"])
            elif event_type == "onDamage":
                damage_messages.append(event["onDamage"])
            elif event_type == "observe":
                biome = event["status"]["biome"]
                voxels = event["voxels"]
                entities = event["status"]["entities"]
                position = event["status"]["position"]
                equipment = event["status"]["equipment"]
                inventory_used = event["status"]["inventoryUsed"]
                inventory = event["inventory"]
                assert i == len(events) - 1, "observe must be the last event"

        observation = ""

        code_content = f"\n{code}" if code else "No code in the first round"
        observation += f"Code from the last round:{code_content}\n\n"

        error_content = (
            "\n" + "\n".join(error_messages) if error_messages else "No error"
        )
        observation += f"Execution error:{error_content}\n\n"

        chat_log_content = "\n" + "\n".join(chat_messages) if chat_messages else "None"
        observation += f"Chat log: {chat_log_content}\n\n"

        observation += f"Biome: {biome}\n\n"

        voxels_content = ", ".join(voxels) if voxels else "None"
        observation += f"Nearby blocks: {voxels_content}\n\n"

        if entities:
            nearby_entities = [
                k for k, _ in sorted(entities.items(), key=lambda x: x[1])
            ]
            observation += f"Nearby entities (nearest to farthest): {', '.join(nearby_entities)}\n\n"
        else:
            observation += f"Nearby entities (nearest to farthest): None\n\n"

        observation += f"Position: x={position['x']:.1f}, y={position['y']:.1f}, z={position['z']:.1f}\n\n"

        observation += f"Equipment: {equipment}\n\n"

        if inventory:
            observation += f"Inventory ({inventory_used}/36): {inventory}\n\n"
        else:
            observation += f"Inventory ({inventory_used}/36): Empty\n\n"

        observation += self.render_chest_observation()

        observation += f"Task: {subtask.content}\n\n"

        observation += f"Materials required: {subtask.materials}\n\n"

        observation += f"Tools required: {subtask.tools}\n\n"

        critique_content = critique if critique else "None"
        observation += f"Critique: {critique_content}\n\n"

        return HumanMessage(content=observation)

    def create_skill(
        self, events: list, subtask: SubTask, code: str, critique: str
    ) -> str:
        system_message = self._get_skills_message()
        human_message = self.get_status_message(
            events=events, code=code, subtask=subtask, critique=critique
        )
        messages = [system_message, human_message]
        print(
            f"\033[32m****Skill manager human message****\n{human_message.content}\033[0m"
        )
        ai_message = self.llm.invoke(messages)
        return ai_message.content

    def extract_code(self, skill_text: str) -> tuple[str, str, str]:
        retry = 3
        error = None
        while retry > 0:
            try:
                babel = require("@babel/core")
                babel_generator = require("@babel/generator").default

                code_pattern = re.compile(r"```(?:javascript|js)(.*?)```", re.DOTALL)
                code = "\n".join(code_pattern.findall(str(skill_text)))
                parsed = babel.parse(code)
                functions = []
                assert len(list(parsed.program.body)) > 0, "No functions found"
                for i, node in enumerate(parsed.program.body):
                    if node.type != "FunctionDeclaration":
                        continue
                    node_type = (
                        "AsyncFunctionDeclaration"
                        if node["async"]
                        else "FunctionDeclaration"
                    )
                    functions.append(
                        {
                            "name": node.id.name,
                            "type": node_type,
                            "body": babel_generator(node).code,
                            "params": list(node["params"]),
                        }
                    )
                # find the last async function
                main_function = None
                for function in reversed(functions):
                    if function["type"] == "AsyncFunctionDeclaration":
                        main_function = function
                        break
                assert (
                    main_function is not None
                ), "No async function found. Your main function must be async."
                assert (
                    len(main_function["params"]) == 1
                    and main_function["params"][0].name == "bot"
                ), f"Main function {main_function['name']} must take a single argument named 'bot'"
                program_code = "\n\n".join(function["body"] for function in functions)
                exec_code = f"await {main_function['name']}(bot);"
                return program_code, main_function["name"], exec_code
            except Exception as e:
                retry -= 1
                error = e
                time.sleep(1)
        print(f"Error parsing action response (before program execution): {error}")
        return "", "", ""
