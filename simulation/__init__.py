import os

N_THREADS = int(os.getenv("N_THREADS", 8))

type TimeQuantum = int

CLOCK_CYCLES_PER_TIME_QUANTUM = 10
