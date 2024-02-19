import voyager.utils as U
import wandb
from voyager import Voyager
from voyager.utils.components import get_agents, get_environment, get_recorder
from voyager.utils.config import get_azure_login, set_openai_config

run = 1
for skill_library in [
    "skill_library/trial1",
    "skill_library/trial2",
    "skill_library/trial3",
]:
    for run in range(3):
        wandb.init(
            project="Co-Voyager",
            name=f"baseline-{run}"
            # track hyperparameters and run metadata
            config={"skill_library": skill_library},
        )
        run += 1

        set_openai_config()
        U.file_utils.f_remove("ckpt")

        azure_login = get_azure_login()

        env = get_environment(azure_login)
        action_agent, curriculum_agent, critic_agent, skill_manager = get_agents(
            resume=False,
            request_timeout=240,
            skills_folder="skill_library/trial1",
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

        # voyager.learn()
        voyager.learn_task(
            task="Build a wooden house 4x4 with a door and a gated-fence around it."
        )

        wandb.finish()
