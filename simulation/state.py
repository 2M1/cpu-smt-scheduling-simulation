from simulation.tasks import InstructionType, TimeQuantum
from simulation import CLOCK_CYCLES_PER_TIME_QUANTUM

from dataclasses import dataclass, field
from typing import Iterator


class LimitedList(list):
    max_size: int

    def __init__(self, max_size: int):
        super().__init__([])
        self.max_size = max_size

    def append(self, __object):
        if self.max_size == len(self):
            return False
        super().append(__object)

    def get_equal_partition(self, part_nr: int, smt_size: int) -> list:
        assert part_nr in (0, 1)
        assert smt_size in (1, 2, 4)

        # result should not be modified.
        return self[part_nr * smt_size:(part_nr + 1) * smt_size]


@dataclass
class ProcessorState:
    time_quantum: TimeQuantum = 0
    cycles_left: int = CLOCK_CYCLES_PER_TIME_QUANTUM
    last_fetch_index: int = 0

    ifb: list[InstructionType] = field(default_factory=lambda: LimitedList(96))
    issue_queues: list[list[InstructionType]] = field(default_factory=lambda: [LimitedList(26), LimitedList(26)])

    def advance_quantum(self):
        # TODO:
        self.cycles_left = CLOCK_CYCLES_PER_TIME_QUANTUM
        self.time_quantum += 1

    def clear_pipeline(self):
        # does not consume time.
        self.ifb.clear()
        for queue in self.issue_queues:
            queue.clear()

    def cycles(self) -> Iterator[int]:
        for i in range(self.cycles_left):
            self.cycles_left -= 1
            yield i
