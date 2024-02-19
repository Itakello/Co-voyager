import json
import os.path
import time
import warnings
from typing import Any, Dict, SupportsFloat, Tuple

import gymnasium as gym
import requests
from gymnasium.core import ObsType

import voyager.utils as U

from .minecraft_launcher import MinecraftInstance
from .process_monitor import SubProcess


class VoyagerEnv(gym.Env):
    def __init__(
        self,
        mc_port,
        azure_login,
        wait_ticks=50,
        server_host="http://127.0.0.1",
        max_iteractions=160,
        server_port=3000,
        request_timeout=600,
        log_path="./logs",
    ):
        if not mc_port and not azure_login:
            raise ValueError("Either mc_port or azure_login must be specified")
        if mc_port and azure_login:
            warnings.warn(
                "Both mc_port and mc_login are specified, mc_port will be ignored"
            )
        self.server = f"{server_host}:{server_port}"
        self.max_iteractions = max_iteractions
        self.request_timeout = request_timeout
        self.wait_ticks = wait_ticks
        self.log_path = log_path
        self.mineflayer = self.get_mineflayer_process(server_port)
        if azure_login:
            self.mc_instance = self.get_mc_instance(azure_login)
            self.mc_port = self._start_minecraft_server()
        else:
            self.mc_instance = None
            self.mc_port = mc_port
        self.has_reset = False
        self.reset_options = None
        self.connected = False
        self.server_paused = False

    def get_mineflayer_process(self, server_port: int) -> SubProcess:
        print("Creating Mineflayer process")
        U.f_mkdir(self.log_path, "mineflayer")
        file_path = os.path.abspath(os.path.dirname(__file__))
        return SubProcess(
            commands=[
                "node",
                U.f_join(file_path, "mineflayer/index.js"),
                str(server_port),
            ],
            name="mineflayer",
            ready_match=r"Server started on port (\d+)",
            log_path=U.f_join(self.log_path, "mineflayer"),
        )

    def get_mc_instance(self, azure_login: dict) -> MinecraftInstance:
        print("Creating Minecraft server")
        U.f_mkdir(self.log_path, "minecraft")
        return MinecraftInstance(
            client_id=azure_login["client_id"],
            redirect_url=azure_login["redirect_url"],
            secret_value=azure_login["secret_value"],
            version=azure_login["version"],
            mineflayer=self.mineflayer,
            log_path=U.f_join(self.log_path, "minecraft"),
        )

    def _start_minecraft_server(self) -> int:
        if not self.mc_instance or self.mc_instance.is_running:
            raise RuntimeError("Minecraft server is already running")
        print("Starting Minecraft server")
        self.mc_instance.run()
        print(f"Server started on port {self.mc_instance.port}")
        return self.mc_instance.port

    def _start_mineflayer(self, options: dict) -> list:
        if not self.mineflayer or self.mineflayer.is_running:
            raise RuntimeError("Mineflayer process is already running")
        print("Starting Mineflayer process")
        started = False
        for _ in range(3):
            self.mineflayer.start()
            if self.mineflayer.is_running:
                started = True
                break
        if not started:
            raise RuntimeError("Mineflayer process failed to start")
        print(self.mineflayer.ready_line)
        res = requests.post(
            f"{self.server}/start",
            json=options,
            timeout=self.request_timeout,
        )
        if res.status_code != 200:
            self.mineflayer.stop()
            raise RuntimeError(f"Minecraft server reply with code {res.status_code}")
        last_events = json.loads(res.json())
        return last_events

    def reset(
        self,
        mode: str = "hard",
        inventory: dict = {},
        equipment: list = [],
        spread: bool = False,
        position=None,
    ) -> list:
        if inventory and mode != "hard":
            raise RuntimeError("inventory can only be set when mode is hard")

        self.unpause()
        self.mineflayer.stop()
        time.sleep(3)  # wait for mineflayer to exit

        options = {
            "port": self.mc_port,
            "reset": mode,
            "inventory": inventory,
            "equipment": equipment,
            "spread": spread,
            "waitTicks": self.wait_ticks,
            "position": position,
        }
        last_events = self._start_mineflayer(options)
        self.has_reset = True
        self.connected = True
        self.pause()
        return last_events

    def step(
        self,
        code: str,
        programs: str = "",
    ) -> dict:
        if not self.has_reset:
            raise RuntimeError("Environment has not been reset yet")
        self.unpause()
        data = {
            "code": code,
            "programs": programs,
        }
        res = requests.post(
            f"{self.server}/step", json=data, timeout=self.request_timeout
        )
        if res.status_code != 200:
            raise RuntimeError("Failed to step Minecraft server")
        self.pause()
        returned_data = json.loads(res.json())
        return returned_data

    def close(self) -> None:
        self.unpause()
        if self.connected:
            res = requests.post(f"{self.server}/stop")
            if res.status_code == 200:
                self.connected = False
            else:
                raise RuntimeError(
                    f"Failed to stop Minecraft server with code {res.status_code}"
                )
        if self.mc_instance:
            self.mc_instance.stop()
        self.mineflayer.stop()

    def pause(self) -> None:
        if self.server_paused:
            return
        res = requests.post(f"{self.server}/pause")
        if res.status_code == 200:
            self.server_paused = True
        else:
            raise RuntimeError(
                f"Failed to pause Minecraft server with code {res.status_code}"
            )

    def unpause(self) -> None:
        if not self.server_paused:
            return
        res = requests.post(f"{self.server}/pause")
        if res.status_code == 200:
            self.server_paused = False
        else:
            raise RuntimeError(
                f"Failed to unpause Minecraft server with code {res.status_code}"
            )
