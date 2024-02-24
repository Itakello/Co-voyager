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
from voyager.utils.config import get_azure_login, set_openai_config

os.environ["WANDB_MODE"] = "offline"
RESUME = False
INDEX_TASK = 0

wandb.init(
    project="Co-Voyager",
    name=f"test",
)

set_openai_config()

task_manager = TaskManager(
    llm_type="gpt-4",
    critic=TaskCritic(
        llm_type="gpt-4",
        mode="auto",
    ),
)

skill_manager = SkillManager(
    dir=task_manager.dir,
    resume=RESUME,
    llm_type="gpt-4",
    critic=SkillCritic(
        llm_type="gpt-4",
        mode="auto",
    ),
    descriptor=SkillDescriptor(dir=task_manager.dir, llm_type="gpt-3.5-turbo"),
)
pairs_manager = PairsManager(dir=task_manager.dir)

env = get_environment(
    azure_login=get_azure_login(), server_port=3000, request_timeout=200, resume=RESUME
)

voyager = Voyager(
    env=env,
    skill_manager=skill_manager,
    pairs_manager=pairs_manager,
)

voyager.reset(starting_position=(-14, -60, -4))

# if RESUME:
# task_manager.task.sub_tasks = task_manager.task.sub_tasks[INDEX_TASK:]

for i, sub_task in enumerate(task_manager.task.sub_tasks):
    index = i + INDEX_TASK if RESUME else i
    voyager.learn_task(sub_task=sub_task, index=index)

# for i, sub_task in enumerate(task_manager.task.sub_tasks):
#    index = i + INDEX_TASK if RESUME else i
#    voyager.execute(sub_task=sub_task, index=index)


wandb.finish()

voyager.env.close()
