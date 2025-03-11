from typing import Callable, Iterator

from simulation.state import ProcessorState
from simulation.tasks import Task, InstructionType
from simulation.runqueue import RunQueue
from simulation import TimeQuantum, CLOCK_CYCLES_PER_TIME_QUANTUM


def pop_run_instructions_from_tasks(tasks: list[Task]) -> None:
    for task in tasks:
        task.remaining_instructions.pop(0)


def pipeline_run_for_quantum(
        processor_state: ProcessorState,
        tasks: list[Task],
        quantum: TimeQuantum,
):
    processor_state.clear_pipeline()
    assert processor_state.time_quantum == quantum
    for tick in processor_state.cycles():
        pipeline_tick(processor_state, tasks)

    processor_state.advance_quantum()


def run_simulation_to_exhaustion(
        tasks: list[tuple[TimeQuantum, Task]],
        scheduling_algorithm: Callable[[RunQueue], list[Task]],
) -> dict[TimeQuantum, list[Task]]:
    run_queue = RunQueue(
        list(map(lambda t: t[1], filter(lambda t: t[0] == 0, tasks))))  # initialise with tasks arriving at start
    run_order = {}

    quantum = 0
    while not run_queue.is_empty():
        scheduled_tasks = scheduling_algorithm(run_queue)
        quantum_smt = len(scheduled_tasks)
        print(f"quantum {quantum} smt {quantum_smt}")
        for task in scheduled_tasks:
            task.instructions.pop(0)
            if len(task.instructions) == 0:
                print(f"completed task {task.id} at quantum {quantum}")
                task.mark_completed(quantum)

        run_order[quantum] = scheduled_tasks

        quantum += 1
        new_tasks = filter(lambda t: t[0] == quantum, tasks)
        for _, task in new_tasks:
            run_queue.add_task(task)

        for task in scheduled_tasks:

            task.ran_at.append(quantum)
            if not task.is_complete():
                run_queue.add_task(task)

    return run_order
