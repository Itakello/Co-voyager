import os

import wandb
from voyager import Voyager
from voyager.agents import (
    PairsManager,
    SkillCritic,
    SkillDescriptor,
    SkillManager,
    TaskCritic,
    TaskManager,
)
from voyager.utils.components import get_environment
from voyager.utils.config import fix_folders, get_azure_login, set_openai_config

os.environ["WANDB_MODE"] = "offline"

wandb.init(
    project="Co-Voyager",
    name=f"test",
)

set_openai_config()

fix_folders()

task_manager = TaskManager(
    llm_type="gpt-4",
    critic=TaskCritic(
        llm_type="gpt-4",
        mode="auto",
    ),
)

skill_manager = SkillManager(
    llm_type="gpt-4",
    critic=SkillCritic(
        llm_type="gpt-4",
        mode="auto",
    ),
    descriptor=SkillDescriptor(dir=task_manager.dir, llm_type="gpt-3.5-turbo"),
)
pairs_manager = PairsManager(dir=task_manager.dir)

env = get_environment(
    azure_login=get_azure_login(), server_port=3000, request_timeout=600
)

voyager = Voyager(
    env=env,
    task_manager=task_manager,
    skill_manager=skill_manager,
    pairs_manager=pairs_manager,
)

voyager.learn_task(
    starting_position=(-14, -60, -4),
)

wandb.finish()
