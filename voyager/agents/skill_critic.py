from dataclasses import dataclass
from typing import Union

from langchain.schema import HumanMessage, SystemMessage
from langchain_community.chat_models import ChatOllama
from langchain_openai.chat_models import ChatOpenAI
from langchain_openai.chat_models.azure import AzureChatOpenAI

from voyager.prompts import load_prompt
from voyager.utils.json_utils import fix_and_parse_json
from voyager.utils.llms import get_llm


@dataclass
class SkillCritic:

    llm: Union[AzureChatOpenAI, ChatOpenAI, ChatOllama]
    mode: str

    def __init__(
        self, llm_type: str, mode: str, temperature: int = 0, request_timeout: int = 240
    ):
        self.llm = get_llm(llm_type, temperature, request_timeout)
        self.mode = mode
        assert self.mode in ["auto", "manual"]

    def check_task_success(
        self, events: dict, task: str, chest_observation: str, max_retries: int = 5
    ) -> tuple[bool, str]:
        success = False
        critique = ""
        if "1 block" in task:
            task = task.split(" 1 block")[0] + "."
        if ". Then place" in task:
            task = task.split(" Then place")[0] + ""
        if (
            "crafting table" not in task
            and "furnace" not in task
            and " and place" in task
        ):
            task = task.split(" and place")[0] + "."
            task += " It's ok if they are in the inventory or in the chest."
        human_message = self._get_status_message(
            events=events,
            task=task,
            chest_observation=chest_observation,
        )
        if self.mode == "manual":
            success, critique = self._human_check_task_success()
        else:
            messages = [
                SystemMessage(content=load_prompt("skill_critic")),
                human_message,
            ]
            success, critique = self._ai_check_task_success(
                messages=messages, max_retries=max_retries
            )
        return success, critique

    def _get_status_message(self, *, events, task, chest_observation):
        assert events[-1][0] == "observe", "Last event must be observe"
        last_event = events[-1][1]
        status = last_event["status"]

        for i, (event_type, event) in enumerate(events):
            if event_type == "onError":
                print(f"\033[31mCritic Agent: Error occurs {event['onError']}\033[0m")
                return None

        observation = ""

        observation += f"Biome: {status['biome']}\n\n"

        observation += f"Time: {status['timeOfDay']}\n\n"

        nearby_blocks_content = (
            {", ".join(last_event["voxels"])} if last_event["voxels"] else "None"
        )
        observation += f"Nearby blocks: {nearby_blocks_content}\n\n"

        observation += f"Health: {status['health']:.1f}/20\n\n"
        observation += f"Hunger: {status['food']:.1f}/20\n\n"
        observation += f"Position: x={status['position']['x']:.1f}, y={status['position']['y']:.1f}, z={status['position']['z']:.1f}\n\n"
        observation += f"Equipment: {status['equipment']}\n\n"

        inventory_content = (
            last_event["inventory"] if last_event["inventory"] else "Empty"
        )
        observation += (
            f"Inventory ({status['inventoryUsed']}/36): {inventory_content}\n\n"
        )

        observation += chest_observation

        observation += f"Task: {task}\n\n"

        print(f"\033[31m****Critic Agent human message****\n{observation}\033[0m")
        return HumanMessage(content=observation)

    def _human_check_task_success(self):
        confirmed = False
        success = False
        critique = ""
        while not confirmed:
            success = input("Success? (y/n)").lower() in ["y", ""]
            critique = input("Enter your critique:") if not success else ""
            print(f"Success: {success}\nCritique: {critique}")
            confirmed = input("Confirm? (y/n)").lower() in ["y", ""]
        return success, critique

    def _ai_check_task_success(self, messages, max_retries=5):
        if max_retries == 0:
            print(
                "\033[31mFailed to parse Critic Agent response. Consider updating your prompt.\033[0m"
            )
            return False, ""

        if messages[1] is None:
            return False, ""

        critic = self.llm.invoke(messages).content
        print(f"\033[31m****Critic Agent ai message****\n{critic}\033[0m")
        try:
            response = fix_and_parse_json(critic)
            assert response["success"] in [True, False]
            if "critique" not in response:
                response["critique"] = ""
            return response["success"], response["critique"]
        except Exception as e:
            print(f"\033[31mError parsing critic response: {e} Trying again!\033[0m")
            return self._ai_check_task_success(
                messages=messages,
                max_retries=max_retries - 1,
            )
