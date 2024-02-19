from dataclasses import dataclass

from langchain.schema import SystemMessage

from voyager.prompts import load_prompt
from voyager.utils.llms import get_llm


@dataclass
class CreatorAgent:
    ckpt_dir: str = "ckpt"
    resume = False
    max_retries: int = 4
    num_iter: int = -1

    def __post_init__(
        self, llm_type: str, temperature: float = 0, request_timeout: int = 120
    ) -> None:
        self.llm = get_llm(llm_type, temperature, request_timeout)

    def get_instruction_message(self, task: str) -> SystemMessage:
        prompt_template = load_prompt("creator_template")
        response_format = load_prompt("action_response_format")

        return SystemMessage(content=prompt_template)

    def get_prompt(self, task: str) -> str:
        return f"Create a Minecraft world with the following task: {task}"
