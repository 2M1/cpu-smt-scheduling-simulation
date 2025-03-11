from dataclasses import dataclass, field
from enum import auto, Enum
from pathlib import Path
from time import sleep
from typing import Optional, Annotated, Callable, Any
from pprint import pprint

from simulation.load_exec import load_exec_dump
from simulation.pipeline import PipelineStart, Pipeline
from simulation.scheduling import slot_fill_shed, score_scheduling, round_robin_smt4
from simulation.simulation import run_simulation_to_exhaustion
from simulation.tasks import Task, TaskCategory, InstructionType, BranchInstruction
from simulation.display import plot_schedule_processor_view
from simulation.tasks import TimeQuantum

import matplotlib.colors
import matplotlib.pyplot as plt
from matplotlib import colormaps

QUNATUM_NUM_CYCLES = 0  # TODO
SMT_MAX = 4

N_THREADS = 5


def calculate_statistics(timeline: dict[TimeQuantum, list[Task]]) -> dict[str, Any]:
    return {}


if __name__ == '__main__':
    # res = run_simulation_to_exhaustion([
    #     (0, Task(0, TaskCategory.LSU,
    #              [InstructionType.LSU, InstructionType.LSU, InstructionType.LSU, InstructionType.LSU] * 2)),
    #     (0, Task(1, TaskCategory.LSU,
    #              [InstructionType.LSU, InstructionType.FX, InstructionType.FX, InstructionType.LSU] * 2)),
    #     (0, Task(2, TaskCategory.FX,
    #              [InstructionType.LSU, InstructionType.LSU, InstructionType.LSU, InstructionType.LSU])),
    #     (0, Task(3, TaskCategory.FX,
    #              [InstructionType.LSU, InstructionType.LSU, InstructionType.LSU, InstructionType.LSU])),
    #     (0, Task(4, TaskCategory.LSU, [InstructionType.LSU, InstructionType.LSU, InstructionType.LSU])),
    #     (0, Task(5, TaskCategory.FX, [InstructionType.LSU, InstructionType.LSU, InstructionType.LSU])),
    #     (0, Task(6, TaskCategory.VSU_QUAD_WORD, [InstructionType.LSU] * 7)),
    #     # (0, Task("orange", TaskCategory.MEM, [InstructionType.MEM, InstructionType.MEM, InstructionType.MEM, InstructionType.MEM])),
    # ],
    #     slot_fill_shed)
    #
    # plot_schedule_processor_view(res, "Slot Scheduling")
    #
    tasks = load_exec_dump(Path("workload/matrix.dump"), {"mul_row_thread": 4})
    insts = tasks[0].instructions
    print(list(
        filter(lambda i: (i.type == InstructionType.BRANCH and i.branch_mode == BranchInstruction.BranchMode.UNTIL),
               insts)
    ))
    pipeline = Pipeline(tasks)
    while not (res := pipeline.tick()):
        pass
    pprint(res)
