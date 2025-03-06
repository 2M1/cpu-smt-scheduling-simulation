#!/usr/bin/env python
from pathlib import Path
from typing import List, Dict


def load_elf(filename: Path, thread_entries: Dict[str, int]):
    """
    loads an ppc64le elf file and extracts all thread functions into 

    :param filename:
    :param thread_entries:
    :return:
    """
