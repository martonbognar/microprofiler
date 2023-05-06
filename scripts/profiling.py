#!/usr/bin/env python3

import argparse
import os
from enum import Enum
from tablegen_to_asm import generated_instructions
from classes import CLASSES


class Parser(Enum):
    SKIP = 1
    FIND_LAST = 2
    IN_LAST = 3
    LAST_DONE = 4
    IN_TARGET = 5
    PAST_TARGET = 6

def copy_stimulus(SNCSIM_DIR):
    os.system(f"cp classifier.v {SNCSIM_DIR}/core/sim/rtl_sim/src/sancus/classifier.v")


def generate_asm(inst):
    with open("template.asm") as template:
        lines = [line if "%instruction%" not in line else inst +
                 "\n" for line in template]
        return lines


def write_testfile(asm, SNCSIM_DIR):
    bench = open(
        f"{SNCSIM_DIR}/core/sim/rtl_sim/src/sancus/classifier.s43", "w", buffering=1)
    bench.writelines(asm)
    bench.flush()
    bench.close()


def run_testfile(SNCSIM_DIR):
    # TODO: if not success, abort
    os.system(
        f"cd {SNCSIM_DIR}/core/sim/rtl_sim/run; ./run sancus/classifier > /dev/null")


def create_trace(SNCSIM_DIR, VCDCAT_DIR):
    os.system(f"{VCDCAT_DIR}/vcdcat --exact {SNCSIM_DIR}/core/sim/rtl_sim/run/tb_openMSP430.vcd tb_openMSP430.mclk tb_openMSP430.inst_full tb_openMSP430.dut.mem_backbone_0.eu_pmem_en tb_openMSP430.dut.mem_backbone_0.fe_pmem_en tb_openMSP430.dut.mem_backbone_0.eu_dmem_en tb_openMSP430.dut.mem_backbone_0.per_en tb_openMSP430.exec_done > trace.txt")


def parse_trace():
    state = Parser.SKIP
    LAST_INST = "4d4f560020234e2c207237"

    PMEM_TRACE = []
    DMEM_TRACE = []
    MMIO_TRACE = []

    with open("trace.txt") as trace:
        lines = trace.readlines()
        for (idx, line) in enumerate(lines):
            if state == Parser.SKIP:
                if line.startswith("==="):
                    state = Parser.FIND_LAST
                continue
            if idx % 2 == 0:
                continue
            if state == Parser.FIND_LAST:
                if line.split()[2] == LAST_INST:
                    state = Parser.IN_LAST
                continue
            if state == Parser.IN_LAST:
                if line.split()[9] == '1':
                    state = Parser.IN_TARGET
                continue
            if state == Parser.IN_TARGET:
                PMEM_TRACE.append('1' if line.split()[
                                  3] == '1' or line.split()[4] == '1' else '0')
                DMEM_TRACE.append('1' if line.split()[6] == '1' else '0')
                MMIO_TRACE.append('1' if line.split()[8] == '1' else '0')
                if line.split()[9] == '1':
                    state = Parser.PAST_TARGET
                continue
            if state == Parser.PAST_TARGET:
                break
    return "".join(PMEM_TRACE) + "|" + "".join(DMEM_TRACE) + "|" + "".join(MMIO_TRACE)


def generate_all(args):
    table = generated_instructions(args.tablegen)
    clean_ret = {}
    for item in table:
        test = generate_asm(item["asm"])
        write_testfile(test, args.sancus_core)
        run_testfile(args.sancus_core)
        create_trace(args.sancus_core,  args.vcdvcd)
        trace = parse_trace()
        no_dummy = {"number": 999, "dummy": "XXX"}
        dummy = CLASSES[trace] if trace in CLASSES else no_dummy
        clean_ret[item["id"]] = {
            "llvm": item["short"], "trace": trace, "dummy": dummy}
        print({**item,  **{'trace': trace, 'dummy': dummy}})
    return clean_ret


def find_optimized_0_index_dummy(instr, output):
    if instr.endswith("m"):
        optimized_llvm = instr[:-1] + "n"
        for iden in output:
            if output[iden]["llvm"] == optimized_llvm:
                return output[iden]["dummy"]["number"]
    return 999


def print_result(output):
    dummy_ids = [(0, 999)] * (max(iden for iden in output) + 1)
    for iden in output:
        dummy_ids[iden] = (output[iden]["dummy"]["number"],
                           find_optimized_0_index_dummy(output[iden]["llvm"], output))
    print(dummy_ids)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Run the profiling step for all instructions.')
    parser.add_argument('sancus_core',
                        help="Directory of sancus-core")
    parser.add_argument('vcdvcd',
                        help="Directory of the vcdvcd installation")
    parser.add_argument('tablegen',
                        help="Path to the raw tablegen file")
    parser.add_argument(
        '-llvm', help="If set, output will include pairs of dummy identifiers used during building the compiler")
    args = parser.parse_args()

    if args.sancus_core[-1] == '/':
        args.sancus_core = args.sancus_core[:-1]

    if args.vcdvcd[-1] == '/':
        args.vcdvcd = args.vcdvcd[:-1]

    copy_stimulus(args.sancus_core)

    output = generate_all(args)
    if args.llvm:
        print_result(output)
