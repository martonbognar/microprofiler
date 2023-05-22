# MicroProfiler: Principled Side-Channel Mitigation through Microarchitectural Profiling

This repository contains the programs developed as part of our [MicroProfiler](https://mici.hu/papers/bognar23microprofiler.pdf) paper.

```
@inproceedings{bognar23microprofiler,
  author    = {Bognar, Marton and Winderix, Hans and {Van Bulck}, Jo and Piessens, Frank},
  title     = {MicroProfiler: Principled Side-Channel Mitigation through Microarchitectural Profiling},
  year      = {2023},
  booktitle = {8th IEEE European Symposium on Security and Privacy (EuroS\&P 23)},
  publisher = {IEEE},
  month     = jul
}
```

All tools and experiments are bundled into a Docker container for convenience, but can of course also be run separately.
As such, the only prerequisite is to have [Docker](https://docs.docker.com/engine/install/) installed on your system.
The container can be built with `make docker-build` and run with `make docker-run`.
Building the container takes about 6 hours and requires 10 GB of disk space.

The rest of this document describes the components of the Docker container, with references to the build steps outlined in the [Dockerfile](./Dockerfile).

## Profiling step

The main script to perform the microarchitectural profiling is `scripts/profiling.py`.
Inside the container, this is copied to `/profiling/profiling.py` and ran in step 3, with as input the raw TableGen generated list of instructions (and some paths for running the simulations and the vcdvcd extraction tool):
```
cd /profiling
./profiling.py /sllvm/sancus-main/sancus-core /vcdvcd /benchmarks-nemesis/tablegen_raw.txt
```

The expected output is a list of profiled instructions with their memory traces and assigned dummies:
```
...
{'id': 550, 'short': 'SUBC8rr', 'asm': 'subc.b r10, r10', 'len': 1, 'trace': '1|0|0', 'dummy': {'number': 1, 'dummy': 'BIC16rc', 'asm': 'bic #1, r3'}}
{'id': 551, 'short': 'SWPB16m', 'asm': 'swpb 42(r6)', 'len': 2, 'trace': '1001|0101|0000', 'dummy': {'number': 41, 'dummy': 'SWPB16m', 'asm': 'swpb &dummy'}}
{'id': 551, 'short': 'SWPB16m', 'asm': 'swpb &DMEM_ADDR', 'len': 2, 'trace': '1001|0101|0000', 'dummy': {'number': 41, 'dummy': 'SWPB16m', 'asm': 'swpb &dummy'}}
...
```

## Compiler mitigation for Nemesis + DMA side channel

Our extended LLVM compiler and its benchmarks can be found [in a separate repository](https://github.com/hanswinderix/sllvm/tree/dma-attack).
Inside the container, the compiler is first built (`/sllvm`) with just the Nemesis mitigation to reproduce its benchmarks (steps 1.1. and 1.1.2.), then with the combined mitigation (step 1.1.3.).

The benchmark results are copied to `/benchmarks-nemesis` and `/benchmarks-dma`, and can be viewed in e.g., `/benchmarks-dma/results/synthetic.txt`.

```
$ cat /benchmarks-nemesis/results/synthetic.txt
----------------------------------------------------------------------------------------------------
Benchmark               Baseline                               Overhead of balancing
---------         -----------------------          -------------------------------------------------
                  Size     Execution Time          Size       Execution Time          Execution Time
                 (bytes)      (cycles)                                                (longest path)

call               300    112,   91                1.09x   1.05x, 1.30x                  1.05x
diamond            282    102,  101,  103          1.16x   1.13x, 1.14x, 1.12x           1.12x
fork               262     90,   91                1.06x   1.07x, 1.05x                  1.05x
ifcompound         382    370,  371,  372          1.06x   1.02x, 1.02x, 1.02x           1.02x
ifthenloop         282    143,   96                1.28x   1.19x, 1.77x                  1.19x
...
```

## Attacks

The script `scripts/attacker.py` can analyze the memory activity of the simulations and reconstruct the secret leakage based on it (step 2).

```shell
RUN ./attacker.py bsl /attacks/bsl.nemdef.vcd
RUN ./attacker.py mul /attacks/mulhi3.nemdef.vcd
```

Expected output:

```
./attacker.py bsl /attacks/bsl.nemdef.vcd
Starting attack...
✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓
Starting attack...
✓ ✓ ✘ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓ ✓
Starting attack...
✓ ✓ ✘ ✓ ✓ ✓ ✓ ✘ ✘ ✓ ✓ ✓ ✓ ✓ ✓ ✓
Starting attack...
✓ ✓ ✘ ✓ ✓ ✓ ✓ ✘ ✘ ✓ ✘ ✘ ✓ ✓ ✓ ✓
```

The covert channel demonstration can be run with
```shell
__SANCUS_SIM=1 /sllvm/sancus-main/sancus-core/core/sim/rtl_sim/run/run sancus/dma_covert
/profiling/attacker.py covert /sllvm/sancus-main/sancus-core/core/sim/rtl_sim/run/tb_openMSP430.vcd
```

Additionally, the two case study attacks on the hardened benchmark programs can be conducted using the peripheral, controlled from untrusted C code (step 1.1.1.).
```shell
cd /sllvm/test/sancus/bsl
make -f Makefile.attacker
make -f Makefile.attacker sim

cd /sllvm/test/sancus/mulhi3
make -f Makefile.attacker
make -f Makefile.attacker sim
```

Important to note, these attack demonstrations require the Nemesis-only mitigation to be compiled on the system, which is overwritten by the DMA+Nemesis mitigation during later stages of the Docker build process.
To recompile the Nemesis mitigation, run `cd /sllvm && make checkout-master && make install`.

## Static analysis

The source code for the extended SCF-MSP tool can also be found in a [separate repository](https://github.com/jovanbulck/scf-msp430-dma).
In the container, the analysis is performed for binaries compiled by the original Nemesis mitigation, as well as for our extended DMA+Nemesis mitigation (step 4).
The example of running the analysis for the binaries compiled by the combined mitigation is shown below:

```shell
cd /scf-msp430-dma
cp /benchmarks-dma/*/[a-z]*.vulnerable testcase/
cp /benchmarks-dma/*/[a-z]*.nemdef testcase/

./run_all_nemdef.sh
```

Expected output (running for the only-Nemesis-hardened benchmarks):
```
                testcase/bsl.nemdef.json	Architectural 🗲
               testcase/call.nemdef.json	DMA 🗲
            testcase/diamond.nemdef.json	Architectural 🗲
               testcase/fork.nemdef.json	Architectural 🗲
         testcase/ifcompound.nemdef.json	Architectural 🗲
         testcase/ifthenloop.nemdef.json	DMA 🗲
       testcase/ifthenloopif.nemdef.json	DMA 🗲
     testcase/ifthenlooploop.nemdef.json	DMA 🗲
 testcase/ifthenlooplooptail.nemdef.json	DMA 🗲
           testcase/indirect.nemdef.json	Architectural 🗲
             testcase/keypad.nemdef.json	DMA 🗲
            testcase/kruskal.nemdef.json	Recursion exception!
               testcase/loop.nemdef.json	Success
             testcase/modexp.nemdef.json	Nemesis 🗲
             testcase/mulhi3.nemdef.json	DMA 🗲
            testcase/mulmod8.nemdef.json	DMA 🗲
          testcase/multifork.nemdef.json	Architectural 🗲
         testcase/sharevalue.nemdef.json	DMA 🗲
           testcase/switch16.nemdef.json	DMA 🗲
            testcase/switch8.nemdef.json	DMA 🗲
           testcase/triangle.nemdef.json	Architectural 🗲
```
