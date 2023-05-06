FROM ubuntu:20.04

# Config parameters
ARG BUILD_SECURITY=64
ARG BUILD_KEY=deadbeefcafebabe
ENV SANCUS_SECURITY=$BUILD_SECURITY
ENV SANCUS_KEY=$BUILD_KEY

################################################################################
## 1. Install dependencies
################################################################################

RUN apt-get update -yqq && \
    apt-get -yqq install build-essential git lsb-release sloccount sudo vim verilator && \
    echo "Europe/Brussels" > /etc/timezone && \
    DEBIAN_FRONTEND=noninteractive apt-get install -yqq tzdata

########################################
## 1.1. SLLVM + Sancus
########################################
WORKDIR /sllvm

RUN git clone --branch dma-attack https://github.com/hanswinderix/sllvm . && make install-deps && make fetch && make configure

WORKDIR /sllvm/sancus-main/sancus-core
RUN git checkout dma-attack

WORKDIR /sllvm
RUN make install && rm -rf build

################################################################################
## 1.1.1. Run case study attacks with the peripheral and untrusted C code
################################################################################

WORKDIR /sllvm/test/sancus/bsl
RUN make -f Makefile.attacker && make -f Makefile.attacker sim

WORKDIR /sllvm/test/sancus/mulhi3
RUN make -f Makefile.attacker && make -f Makefile.attacker sim

################################################################################
## 1.1.2. Run mitigation evaluation for Nemesis
################################################################################

WORKDIR /sllvm
RUN make checkout-master && make -C test/sancus nemdef-pp

WORKDIR /benchmarks-nemesis
RUN cp -r /sllvm/test/sancus/* /benchmarks-nemesis

# Get TableGen description used for profiling
RUN /sllvm/install/bin/llvm-tblgen -I /sllvm/sllvm/llvm/lib/Target/MSP430/ -I /sllvm/sllvm/llvm/include/ -gen-msp430-latency-info /sllvm/sllvm/llvm/lib/Target/MSP430/MSP430.td >tablegen_raw.txt

################################################################################
## 1.1.3. Run mitigation evaluation for DMA
################################################################################

WORKDIR /sllvm
RUN make -C test/sancus nemdef-clean && make checkout-dma-attack && make configure && make install && make -C test/sancus nemdef-pp && rm -rf build

WORKDIR /benchmarks-dma
RUN cp -r /sllvm/test/sancus/* /benchmarks-dma

########################################
## 1.2. VCDVCD
########################################
WORKDIR /vcdvcd

RUN git clone https://github.com/cirosantilli/vcdvcd .
RUN python3 -m pip install --user /vcdvcd

########################################
## 1.3. SCF-MSP
########################################
WORKDIR /scf-msp430-dma

RUN git clone https://github.com/jovanbulck/scf-msp430-dma.git . && apt-get install -yqq graphviz && pip3 install -r requirements.txt

########################################
## 1.4. Profiling scripts
########################################
WORKDIR /profiling

COPY scripts/* ./

################################################################################
## 2. Reproduce attack case studies
################################################################################

WORKDIR /sllvm/sancus-main/sancus-core/core/sim/rtl_sim/run
RUN __SANCUS_SIM=1 ./run sancus/dma_covert

WORKDIR /profiling
RUN ./attacker.py bsl /benchmarks-nemesis/bsl/bsl.nemdef.vcd
RUN ./attacker.py mul /benchmarks-nemesis/mulhi3/mulhi3.nemdef.vcd
RUN ./attacker.py covert /sllvm/sancus-main/sancus-core/core/sim/rtl_sim/run/tb_openMSP430.vcd

################################################################################
## 3. Run microarchitectural profiling
################################################################################

WORKDIR /profiling
RUN ./profiling.py /sllvm/sancus-main/sancus-core /vcdvcd /benchmarks-nemesis/tablegen_raw.txt

################################################################################
## 4. Run security validation
################################################################################

WORKDIR /scf-msp430-dma
# clean up built-in benchmarks
RUN rm testcase/*.nemdef testcase/*.vulnerable

RUN cp /benchmarks-nemesis/*/[a-z]*.vulnerable testcase/
RUN cp /benchmarks-nemesis/*/[a-z]*.nemdef testcase/

RUN ./run_all_nemdef.sh --minimal

RUN cp /benchmarks-dma/*/[a-z]*.vulnerable testcase/
RUN cp /benchmarks-dma/*/[a-z]*.nemdef testcase/

RUN ./run_all_nemdef.sh --minimal

################################################################################
## 5. Interactive Docker container with fully built and validated pipeline
################################################################################

# Display a welcome message for interactive sessions
RUN echo '[ ! -z "$TERM" -a -r /etc/motd ] && cat /etc/motd' \
    >> /etc/bash.bashrc ; echo "\
    ========================================================================\n\
    = MicroProfiler Docker container                                       =\n\
    ========================================================================\n\
    `lsb_release -d`\n\
    \n" > /etc/motd

WORKDIR /
CMD /bin/bash
