import copy
from dataclasses import dataclass, field

import voyager.utils as U
import wandb
from voyager.classes.subtask import SubTask
from voyager.classes.task import Task

from .agents import ActionAgent, CriticAgent, SkillManager
from .env import VoyagerEnv


@dataclass
class Voyager:

    env: VoyagerEnv
    action_agent: ActionAgent
    critic_agent: CriticAgent
    skill_manager: SkillManager
    iterations: int = 0
    last_events: list = field(default_factory=list)

    def learn(self, reset_env=True) -> None:
        self.env.reset()
        self.last_events = self.env.step("")

        while True:
            if self.iterations > self.env.max_iteractions:
                print("Iteration limit reached")
                break
            task, context = self.curriculum_agent.propose_next_task(
                events=self.last_events,
                chest_observation=self.action_agent.render_chest_observation(),
            )
            print(
                f"\033[35mStarting task {task} for at most {self.action_agent.MAX_RETRIES} times\033[0m"
            )
            performed = False
            for _ in range(3):
                try:
                    info = self._rollout(
                        sub_task=task,
                        context=context,
                        reset_env=reset_env,
                    )
                    performed = True
                    break
                except Exception as e:
                    self.last_events = self.env.reset(
                        inventory=self.last_events[-1][1]["inventory"],
                        equipment=self.last_events[-1][1]["status"]["equipment"],
                        position=self.last_events[-1][1]["status"]["position"],
                    )
                    print("Your last round rollout terminated due to error:")
                    print(f"\033[41m{e}\033[0m")
            if not performed:
                info = {
                    "task": task,
                    "success": False,
                }

            if info["success"]:
                self.skill_manager.add_new_skill(info)

            self.curriculum_agent.update_exploration_progress(info)
            print(
                f"\033[35mCompleted tasks: {', '.join(self.curriculum_agent.completed_tasks)}\033[0m"
            )
            print(
                f"\033[35mFailed tasks: {', '.join(self.curriculum_agent.failed_tasks)}\033[0m"
            )
        return

    def decompose_task(self, task):
        if self.last_events == []:
            self.last_events = self.env.reset()
        return self.curriculum_agent._REFERENCE_decompose_task(task, self.last_events)

    def execute_task(
        self,
        task: Task,
        starting_position: tuple[int, int, int] = (-14, -60, -4),
        reset_mode: str = "hard",
    ) -> None:
        self.env.reset(
            mode=reset_mode,
        )

    def learn_task(
        self,
        task: Task,
        starting_position: tuple[int, int, int] = (-14, -60, -4),
        reset_mode: str = "hard",
    ):
        self.env.reset(
            mode=reset_mode,
        )

        for sub_task in task.sub_tasks:
            print(
                f"\033[35mLearning task [{sub_task.content}] for at most {self.action_agent.MAX_RETRIES} times\033[0m"
            )
            performed = False
            for _ in range(3):
                self.last_events = self.env.step(
                    f"bot.chat(`/tp {starting_position[0]} {starting_position[1]} {starting_position[2]}`);\n"
                    + "bot.chat(`/time set day`);",
                )
                try:
                    retries = self._rollout(
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

    def _step(
        self, events: list, sub_task: SubTask, code: str, critique: str
    ) -> tuple[bool, dict]:
        skill_text = self.action_agent.create_skill(
            events=events, subtask=sub_task, code=code, critique=critique
        )
        print(f"\033[34m****Action Agent ai message****\n{skill_text}\033[0m")
        program_code, program_name, exec_code = self.action_agent.extract_code(
            skill_text=skill_text
        )
        full_code = program_code + "\n" + exec_code
        events = self.env.step(
            code=full_code,
            programs=self.skill_manager.programs,
        )

        self.action_agent.update_chest_memory(events[-1][1]["nearbyChests"])
        success, critique = self.critic_agent.check_task_success(
            events=events,
            task=sub_task.content,
            chest_observation=self.action_agent.render_chest_observation(),
            max_retries=5,
        )

        if success:
            self.skill_manager.add_new_skill(
                program_name=program_name,
                program_code=program_code,
            )

        self.last_events = copy.deepcopy(events)

        return success, critique

    def _rollout(self, sub_task: SubTask) -> tuple[dict, int]:
        events = self.env.step("")
        iter = 0
        success = False
        code = ""
        critique = ""
        while not success or iter >= self.action_agent.MAX_RETRIES:
            success, code, critique = self._step(
                events=events, sub_task=sub_task, code=code, critique=critique
            )
            iter += 1
        return iter
