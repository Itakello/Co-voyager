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
    "Gather 5 wood logs.",
    "Craft 20 wood planks.",
    "Craft 8 stick.",
    "Craft 1 crafting table.",
    "Craft 1 wooden pickaxe.",
    "Gather 11 cobblestone.",
    "Craft 1 stone pickaxe.",
    "Gather 7 iron raws.",
    "Smelt 7 iron ingot.",
    "Craft 1 iron pickaxe.",
    "Gather 1 redstone dust.",
    "Craft 1 compass.",
]
voyager.inference(sub_goals=sub_goals)
