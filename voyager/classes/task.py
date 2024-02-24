import math
from dataclasses import dataclass, field

import voyager.utils as U
from voyager.classes import Status, SubTask


@dataclass
class Task:

    name: str
    content: str
    sub_tasks: list[SubTask]
    ready: bool = False
    inventory: dict = field(default_factory=dict)

    def __post_init__(self):
        self.path = f"tasks/{self.name}"
        if not U.file_utils.f_exists(self.path):
            U.file_utils.f_mkdir(self.path)
        self._check_tool_order()
        self._update_gather_quantities()
        self._initialize_subtasks()

    def _update_gather_quantities(self) -> None:
        materials = {}
        for i, sub_task in enumerate(self.sub_tasks):
            if sub_task.action in ["gather", "smelt"]:
                if i == len(self.sub_tasks) - 1:
                    for material in sub_task.materials:
                        if material.name not in materials:
                            materials[material.name] = 0
                        materials[material.name] += (
                            material.quantity * sub_task.quantity
                        )
                else:
                    sub_task.quantity = -1
            else:
                for material in sub_task.materials:
                    if material.name not in materials:
                        materials[material.name] = 0
                    materials[material.name] += material.quantity * sub_task.quantity

        for sub_task in self.sub_tasks[:-1]:
            if sub_task.action == "smelt":
                if sub_task.item not in materials:
                    raise ValueError(f"The smelting of [{sub_task.item}] was not used.")
                sub_task.quantity = materials[sub_task.item]
                for material in sub_task.materials:
                    if material.name not in materials:
                        materials[material.name] = 0
                    materials[material.name] += material.quantity * sub_task.quantity
                del materials[sub_task.item]

        materials = self._add_wood_subtasks(materials=materials)

        for sub_task in self.sub_tasks[:-1]:
            if sub_task.action in ["gather"] and sub_task.quantity == -1:
                if sub_task.item not in materials:
                    raise ValueError(
                        f"Material [{sub_task.item}] was not previously {sub_task.action}ed."
                    )
                sub_task.quantity = materials[sub_task.item]
                del materials[sub_task.item]
        if materials != {}:
            raise ValueError(f"Materials {materials} have not been gathered/smelted.")

    def _add_wood_subtasks(self, materials: dict) -> dict:
        sticks = materials.get("stick", 0)
        if "stick" in materials:
            del materials["stick"]
        sticks = max(sticks, math.ceil(sticks / 4) * 4)
        wood_planks_for_sticks = math.ceil(sticks / 2)
        wood_planks = materials.get("wood plank", 0) + wood_planks_for_sticks
        if "wood plank" in materials:
            del materials["wood plank"]
        wood_planks = max(wood_planks, math.ceil(wood_planks / 4) * 4)
        wood_logs = materials.get("wood log", 0) + math.ceil(wood_planks / 4)
        if "wood log" in materials:
            del materials["wood log"]
        if sticks > 0 or wood_planks > 0:
            self.sub_tasks.insert(
                0,
                SubTask(
                    action="gather",
                    item="wood log",
                    quantity=wood_logs,
                ),
            )
        if sticks > 0:
            self.sub_tasks.insert(
                1,
                SubTask(
                    action="craft",
                    item="stick",
                    quantity=sticks,
                    materials=f"{wood_planks_for_sticks} wood planks",
                ),
            )
        if wood_planks > 0:
            self.sub_tasks.insert(
                1,
                SubTask(
                    action="craft",
                    item="wood plank",
                    quantity=wood_planks,
                    materials=f"{wood_logs} wood logs",
                ),
            )
        return materials

    def _fix_wood_quantities(self, materials) -> dict:
        if "wood plank" not in materials:
            materials["wood plank"] = 0
        if "stick" in materials:
            materials["wood plank"] += math.ceil(materials["stick"] / 2)
            del materials["stick"]
        if "wood log" not in materials:
            materials["wood log"] = 0
        materials["wood log"] += math.ceil(materials["wood plank"] / 4)
        del materials["wood plank"]
        return materials

    def _find_subtask_position(self, action: str, item: str) -> int:
        for i, sub_task in enumerate(self.sub_tasks):
            if sub_task.action == action and sub_task.item == item:
                return i
        return -1

    def _initialize_subtasks(self):
        for sub_task in self.sub_tasks:
            sub_task.update_statuses_to_ready(self.inventory)
            sub_task.generate_content()

    def complete_subtask(self, subtask_index: int):
        subtask = self.sub_tasks[subtask_index]
        if subtask.status != Status.IN_PROGRESS:
            raise ValueError(f"Subtask [{subtask.content}] is not in progress.")
        subtask.status = Status.COMPLETED

    def get_ready_subtasks(self):
        enumerated_subtasks = {}
        for i, subtask in enumerate(self.sub_tasks):
            if subtask.status == Status.READY:
                enumerated_subtasks[i] = subtask
        index = -1
        while index != -1:
            print(f"Ready subtasks:\n")
            for i, subtask in enumerate(enumerated_subtasks.items()):
                print(f"{i+1}: {subtask}")
            index = input("Enter the index of the subtask you want to perform: ")
            if index < 1 or index > len(enumerated_subtasks):
                index = -1

    def _check_tool_order(self):
        tools = []
        for sub_task in self.sub_tasks:
            if sub_task.tools != []:
                for tool in sub_task.tools:
                    if tool not in tools:
                        raise ValueError(
                            f"Tool [{tool}] for task [{sub_task.action} {sub_task.item}] was not crafted."
                        )
            if sub_task.action == "craft":
                if sub_task.item in tools:
                    raise ValueError(
                        f"Crafted tool [{sub_task.item}] was already crafted."
                    )
                tools.append(sub_task.item)
