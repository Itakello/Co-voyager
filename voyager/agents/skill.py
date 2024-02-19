import os
from dataclasses import dataclass

from langchain.schema import HumanMessage, SystemMessage
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings

import voyager.utils as U
from voyager.control_primitives import load_control_primitives
from voyager.prompts import load_prompt
from voyager.utils.llms import get_llm


@dataclass
class SkillManager:

    dir: str
    temperature: int = 0
    request_timeout: int = 120
    llm_type: str = "gpt-3.5-turbo"

    def __post_init__(self):
        self.llm = get_llm(self.llm_type, self.temperature, self.request_timeout)
        U.f_mkdir(f"{self.dir}/code")
        U.f_mkdir(f"{self.dir}/description")
        U.f_mkdir(f"{self.dir}/vectordb")
        if U.f_exists(f"{self.dir}/skills.json"):
            self.skills = U.load_json(f"{self.dir}/skills.json")
        else:
            self.skills = {}

        self.control_primitives = load_control_primitives()

        self.vectordb = Chroma(
            collection_name="skill_vectordb",
            embedding_function=OpenAIEmbeddings(),
            persist_directory=f"{self.dir}/vectordb",
        )
        assert self.vectordb._collection.count() == len(self.skills), (
            f"Skill Manager's vectordb is not synced with skills.json.\n"
            f"There are {self.vectordb._collection.count()} skills in vectordb but {len(self.skills)} skills in skills.json.\n"
            f"Did you set resume=False when initializing the manager?\n"
            f"You may need to manually delete the vectordb directory for running from scratch."
        )

    @property
    def occupied(self) -> bool:
        return U.f_not_empty(f"{self.dir}/code")

    @property
    def programs(self):
        programs = ""
        for skill_name, entry in self.skills.items():
            programs += f"{entry['code']}\n\n"
        for primitives in self.control_primitives:
            programs += f"{primitives}\n\n"
        return programs

    def add_new_skill(self, program_name: str, program_code: str) -> None:
        skill_description = self._generate_skill_description(program_name, program_code)
        print(
            f"\033[33mSkill Manager generated description for {program_name}:\n{skill_description}\033[0m"
        )
        if program_name in self.skills:
            print(f"\033[33mSkill {program_name} already exists. Rewriting!\033[0m")
            self.vectordb._collection.delete(ids=[program_name])
            i = 2
            while f"{program_name}V{i}.js" in os.listdir(f"{self.ckpt_dir}/skill/code"):
                i += 1
            dumped_program_name = f"{program_name}V{i}"
        else:
            dumped_program_name = program_name
        self.vectordb.add_texts(
            texts=[skill_description],
            ids=[program_name],
            metadatas=[{"name": program_name}],
        )
        self.skills[program_name] = {
            "code": program_code,
            "description": skill_description,
        }
        assert self.vectordb._collection.count() == len(
            self.skills
        ), "vectordb is not synced with skills.json"
        U.dump_text(program_code, f"{self.dir}/code/{dumped_program_name}.js")
        U.dump_text(
            skill_description,
            f"{self.dir}/description/{dumped_program_name}.txt",
        )
        U.dump_json(self.skills, f"{self.dir}/skills.json")
        self.vectordb.persist()

    def retrieve_skills(self, query):
        k = min(self.vectordb._collection.count(), self.retrieval_top_k)
        if k == 0:
            return []
        print(f"\033[33mSkill Manager retrieving for {k} skills\033[0m")
        docs_and_scores = self.vectordb.similarity_search_with_score(query, k=k)
        print(
            f"\033[33mSkill Manager retrieved skills: "
            f"{', '.join([doc.metadata['name'] for doc, _ in docs_and_scores])}\033[0m"
        )
        skills = []
        for doc, _ in docs_and_scores:
            skills.append(self.skills[doc.metadata["name"]]["code"])
        return skills

    def _generate_skill_description(self, program_name, program_code):
        messages = [
            SystemMessage(content=load_prompt("skill")),
            HumanMessage(
                content=program_code
                + "\n\n"
                + f"The main function is `{program_name}`."
            ),
        ]
        skill_description = f"    // { self.llm.invoke(messages).content}"
        return f"async function {program_name}(bot) {{\n{skill_description}\n}}"
