from voyager import Voyager
from voyager.utils.config import *

set_openai_config()

voyager = Voyager(
    azure_login=get_azure_login(),
    curriculum_agent_mode="manual",
    critic_agent_mode="manual",
    resume=False,
)

tasks = voyager.decompose_task(task="Craft a Diamond Pickaxe")
voyager.inference(tasks=tasks)
