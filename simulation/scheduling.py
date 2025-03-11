from simulation.tasks import Task, TaskCategory
from simulation.runqueue import RunQueue
from simulation import N_THREADS as SMT_MAX


def round_robin_smt4(run_queue: RunQueue) -> list[Task]:
    assert not run_queue.is_empty()

    return run_queue.pop_n_tasks(SMT_MAX)


def slot_fill_shed(run_queue: RunQueue) -> list[Task]:
    assert not run_queue.is_empty()

    if len(run_queue) < 2:
        return run_queue.pop_task()

    run_queue.reset_indices()
    top = run_queue.pop_task()[0]
    remaining = SMT_MAX - top.category.value.slots_filled
    print(f"Top task {top.id} width {top.category.value.slots_filled} means {remaining} slots remaining")
    selected = [None] * SMT_MAX
    if remaining <= 1:
        return [top] # no more room
    elif remaining == 2:
        # must select a single thread with size two
        last = run_queue.peek_task()[0]
        index = len(run_queue.tasks) - 2
        while last.category.value.slots_filled != 2:
            if index < 0:
                # only tasks with slot-width 1 remaining, pick the most current one
                return [top, run_queue.pop_task()[0]]
            last = run_queue.tasks[index]
            index -= 1

        run_queue.tasks.remove(last)
        return [top, last]
    else: # remaining = 3: Select 3 threads with width 1 or one with 1 and fill remainder
        selected = []
        while len(selected) < 3:

            last = run_queue.peek_prev_single_width()
            if last is None:
                break

            selected.append(last)

        if len(selected) < 3:
            # search for a task with width two to fill the slot:
            if len(selected) == 2:
                # fill with any remaining:
                while last := run_queue.peek_prev():
                    if last is None:
                        break

                    if last not in selected:
                        selected.append(last)
                        break

                if len(selected) == 2:
                    # only three tasks remaining, can only run two at a time.
                    # remove last added task since we cannot run 3
                    selected.pop()

        for task in selected:
            run_queue.tasks.remove(task)

        selected.insert(0, top)
        return selected


def even_slot_scheduling(run_queue: RunQueue) -> list[Task]:
    assert not run_queue.is_empty()
    if len(run_queue) == 1:
        return run_queue.pop_task()

    penalties = {
       TaskCategory.MEM: [0, 1],
       TaskCategory.IO: [],
    }
    # calculates
