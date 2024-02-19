import os

import wandb
from voyager import Voyager
from voyager.classes.subtask import SubTask
from voyager.classes.task import Task
from voyager.utils.components import get_agents, get_environment, get_recorder
from voyager.utils.config import fix_folders, get_azure_login, set_openai_config

os.environ["WANDB_MODE"] = "offline"

wandb.init(
    project="Co-Voyager",
    name=f"test",
)

task = Task(
    name="cobblestone_pickaxe",
    content="Craft a Cobblestone Pickaxe",
    sub_tasks=[
        SubTask(
            "Gather 10 Wood Logs, craft them into Wooden Planks directly in the Inventory and place them all in the chest"
        ),
        SubTask(
            "Craft Wooden Pickaxe",
            materials="3 Wooden Planks, 2 Sticks",
            tool="Crafting Table",
        ),
        SubTask(
            "Gather 10 Cobblestones and place them all in the chest",
            tool="Wooden Pickaxe",
        ),
        SubTask(
            "Craft a Cobblestone Pickaxe",
            tool="Crafting table",
            materials="3 Cobblestones, 2 Sticks",
        ),
    ],
)

set_openai_config()
fix_folders()

azure_login = get_azure_login()

env = get_environment(azure_login=azure_login, server_port=3000, request_timeout=600)
action_agent, critic_agent, skill_manager = get_agents(
    skills_folder=task.skills_folder,
    temperature=0,
    request_timeout=240,
    action_agent_llm_type="gpt-4",
    critic_agent_llm_type="gpt-4",
    skill_manager_llm_type="gpt-3.5-turbo",
)

voyager = Voyager(
    env=env,
    action_agent=action_agent,
    critic_agent=critic_agent,
    skill_manager=skill_manager,
)

# voyager.learn()

voyager.learn_task(
    starting_position=(-14, -60, -4),
    task=task,
)

wandb.finish()
