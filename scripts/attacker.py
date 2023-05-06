#!/usr/bin/env python3

import vcdvcd
import argparse


def extract_bsl(trace):
    index = 52
    y = ""
    for _ in range(16):
        if trace[index] == '1':
            y += "✓ "
        else:
            y += "✘ "
        index += 61
    print(y)


def extract_y(trace):
    index = 77
    y = ""
    for _ in range(16):
        if trace[index] == '1':
            y = y.rjust(16, '0')
            break
        index += 2
        if trace[index] == '1':
            y = '0' + y
        else:
            y = '1' + y
        index += 78
    print("y =", str(int(y, 2)))


def extract_covert(trace):
    index = 14
    for _ in range(4):
        word = ''
        for _ in range(16):
            if trace[index] == '0':
                word = '0' + word
                index += 9
            else:
                word = '1' + word
                index += 12
        print(hex(int(word, 2)))
        index += 9


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Extract leakage from a vcd file.')

    parser.add_argument(
        'attack',
        help='the attack to perform',
        choices=['bsl', 'mul', 'covert'],
    )

    parser.add_argument('vcd', help="Path to the VCD file")
    args = parser.parse_args()

    clk = "TOP.tb_openMSP430.dut.mclk" if args.attack != "covert" else "tb_openMSP430.dut.mclk"
    mem_cen = "TOP.tb_openMSP430.dut.mem_backbone_0.pmem_cen" if args.attack != "covert" else "tb_openMSP430.dut.mem_backbone_0.dmem_cen"
    pc = "TOP.tb_openMSP430.dut.current_inst_pc[15:0]" if args.attack != "covert" else "tb_openMSP430.dut.current_inst_pc[15:0]"

    vcd = vcdvcd.VCDVCD(args.vcd)

    def collect(start_pc, period, extract):
        mems = []
        counter = 0

        for t, v in [(t, int(v, 2)) for (t, v) in vcd[clk].tv]:
            if v == 1:
                try:
                    curr_pc = int(vcd[pc][t], 2)
                except ValueError:
                    continue
                # rising clock
                pmem = int(vcd[mem_cen][t], 2)
                if curr_pc == int(start_pc, 16) and counter == 0:
                    print("Starting attack...")
                    mems = [1 if pmem == 0 else 0]
                    counter += 1
                if counter != 0:
                    mems.append(1 if pmem == 0 else 0)
                    counter += 1
                    if counter == period:
                        counter = 0
                        extract("".join([str(x) for x in mems]))

    if args.attack == "bsl":
        collect("8162", 1100, extract_bsl)

    if args.attack == "mul":
        collect("8186", 1300, extract_y)

    if args.attack == "covert":
        collect("5c02", 750, extract_covert)
