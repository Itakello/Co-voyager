import voyager.utils as U
from voyager.agents import ActionAgent, CriticAgent, CurriculumAgent, SkillManager
from voyager.env import VoyagerEnv


def get_agents(
    skills_folder: str,
    temperature: int,
    request_timeout: int,
    action_agent_llm_type: str,
    critic_agent_llm_type: str,
    skill_manager_llm_type: str,
) -> tuple[ActionAgent, CurriculumAgent, CriticAgent, SkillManager]:
    action_agent = ActionAgent(
        temperature=temperature,
        request_timeout=request_timeout,
        llm_type=action_agent_llm_type,
    )

    critic_agent = CriticAgent(
        temperature=temperature,
        request_timeout=request_timeout,
        mode="manual",
        llm_type=critic_agent_llm_type,
    )

    skill_manager = SkillManager(
        dir=skills_folder,
        temperature=temperature,
        request_timeout=request_timeout,
        llm_type=skill_manager_llm_type,
    )
    return action_agent, critic_agent, skill_manager


def get_environment(
    azure_login: dict, server_port: int, request_timeout: int
) -> VoyagerEnv:
    env = VoyagerEnv(
        mc_port=None,
        azure_login=azure_login,
        server_port=server_port,
        request_timeout=request_timeout,
    )
    return env


def get_recorder(ckpt_dir: str = "ckpt", resume: bool = False) -> U.EventRecorder:
    return U.EventRecorder(ckpt_dir=ckpt_dir, resume=resume)
