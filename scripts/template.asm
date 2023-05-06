.include "pmem_defs.asm"
.include "sancus_macros.asm"

.set MMIO_ADDR, (0x0090)
.set DMEM_ADDR, DMEM_200
.set STACK, DMEM_240
.set PMEM_ADDR, end_of_test

.global main
main:
    clr r15
    mov #STACK, r1
    mov #PMEM_ADDR, r10
    mov #PMEM_ADDR, &DMEM_ADDR
    mov #MMIO_ADDR, r5
    mov #DMEM_ADDR, r6
    mov #PMEM_ADDR, r7

    %instruction%

    /* ----------------------         END OF TEST        --------------- */
end_of_test:
	mov #0x2000, r15
    br #0xffff

.section .vectors, "a"
.word end_of_test  ; Interrupt  0 (lowest priority)    <unused>
.word end_of_test  ; Interrupt  1                      <unused>
.word end_of_test  ; Interrupt  2                      <unused>
.word end_of_test  ; Interrupt  3                      <unused>
.word end_of_test  ; Interrupt  4                      <unused>
.word end_of_test  ; Interrupt  5                      <unused>
.word end_of_test  ; Interrupt  6                      <unused>
.word end_of_test  ; Interrupt  7                      <unused>
.word end_of_test  ; Interrupt  8                      <unused>
.word end_of_test  ; Interrupt  9                      TEST IRQ
.word end_of_test  ; Interrupt 10                      Watchdog timer
.word end_of_test  ; Interrupt 11                      <unused>
.word end_of_test  ; Interrupt 12                      <unused>
.word end_of_test  ; Interrupt 13                      SM_IRQ
.word end_of_test  ; Interrupt 14                      NMI
.word main         ; Interrupt 15 (highest priority)   RESET
