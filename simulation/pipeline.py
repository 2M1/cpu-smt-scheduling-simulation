from __future__ import annotations

from dataclasses import dataclass, field
from random import random
from typing import NamedTuple, Self, Generator, Optional
from unittest import case

from simulation.state import ProcessorState, LimitedList
from simulation.tasks import Task, InstructionType, Instruction, BranchInstruction


class InstructionInfo(NamedTuple):
    inst: Instruction
    task: Task


@dataclass
class BranchPipeline:
    issue_queue: IssueQueueStage
    ex_content: list
    rf_stage: list
    issue_stage: list
    map_stage: list
    fin_stage: list
    xmit_stage: list

    def __init__(self):
        self.issue_queue = IssueQueueStage()
        self.ex_content = []
        self.rf_stage = []
        self.issue_stage = []
        self.map_stage = []
        self.fin_stage = []
        self.xmit_stage = []


class Stage:
    previous: Stage
    internal_size: int
    internal_content: LimitedList[InstructionInfo]

    def __init__(self, previous: Stage, internal_size: int, completion_rate: int = 1, name: str = "Stage"):
        assert internal_size >= 0

        self.previous = previous
        self.internal_content = LimitedList(internal_size)
        self.completion_rate = completion_rate
        self.name = name

    def forward(self) -> list[InstructionInfo]:
        finished_count = min(self.completion_rate, len(self.internal_content))

        res = [self.internal_content.pop(0) for _ in range(finished_count)]
        print(f"{self.name} passed {finished_count} instructions along")
        # load new ones (must be one cycle here)
        self.internal_content.extend(self.previous.forward())
        return res


class PipelineStart(Stage):
    threads: list[Task]
    next_fetch_index: int

    def __init__(self, threads: list[Task]):
        super().__init__(None, 0)
        self.threads = threads
        self.next_fetch_index = 0
        len(threads) - 1

    def forward(self) -> list[list[InstructionInfo]]:

        task_to_fetch_from = self.threads[self.next_fetch_index]

        instructions = task_to_fetch_from.instructions[
                       task_to_fetch_from.inst_index:task_to_fetch_from.inst_index + 8
                       ]
        instructions = list(
            map(lambda inst: InstructionInfo(inst, task_to_fetch_from), instructions)
        )
        for i, inst in enumerate(instructions):
            match inst:
                case InstructionInfo(inst=BranchInstruction(), task=task):
                    # determine branches
                    branch = inst.inst
                    if branch.branch_mode.always:
                        branch.target_index_delta += self.next_fetch_index + i
                    if branch.type == BranchInstruction.BranchMode.PROB and branch.probability >= random():
                        branch.target_index_delta += self.next_fetch_index + i
                    if branch.type == BranchInstruction.BranchMode.UNTIL and branch.counter_max > 0:
                        branch.counter += 1
                        if branch.counter <= branch.counter_max:
                            branch.target_index_delta += self.next_fetch_index + i
                            if branch.reset_counter: branch.counter = 0
                    if branch.type == BranchInstruction.BranchMode.FROM and branch.counter_max > 0:
                        branch.counter += 1
                        if branch.counter >= branch.counter_max:
                            branch.target_index_delta += self.next_fetch_index + i
                            if branch.reset_counter: branch.counter = 0

        ifb_additions = [[], [], [], []]
        ifb_additions[self.next_fetch_index] = instructions

        task_to_fetch_from.inst_index += 8
        self.next_fetch_index = (self.next_fetch_index + 1) % len(self.threads)
        print(f"Pipeline start fetched {len(instructions)} instructions")
        return ifb_additions


def even_take(l1: list, l2: list, n: int) -> Generator[InstructionInfo]:
    while n >= 0:
        if len(l1) > 0:
            yield l1.pop(0)
            n -= 1
        if len(l2) > 0:
            yield l2.pop(0)
            n -= 1
        if len(l1) == 0 and len(l2) == 0:
            break


