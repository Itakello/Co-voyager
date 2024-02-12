from voyager import Voyager
from voyager.utils.components import get_agents, get_environment, get_recorder
from voyager.utils.config import get_azure_login, set_openai_config

set_openai_config()

azure_login = get_azure_login()

env = get_environment(azure_login)
action_agent, curriculum_agent, critic_agent, skill_manager = get_agents(
    resume=False, request_timeout=240, skill_library_dir=""
)
recorder = get_recorder(ckpt_dir="ckpt", resume=False)

voyager = Voyager(
    env=env,
    action_agent=action_agent,
    curriculum_agent=curriculum_agent,
    critic_agent=critic_agent,
    skill_manager=skill_manager,
    recorder=recorder,
)

voyager.learn()
