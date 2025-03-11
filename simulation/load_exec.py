#!/usr/bin/env python
import re
import sys
from pathlib import Path
from typing import List, Dict, Optional, Iterator
from collections import OrderedDict

from simulation.tasks import InstructionType, Task, TaskCategory, BranchInstruction, Instruction

type InstructionMap = OrderedDict[int, tuple[str, str, str]]
type FunctionMap = OrderedDict[str, int]


def _get_index_of_addr(addr: int, instructions: InstructionMap) -> int:
    for i, (a, _) in enumerate(instructions.items()):
        if a == addr:
            return i
    raise ValueError(f"Could not find instruction at address {addr}")


def _calculate_instruction_index_offset(addr: int, target: int, inst_map: InstructionMap) -> int:
    rel_index = 0
    found = False

    if target < addr:
        inst_map_iter = iter(reversed(inst_map.items()))
        # skip to current instruction
        for a, _ in inst_map_iter:
            if addr == a:
                break
        for a, (inst, _, _) in inst_map_iter:
            rel_index -= 1
            if a == target:
                found = True
                break
    else:  # look forward
        inst_map_iter = iter(inst_map.items())
        # skip to current inst
        for a, _ in inst_map_iter:
            if addr == a:
                break

        for a, (inst, _, _) in inst_map_iter:
            rel_index += 1
            if a == target:
                found = True
                break

    if not found:
        raise ValueError(f"Could not find target instruction {target} in instruction map")
    return rel_index


def parse_branch_instruction(inst_str: str, addr: int, metadata: str, args: str,
                             inst_map: OrderedDict[int, tuple[str, str, str]]) -> BranchInstruction:
    if inst_str in ("b", "bl", "blt", "beq", "bne", "bgt"):
        target = int(args[0], 16)
        relative = _calculate_instruction_index_offset(addr, target, inst_map)
        if metadata:
            type, n = metadata.split(':')
            n = int(n)
            if type == 'u':
                return BranchInstruction.branch_until(n, relative)
            elif type == 'f':
                return BranchInstruction.branch_after(n, relative)

        return BranchInstruction.branch_prob(1.0, relative)

    if inst_str in ("blr",):
        # function return
        return BranchInstruction.ret()

    if inst_str in ("cmp", "cmpi", "cmpdi"):
        return BranchInstruction.compare()

    return BranchInstruction.branch_prob(0.0, 0)


def _not_relevant(inst: str) -> bool:
    return map_instruction(inst) is None


def create_address_maps(lines: List[str]) -> tuple[InstructionMap, FunctionMap]:
    instructions = OrderedDict()
    functions = OrderedDict()

    for line in lines:
        if line[0].isdigit():
            # function start:
            base_addr = int(line.split()[0], 16)
            m = re.search('<(.+?)>', line)
            if not m: continue
            name = m.group(1)

            functions[name] = base_addr
        elif line.isspace():
            continue
        else:
            parts = line.strip().split('\t')
            address = int(parts[0].replace(':', ''), 16)
            inst, *args = parts[2].split()
            if _not_relevant(inst): continue
            metadata = parts[3] if len(parts) > 3 else ""
            instructions[address] = (inst, args, metadata)

    return instructions, functions


def load_exec_dump(file: Path, thread_entries: Dict[str, int]) -> list[Task]:
    """
    loads an ppc64le elf file and extracts all thread functions into

    :param filename:
    :param thread_entries:
    :return:
    """

    with open(file, "r") as f:
        lines = f.readlines()

        # first pass: create map of all addresses.
        instructions, functions = create_address_maps(lines)

        task_instructions = []
        # second pass: create instruction instances
        for address, (inst, args, metadata) in instructions.items():
            match map_instruction(inst):
                case InstructionType.BRANCH:
                    task_instructions.append(parse_branch_instruction(inst, address, metadata, args, instructions))
                case InstructionType.NOP:
                    task_instructions.append(Instruction(InstructionType.NOP))
                case other:
                    if other is None: continue
                    task_instructions.append(Instruction(other))

        print(task_instructions)

    tasks = []
    i = 1
    for fname, count in thread_entries.items():
        index = _get_index_of_addr(functions[fname], instructions)
        tasks.extend((
                         Task(
                             i, TaskCategory.FX, task_instructions, inst_index=index,
                             fname=fname
                         )
                     ) for i in range(i, count + 1))  # +1 since ids start from 1
        i += count

    return tasks


def map_instruction(inst: str) -> Optional[InstructionType]:
    if inst.startswith((
            "add", "sub", "mul", "div", "rl", "or", "xor", "nand", "and", "clrrdi", "clrldi",
            "sld", "slw", "sr", "ext",
    )):
        return InstructionType.FX

    if inst.startswith((
            "b", "cmp"
    )):
        return InstructionType.BRANCH

    if inst.startswith((
            "l", "st",
    )):
        return InstructionType.LSU

    if inst in ("sc", "tw", "twi", "td", "tdi", "sync", "isync", "tlbsync", "tlbie", "rfi"):
        # ignore syscalls for now.
        return None

    if inst in (
            'mflr', 'mtxer', 'mtctr', 'mr', 'mtlr'
    ):
        return InstructionType.FX

    if inst.startswith((
            "mtf", "mff"
    )):
        return InstructionType.VSU  # access to FP registers
    if inst == "nop":
        return InstructionType.NOP

    if inst in (".long",):
        return None  # data or nop

    if inst.startswith((
            "f"
    )):
        return InstructionType.VSU

    print(f"Unknown instruction type {inst}", file=sys.stderr)
    return None
