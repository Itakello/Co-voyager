import voyager.utils as U
from voyager.env import VoyagerEnv
from voyager.utils.config import reset_worlds, restore_world


def get_environment(
    azure_login: dict, server_port: int, request_timeout: int, resume: bool
) -> VoyagerEnv:
    if not resume:
        reset_worlds()
    env = VoyagerEnv(
        mc_port=None,
        azure_login=azure_login,
        server_port=server_port,
        request_timeout=request_timeout,
    )
    return env


def get_recorder(ckpt_dir: str = "ckpt", resume: bool = False) -> U.EventRecorder:
    return U.EventRecorder(ckpt_dir=ckpt_dir, resume=resume)
