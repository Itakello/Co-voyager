import voyager.utils as U
from voyager.agents import ActionAgent, CriticAgent, CurriculumAgent, SkillManager
from voyager.env import VoyagerEnv


def get_agents(
    resume: bool = False,
    request_timeout: int = 240,
    skill_library_dir: str = "",
    ckpt_dir: str = "ckpt",
) -> tuple[ActionAgent, CurriculumAgent, CriticAgent, SkillManager]:
    action_agent = ActionAgent(
        temperature=0,
        request_timeout=request_timeout,
        ckpt_dir=ckpt_dir,
        resume=resume,
        chat_log=True,
        execution_error=True,
    )

    curriculum_agent = CurriculumAgent(
        temperature=0,
        qa_temperature=0,
        request_timeout=request_timeout,
        ckpt_dir=ckpt_dir,
        resume=resume,
        mode="manual",
        warm_up=None,
        core_inventory_items=r".*_log|.*_planks|stick|crafting_table|furnace|cobblestone|dirt|coal|.*_pickaxe|.*_sword|.*_axe",
    )

    critic_agent = CriticAgent(
        temperature=0,
        request_timeout=request_timeout,
        mode="manual",
    )

    skill_manager = SkillManager(
        temperature=0,
        retrieval_top_k=5,
        request_timeout=request_timeout,
        ckpt_dir=skill_library_dir if skill_library_dir != "" else ckpt_dir,
        resume=True if resume or skill_library_dir else False,
    )
    return action_agent, curriculum_agent, critic_agent, skill_manager


def get_environment(azure_login: dict) -> VoyagerEnv:
    env = VoyagerEnv(
        mc_port=None,
        azure_login=azure_login,
        server_port=3000,
        request_timeout=600,
    )
    return env


def get_recorder(ckpt_dir: str = "ckpt", resume: bool = False) -> U.EventRecorder:
    return U.EventRecorder(ckpt_dir=ckpt_dir, resume=resume)
