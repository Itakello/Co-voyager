import json
import os
from dataclasses import dataclass
from typing import Union

from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI

import voyager.utils as U
from voyager.agents import TaskCritic
from voyager.classes import SubTask, Task
from voyager.prompts import load_prompt
from voyager.utils.json_utils import fix_and_parse_json
from voyager.utils.llms import get_llm


@dataclass
class TaskManager:

    llm: Union[AzureChatOpenAI, ChatOpenAI, ChatOllama]
    critic: TaskCritic
    dir: str
    task: Task
    sub_tasks_path: str
    MAX_RETRIES: int = 4

    def __init__(
        self,
        critic: TaskCritic,
        llm_type: str,
        temperature: int = 0,
        request_timeout: int = 240,
    ):
        self.llm = get_llm(llm_type, temperature, request_timeout)
        self.critic = critic

        name, content = self._get_task_descriptors()
        self.dir = U.f_mkdir(f"tasks/{name}")
        with open(f"{self.dir}/task_content.txt", "w") as f:
            f.write(content)
        self.sub_tasks_path = f"{self.dir}/sub_tasks.json"
        self.task = self._get_task(name=name, content=content)

    def _get_task_descriptors(self) -> tuple[str, str]:
        confirmed = False
        while not confirmed:
            old_task = input("Is this an old task? (y/n): ") in ["y", ""]
            if old_task:
                possible_tasks = os.listdir("tasks")
                poassible_tasks_str = "\n".join(
                    [f"{i+1}. {agent}" for i, agent in enumerate(possible_tasks)]
                )
                name = possible_tasks[
                    int(input(f"Which of these?\n{poassible_tasks_str}\nINPUT: ")) - 1
                ]
                content = U.load_text(f"tasks/{name}/task_content.txt")
            else:
                name = input("Enter the task name (e.g. 'cobblestone_pickaxe'): ")
                if name == "":
                    name = "diamond_pickaxe"
                content = input(
                    "Enter the task content (e.g. 'Craft a Cobblestone Pickaxe'): "
                )
                if content == "":
                    content = "Craft a Diamond Pickaxe"
            confirmed = input(f"Confirm? ") in ["y", ""]
        return name, content

    def _get_task(self, name: str, content: str) -> Task:
        sub_tasks = self._get_initial_subtasks(content=content)
        parsed = False
        for _ in range(self.MAX_RETRIES):
            try:
                task = Task(name=name, content=content, sub_tasks=sub_tasks)
                parsed = True
                break
            except Exception as e:
                critique = self.critic.get_critique(
                    content=content,
                    old_sub_tasks=U.load_json(self.sub_tasks_path),
                    error=e,
                )
                sub_tasks = self._ask_for_sub_tasks(
                    content=content,
                    old_sub_tasks=U.load_json(self.sub_tasks_path),
                    critique=critique,
                )
                U.dump_json(sub_tasks, self.sub_tasks_path, indent=2)
                sub_tasks = [SubTask(**sub_task) for sub_task in sub_tasks]
        if not parsed:
            raise ValueError(
                f"Failed to parse task {name} after {self.MAX_RETRIES} retries"
            )
        return task

    def _get_initial_subtasks(self, content: str) -> list[SubTask]:
        if U.f_exists(self.sub_tasks_path):
            sub_tasks = U.load_json(self.sub_tasks_path)
        else:
            sub_tasks = self._ask_for_sub_tasks(content=content)
            U.dump_json(sub_tasks, self.sub_tasks_path, indent=2)
        sub_tasks = [SubTask(**sub_task) for sub_task in sub_tasks]
        return sub_tasks

    def _ask_for_sub_tasks(
        self, content: str, old_sub_tasks: list[dict] = [], critique: str = ""
    ) -> list[dict]:
        old_sub_tasks = old_sub_tasks if old_sub_tasks else "None"
        critique = critique if critique else "None"
        hm_content = f"Previous subdivision:\n{json.dumps(old_sub_tasks, indent=4)}\n\nCritique: {critique}\n\nTask: {content}\n"
        messages = [
            SystemMessage(content=load_prompt("task_response_format")),
            HumanMessage(content=hm_content),
        ]
        response = self.llm.invoke(input=messages).content
        print(f"\033[33mTask Manager received response:\n{response}\033[0m")
        return fix_and_parse_json(response)
