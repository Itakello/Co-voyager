from dataclasses import dataclass

import wandb

from .agents import PairsManager, SkillManager
from .classes import SubTask
from .env import VoyagerEnv


@dataclass
class Voyager:

    env: VoyagerEnv
    skill_manager: SkillManager
    pairs_manager: PairsManager

    def reset(self, starting_position: tuple[int, int, int]) -> None:
        self.env.reset(
            mode="hard",
        )
        self._chat(
            f"/tp {starting_position[0]} {starting_position[1]} {starting_position[2]}"
        )
        self._chat(f"/time set day")

    def execute(
        self,
        sub_task: SubTask,
    ) -> None:
        print(f"\033[35mExecuting sub_task [{sub_task.content}]\033[0m")
        performed = False
        for _ in range(3):
            try:
                retries = self._execute_task(
                    sub_task=sub_task,
                )
                performed = True
                break
            except Exception as e:
                print("Your last round rollout terminated due to error:")
                print(f"\033[41m{e}\033[0m")
        if not performed:
            raise ValueError("Rollout failed")
        wandb.log({"retries": retries})

    def learn_task(self, sub_task: SubTask, index: int) -> None:
        print(f"\033[35m[{index}] [{sub_task.content}]\033[0m")
        performed = False
        for _ in range(3):
            try:
                retries = self._learn_skill(
                    sub_task=sub_task,
                )
                performed = True
                break
            except Exception as e:
                print("Your last round rollout terminated due to error:")
                print(f"\033[41m{e}\033[0m")
        if not performed:
            raise ValueError("Rollout failed")
        wandb.log({"retries": retries})

    def _execute_task(self, sub_task: SubTask) -> None:
        events = self._get_checkpoint()
        skill_name = self.pairs_manager.get_skill_name(sub_task.content)
        skill_code = self.skill_manager.descriptor.skills[skill_name]["executable_code"]
        self.skill_manager.update_chest_memory(events[-1][1]["nearbyChests"])
        events = self.env.step(
            code=skill_code,
            programs=self.skill_manager.descriptor.programs,
        )

    def _learn_skill(self, sub_task: SubTask) -> int:
        events = self._get_checkpoint()
        success = False
        code = ""
        critique = ""
        self.skill_manager.update_chest_memory(events[-1][1]["nearbyChests"])
        for iter in range(self.skill_manager.MAX_RETRIES):
            skill_text = self.skill_manager.create_skill(
                events=events, subtask=sub_task, code=code, critique=critique
            )
            print(f"\033[34m****Action Agent ai message****\n{skill_text}\033[0m")
            program_code, program_name, exec_code = self.skill_manager.extract_code(
                skill_text=skill_text
            )
            full_code = program_code + "\n" + exec_code
            events = self.env.step(
                code=full_code,
                programs=self.skill_manager.descriptor.programs,
            )
            self.skill_manager.update_chest_memory(events[-1][1]["nearbyChests"])
            success, critique = self.skill_manager.critic.check_task_success(
                events=events,
                task=sub_task.content,
                chest_observation=self.skill_manager.render_chest_observation(),
                max_retries=5,
            )

            if success:
                self.skill_manager.descriptor.add_new_skill(
                    program_name=program_name,
                    program_code=program_code,
                    full_code=full_code,
                )
                self.pairs_manager.add_new_pair(
                    task=sub_task.content, skill=program_name
                )
                break

        return iter + 1

    def _chat(self, call: str) -> dict:
        events = self.env.step(f"bot.chat(`{call}`);")
        return events

    def _get_checkpoint(self) -> dict:
        events = self.env.step("")
        return events