class IFBStage(Stage):
    thread_buffers: list[LimitedList]
    _lower: bool
    previous: PipelineStart

    def __init__(self, previous: PipelineStart):
        super().__init__(previous, 0)
        self.thread_buffers = [LimitedList(26), LimitedList(26), LimitedList(26), LimitedList(26)]
        self._lower = False

    def forward(self) -> list[list[InstructionInfo]]:
        # take from up to two threads for decode
        index_add = int(self._lower)

        takentop = min(len(self.thread_buffers[index_add]), 3)
        takenlower = min(len(self.thread_buffers[2 + index_add]), 3)
        decode_instructions = [
            list(self.thread_buffers[index_add].pop(0) for _ in range(takentop)),
            list(self.thread_buffers[2 + index_add].pop(0) for _ in range(takenlower)),
        ]
        self._lower = not self._lower

        buffer_fill = self.previous.next_fetch_index
        if len(self.thread_buffers[buffer_fill]) < 26 - 8:
            self.thread_buffers[buffer_fill].extend(self.previous.forward()[buffer_fill])

        print(f"IFB stage passed {len(decode_instructions[0]) + len(decode_instructions[1])} instructions along")
        print(
            f"ifb status: t1: {len(self.thread_buffers[0])}, t2: {len(self.thread_buffers[1])} t3: {len(self.thread_buffers[2])} t4: {len(self.thread_buffers[3])}")
        return decode_instructions


class DecodePipeline:
    prev_dummy: Stage
    decode_unit: Stage
    crk_unit: Stage
    xfr_unit: Stage
    predispatch0_unit: Stage
    predispatch1_unit: Stage
    transfer_unit: Stage
    dispatch_unit: Stage

    class PreviousDummy(Stage):
        avail: list[InstructionInfo]

        def __init__(self):
            super().__init__(None, 0)
            self.avail = []

        def forward(self) -> list[InstructionInfo]:
            return self.avail

    def __init__(self):
        self.prev_dummy = DecodePipeline.PreviousDummy()
        self.decode_unit = Stage(self.prev_dummy, 3, name="Decode")
        self.crk_unit = Stage(self.decode_unit, 3, name="CRK")
        self.xfr_unit = Stage(self.crk_unit, 3, name="XFR")
        self.predispatch0_unit = Stage(self.xfr_unit, 3, name="PRED0")
        self.predispatch1_unit = Stage(self.predispatch0_unit, 3, name="PRED1")
        self.transfer_unit = Stage(self.predispatch1_unit, 3, name="XMIT")
        self.dispatch_unit = Stage(self.transfer_unit, 3, name="DISPATCH")

    def forward(self, new_inst: list[InstructionInfo]) -> list[InstructionInfo]:
        self.prev_dummy.avail = new_inst
        return self.dispatch_unit.forward()


class ExecPipeline:

    def forward(self, new_inst: list[InstructionInfo]) -> list[InstructionInfo]:
        pass


# TODO: support 128bit.

class IssueQueueStage(Stage):

    @property
    def max_add(self):
        return self.internal_content.max_size - len(self.internal_content)

    def __init__(self, size: int = 13, name: str = "IssueQueue"):
        super().__init__(None, size, name=name)

    def add_insts(self, insts: list[InstructionInfo]):
        assert len(insts) <= self.max_add

        self.internal_content.extend(insts)

    def forward(self) -> list[InstructionInfo]:
        return [self.internal_content.pop(0) for _ in range(min(len(self.internal_content), 4))]


class LSUPipeline:
    issue_queue: IssueQueueStage
    address_gen: Stage
    bdcs: Stage
    dacc: Stage
    fmt: Stage
    fin: Stage
    xmit: Stage

    def __init__(self):
        self.issue_queue = IssueQueueStage(name="LSU_IssueQueue")
        self.address_gen = Stage(self.issue_queue, 1)
        self.bdcs = Stage(self.address_gen, 1)
        self.dacc = Stage(self.bdcs, 1)
        self.fmt = Stage(self.dacc, 1)
        self.fin = Stage(self.fmt, 1)
        self.xmit = Stage(self.fin, 1)

    def forward(self) -> list[InstructionInfo]:
        res = self.xmit.forward()
        return res

    def issue(self, inst: InstructionInfo):
        self.issue_queue.add_insts([inst])


