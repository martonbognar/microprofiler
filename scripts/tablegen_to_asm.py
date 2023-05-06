#!/usr/bin/env python3

import re

CONSTANT = "#0x1"
REGISTER = "r10"
DMEM_INDEXED = "42(r6)"
# DMEM_SYMBOLIC = "DMEM_ADDR"  # we do not care about this mode because it cannot address data memory
DMEM_ABSOLUTE = "&DMEM_ADDR"
DMEM_INDIRECT = "@r6"
DMEM_REG_INC = "@r6+"
IMMEDIATE = "#end_of_test"

JUMP_TARGET = "end_of_test"

IGNORE_LIST = ["BRCALL"]

MANUAL_OVERRIDES = {
    "B":        (["br"], 2),
    "Bm":       (["br 42(r7)"], 2),
    "CALLm":    (["call 42(r7)"], 2),
    "CALLn":    (["call @r7"], 1),
    "JCC":      ([f"jn {JUMP_TARGET}"], 1),
    "JMP":      ([f"jmp {JUMP_TARGET}"], 1),
    "MOVZX":    (["mov.b"], -2),
    "SEXT":     (["sxt"], -2),
    "ZEXT16r":  ([f"mov.b {REGISTER}, {REGISTER}"], 1),
}

def update_result(result, append):
    for i in range(len(result)):
        result[i] += append

def convert_asm(inst_id):
    if inst_id in MANUAL_OVERRIDES:
        return MANUAL_OVERRIDES[inst_id]

    match = re.match(r"^([A-Z]+)(\d*)([rmpicn]?)([rmpicn]?)", inst_id)
    if not match:
        raise "Unexpected format"

    opcode = match.group(1)
    if opcode in MANUAL_OVERRIDES:
        opcode = MANUAL_OVERRIDES[opcode][0][0]
    else:
        opcode = opcode.lower()

    bitlen = match.group(2)

    # a bit misleading, when there's only one operand it's actually the source, not the destination
    destination = match.group(3)
    source = match.group(4)

    result = [opcode]
    if bitlen == '8':
        update_result(result, ".b")
    # elif bitlen == '16':
    #     update_result(result, ".w"

    length = 1

    if source == 'r':
        update_result(result, f" {REGISTER},")
    if source == 'm':
        orig = len(result)
        for i in range(orig):
            temp = result[i]
            result[i] += f" {DMEM_INDEXED},"
            temp += f" {DMEM_ABSOLUTE},"
            result.append(temp)
        length += 1
    if source == 'n':
        update_result(result, f" {DMEM_INDIRECT},")
    if source == 'p':
        update_result(result, f" {DMEM_REG_INC},")
    if source == 'c':
        update_result(result, f" {CONSTANT},")
    if source == 'i':
        update_result(result, f" {IMMEDIATE},")
        length += 1

    if destination == 'r':
        update_result(result, f" {REGISTER}")
    if destination == 'm':
        orig = len(result)
        for i in range(orig):
            temp = result[i]
            result[i] += f" {DMEM_INDEXED}"
            temp += f" {DMEM_ABSOLUTE}"
            result.append(temp)
        length += 1
    if destination == 'n':
        update_result(result, f" {DMEM_INDIRECT}")
    if destination == 'p':
        update_result(result, f" {DMEM_REG_INC}")
    if destination == 'c':
        update_result(result, f" {CONSTANT}")
    if destination == 'i':
        update_result(result, f" {IMMEDIATE}")
        length += 1
    return (result, length)

def generated_instructions(tablegen_file):
    with open(tablegen_file) as file:
        lines = file.readlines()
        instructions = []
        for line in lines:
            match = re.match(r"^\/\*\s+(\d+)\*\/\s+{(\d+),\s\d+,\s\d+},\s\/\/\s\w+::(\w+)$", line)
            if match and int(match.group(2)) != 2 ** 32 - 1:
                if not any([match.group(3).startswith(ignored) for ignored in IGNORE_LIST]):
                    (asms, len) = convert_asm(match.group(3))
                    for asm in asms:
                        instructions.append({"id": int(match.group(1)), "short": match.group(3), "asm": asm, "len": len})
        return instructions

if __name__ == '__main__':
    print(generated_instructions())
