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
        self._update_subtasks()

    def _update_gather_quantities(self) -> None:
        materials = {}
        for sub_task in self.sub_tasks:
            if sub_task.action != "gather":
                for material in sub_task.materials:
                    if material.name not in materials:
                        materials[material.name] = 0
                    materials[material.name] += material.quantity * sub_task.quantity

        self._add_missing_craft_subtasks(materials=materials)

        materials = self._fix_wood_quantities(materials)

        for sub_task in self.sub_tasks:
            if sub_task.action in ["gather", "smelt"]:
                if sub_task.item not in materials:
                    raise ValueError(
                        f"Material [{sub_task.item}] was not previously gathered/crafted/smelted."
                    )
                sub_task.quantity = materials[sub_task.item]
                del materials[sub_task.item]
        if materials != {}:
            raise ValueError(f"Materials {materials} were not used in the task.")

    def _add_missing_craft_subtasks(self, materials: dict) -> None:
        gather_wood_position = self._find_subtask_position(
            action="gather", item="wood log"
        )
        sticks = materials.get("stick", 0)
        wood_planks = materials.get("wood plank", 0)
        if gather_wood_position == -1 and (sticks > 0 or wood_planks > 0):
            gather_wood_position = 0
            self.sub_tasks.insert(
                gather_wood_position,
                SubTask(
                    action="gather",
                    item="wood log",
                    quantity=0,
                ),
            )
        if sticks > 0 and self._find_subtask_position("craft", "stick") == -1:
            self.sub_tasks.insert(
                gather_wood_position + 1,
                SubTask(
                    action="craft",
                    item="stick",
                    quantity=sticks,
                    materials=f"{math.ceil(sticks / 2)} wood planks",
                ),
            )
        if wood_planks > 0 and self._find_subtask_position("craft", "wood plank") == -1:
            self.sub_tasks.insert(
                gather_wood_position + 1,
                SubTask(
                    action="craft",
                    item="wood plank",
                    quantity=wood_planks,
                    materials=f"{math.ceil(wood_planks / 4)} wood logs",
                ),
            )

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

    def _update_subtasks(self):
        for sub_task in self.sub_tasks:
            sub_task.update_status_to_ready(self.inventory)
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
