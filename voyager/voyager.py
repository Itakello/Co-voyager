from dataclasses import dataclass

import wandb

from .agents import PairsManager, SkillManager, TaskManager
from .classes import SubTask
from .env import VoyagerEnv


@dataclass
class Voyager:

    env: VoyagerEnv
    task_manager: TaskManager
    skill_manager: SkillManager
    pairs_manager: PairsManager

    def execute_task(
        self,
        starting_position: tuple[int, int, int] = (-14, -60, -4),
        reset_mode: str = "hard",
    ) -> None:
        self.env.reset(
            mode=reset_mode,
        )
        pass

    def learn_task(
        self,
        starting_position: tuple[int, int, int] = (-14, -60, -4),
        reset_mode: str = "hard",
    ):
        self.env.reset(
            mode=reset_mode,
        )
        self.env.step(
            f"bot.chat(`/tp {starting_position[0]} {starting_position[1]} {starting_position[2]}`);\n"
            + "bot.chat(`/time set day`);",
        )
        for sub_task in self.task_manager.task.sub_tasks:
            print(
                f"\033[35mLearning task [{sub_task.content}] for at most {self.skill_manager.MAX_RETRIES} times\033[0m"
            )
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

    def _learn_skill(self, sub_task: SubTask) -> int:
        events = self.env.step("")
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
            events = self.env.step("")
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
