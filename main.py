from voyager import Voyager
from voyager.utils.config import *

set_openai_config()

fix_folders()

voyager = Voyager(
    azure_login=get_azure_login(),
    curriculum_agent_mode="manual",
    critic_agent_mode="auto",
    resume=False,
)

sub_goals = [
    "Punch 3 trees",
    "Craft 1 crafting table",
    "Place the crafting table",
    "Craft 4 wooden planks",
    "Craft 2 sticks",
    "Mine 3 cobblestone",
    "Craft 1 stone pickaxe",
]  # voyager.decompose_task("Craft a Stone Pickaxe")
voyager.inference(sub_goals=sub_goals)