class FXPipeline:
    issue_queue: IssueQueueStage
    wb_stage: Stage
    ex_stage: Stage
    fin_stage: Stage
    xmit_stage: Stage

    def __init__(self):
        self.issue_queue = IssueQueueStage(name="FX_IssueQueue")
        self.wb_stage = Stage(None, 1)
        self.ex_stage = Stage(self.wb_stage, 1)
        self.fin_stage = Stage(self.ex_stage, 1)
        self.xmit_stage = Stage(self.fin_stage, 1)

    def issue(self, inst: InstructionInfo):
        self.issue_queue.add_insts([inst])

    def forward(self) -> list[InstructionInfo]:
        res = self.xmit_stage.forward()
        return res


class VSXPipeline:
    issue_stage: IssueQueueStage

    def forward(self, new_inst: list[InstructionInfo]) -> list[InstructionInfo]:
        res = self.issue_stage.forward()
        # todo
        return res

    def issue(self, inst: InstructionInfo):
        self.issue_stage.add_insts([inst])


class InternalSlice:
    fxpipe: FXPipeline
    vsx: VSXPipeline
    lsu: LSUPipeline

    def __init__(self):
        self.lsu = LSUPipeline()
        self.vsx = VSXPipeline()
        self.fxpipe = FXPipeline()

    def forward(self, instruct: Optional[InstructionInfo], lsop: Optional[InstructionInfo]) -> list[
        InstructionInfo]:
        res = []
        res += self.lsu.forward()
        res += self.vsx.forward()
        res += self.fxpipe.forward()

        match instruct:
            case InstructionInfo(inst=InstructionType.BRANCH, task=task):
                raise Exception("Branch must be issued to branch pipe")
            case InstructionInfo(inst=InstructionType.FX):
                self.fxpipe.issue(instruct)
            case InstructionInfo(inst=InstructionType.VSU):
                self.vsx.issue(instruct)
            case InstructionInfo(inst=InstructionType.NOP):
                self.fxpipe.issue(instruct)
            case InstructionInfo(inst=InstructionType.LSU):
                raise Exception("LSU must be added as lsop parameter")
            case _:
                raise Exception("Unknown instruction type")

        if lsop:
            self.lsu.issue(lsop)

        return res


class Pipeline:
    ifb: IFBStage
    decode_pipelines: list[DecodePipeline]
    slices: list[InternalSlice]
    branch_pipeline: BranchPipeline

    def __init__(self, tasks: list[Task]):
        self.ifb = IFBStage(PipelineStart(tasks))
        self.decode_pipelines = [DecodePipeline() for _ in range(2)]

    def tick(self):
        res = []
        ifb_forwards = self.ifb.forward()
        for i in range(2):
            res += self.decode_pipelines[i].forward(ifb_forwards[i])

        return res


def pipeline_tick(processor_state: ProcessorState, active_tasks: list[Task]):
    # possible inputs:
    # [Taks, None, None, None]
    # [Task, Task, None, None]
    # [Task, Task, Task, Task]
    assert len(active_tasks) == 4  # filled with None for inactive thread slots

    # HW threads:
    thread_one, thread_two, thread_three, thread_four = active_tasks
    assert thread_one is not None, "First thread must always be active"
    if not thread_two:
        thread_two = thread_one
    if not thread_three:
        thread_three = thread_one
    if not thread_four:
        thread_four = thread_two

    step_complete_instructions(processor_state)
    pass


def decode_pipeline(inst: list[InstructionType]) -> list[InstructionType]:
    pass
