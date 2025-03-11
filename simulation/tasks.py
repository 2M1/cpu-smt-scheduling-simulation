import os
from dataclasses import dataclass, field
from enum import auto, Enum
from typing import Self

from simulation import TimeQuantum, N_THREADS

from matplotlib.pyplot import colormaps


@dataclass
class TaskCategoryCharacteristics:
    speedup: float = 1.0
    slots_filled: int = 1


class InstructionType(Enum):
    VSU = auto()  # vector and scalar unit
    LSU = auto()  # load/store unit
    BRANCH = auto()  # branch unit
    FX = auto()  # fixed point
    CRYPTO = auto()  # crypto
    DFU = auto()  # decimal floating point
    CTRL = auto()  # control instructions of the CPU
    NOP = auto()


@dataclass
class Instruction:
    type: InstructionType


@dataclass
class BranchInstruction(Instruction):
    class BranchMode(Enum):
        PROB = auto(), False
        UNTIL = auto(), False
        FROM = auto(), False
        CMP = auto(), False
        RET = auto(), True

        def __new__(cls, *args, **kwds):
            obj = object.__new__(cls)
            obj._value_ = args[0]
            return obj

        # ignore the first param since it's already set by __new__
        def __init__(self, _: str, always: bool = False):
            self.always = always

        def __str__(self):
            return self.value

    target_index_delta: int = 0
    branch_mode: BranchMode = BranchMode.PROB
    probability: float = 0.5
    counter_max: int = 0
    counter: int = 0
    reset_counter: bool = True

    def __init__(self):
        super().__init__(InstructionType.BRANCH)

    @classmethod
    def branch_after(cls: Self, x_times: int, to_relative: int, reset: bool = True) -> Self:
        instance = cls()
        instance.target_index_delta = to_relative
        instance.branch_mode = cls.BranchMode.FROM
        instance.counter_max = x_times
        instance.reset_counter = reset

        return instance

    @classmethod
    def branch_until(cls: Self, x_times: int, to_relative: int, reset: bool = True) -> Self:
        instance = cls()
        instance.target_index_delta = to_relative
        instance.branch_mode = cls.BranchMode.UNTIL
        instance.counter_max = x_times
        instance.reset_counter = reset
        return instance

    @classmethod
    def branch_prob(cls: Self, probability: float, to_relative: int) -> Self:
        instance = cls()
        instance.target_index_delta = to_relative
        instance.branch_mode = cls.BranchMode.PROB
        instance.probability = probability
        return instance

    @classmethod
    def compare(cls: Self) -> Self:
        instance = cls()
        instance.branch_mode = cls.BranchMode.CMP
        instance.probability = 0.0
        return instance

    @classmethod
    def ret(cls: Self) -> Self:
        instance = cls()
        instance.branch_mode = cls.BranchMode.RET
        return instance


class TaskCategory(Enum):
    VSU_CRYPTO_DFU = TaskCategoryCharacteristics(1.0)
    VSU_QUAD_WORD = TaskCategoryCharacteristics(1.0, 2)
    LSU = TaskCategoryCharacteristics(1.0)
    BRANCH = TaskCategoryCharacteristics(1.0)
    FX = TaskCategoryCharacteristics(1.0)


colors = colormaps['tab20c']


def get_task_color(task_id: int, total_tasks: int) -> str:
    return colors(float(task_id) / total_tasks)


@dataclass
class Task:
    id: int
    category: TaskCategory

    instructions: list[Instruction] = field(repr=False)
    inst_index: int = 0

    # representation data
    colour: str = ""

    # metadata
    fname: str = ""
    ran_at: list[TimeQuantum] = field(default_factory=list)
    completed_at: TimeQuantum = -1

    def __post_init__(self):
        self.colour = get_task_color(self.id, N_THREADS)
        print(
            f"Task {self.id} has colour {self.colour}"
        )

    def is_complete(self) -> bool:
        return self.completed_at > 0

    def mark_completed(self, quantum: TimeQuantum):
        self.completed_at = quantum
