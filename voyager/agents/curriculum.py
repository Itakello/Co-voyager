from __future__ import annotations

import random
import re

from langchain.schema import HumanMessage, SystemMessage
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

import voyager.utils as U
from voyager.prompts import load_prompt
from voyager.utils.json_utils import fix_and_parse_json
from voyager.utils.llms import get_llm


class CurriculumAgent:
    def __init__(
        self,
        temperature=0,
        qa_temperature=0,
        request_timeout=120,
        core_inventory_items: str | None = None,
    ):
        self.llm = get_llm("gpt-4", temperature, request_timeout)
        self.qa_llm = get_llm("gpt-3.5-turbo", qa_temperature, request_timeout)

        self.qa_cache = {}

        self._core_inv_items_regex = re.compile(core_inventory_items)
        self.warm_up = self.default_warmup

    @property
    def default_warmup(self):
        return {
            "context": 15,
            "biome": 10,
            "time": 15,
            "nearby_blocks": 0,
            "other_blocks": 10,
            "nearby_entities": 5,
            "health": 15,
            "hunger": 15,
            "position": 0,
            "equipment": 0,
            "inventory": 0,
            "optional_inventory_items": 7,
            "chests": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
        }

    @property
    def curriculum_observations(self):
        return [
            "context",
            "biome",
            "time",
            "nearby_blocks",
            "other_blocks",
            "nearby_entities",
            "health",
            "hunger",
            "position",
            "equipment",
            "inventory",
            "chests",
            "completed_tasks",
            "failed_tasks",
        ]

    @property
    def progress(self):
        return len(self.completed_tasks)

    def _REFERENCE_decompose_task(self, task, events):
        messages = [
            SystemMessage(
                content=load_prompt("curriculum_task_decomposition"),
            ),
            self._get_human_message(events=events, chest_observation=""),
            HumanMessage(content=f"Final task: {task}"),
        ]
        response = self.llm.invoke(messages).content
        print(
            f"\033[31m****Curriculum Agent task decomposition****\nFinal task: {task}\nSubtasks: {response}\033[0m"
        )
        return fix_and_parse_json(response)

    def get_task_context(self, task: str) -> str:
        # if include ore in question, gpt will try to use tool with skill touch enhancement to mine
        question = (
            f"How to {task.replace('_', ' ').replace(' ore', '').replace(' ores', '').replace('.', '').strip().lower()}"
            f" in Minecraft?"
        )
        if question in self.qa_cache:
            answer = self.qa_cache[question]
        else:
            answer = self._ask_minecraft_question(question=question)
            self.qa_cache[question] = answer
        context = f"Question: {question}\n{answer}"
        return context

    def _ask_minecraft_question(self, question):
        messages = [
            SystemMessage(content=load_prompt("curriculum_qa_step2_answer_questions")),
            HumanMessage(content=f"Question: {question}"),
        ]
        print(f"\033[35mCurriculum Agent Question: {question}\033[0m")
        qa_answer = self.qa_llm.invoke(messages).content
        print(f"\033[31mCurriculum Agent {qa_answer}\033[0m")
        return qa_answer
