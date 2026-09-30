.syntax unified
.cpu cortex-m3
.thumb

.extern _estack
.extern _sidata
.extern _sdata
.extern _edata
.extern _sbss
.extern _ebss
.extern __libc_init_array
.extern main

.section .isr_vector, "a", %progbits
.balign 128
.global __Vectors
.type __Vectors, %object
__Vectors:
    .word _estack
    .word Reset_Handler
    .word Default_Handler
    .word Default_Handler
    .word Default_Handler
    .word Default_Handler
    .word Default_Handler
    .word 0
    .word 0
    .word 0
    .word 0
    .word Default_Handler
    .word Default_Handler
    .word 0
    .word Default_Handler
    .word Default_Handler
    .rept 32
    .word Default_Handler
    .endr
.size __Vectors, . - __Vectors

.section .text.Reset_Handler, "ax", %progbits
.thumb_func
.global Reset_Handler
.type Reset_Handler, %function
Reset_Handler:
    ldr r0, =_sidata
    ldr r1, =_sdata
    ldr r2, =_edata
1:
    cmp r1, r2
    bcs 2f
    ldr r3, [r0]
    str r3, [r1]
    adds r0, #4
    adds r1, #4
    b 1b
2:
    ldr r1, =_sbss
    ldr r2, =_ebss
    movs r3, #0
3:
    cmp r1, r2
    bcs 4f
    str r3, [r1]
    adds r1, #4
    b 3b
4:
    bl __libc_init_array
    bl main
5:
    b 5b
.size Reset_Handler, . - Reset_Handler

.section .text.Default_Handler, "ax", %progbits
.thumb_func
.global Default_Handler
.type Default_Handler, %function
Default_Handler:
    b .
.size Default_Handler, . - Default_Handler

.section .bss.__dso_handle, "aw", %nobits
.balign 4
.global __dso_handle
.type __dso_handle, %object
__dso_handle:
    .word 0
.size __dso_handle, 4

.section .text.runtime_stubs, "ax", %progbits
.thumb_func
.global _init
.type _init, %function
_init:
    bx lr
.size _init, . - _init

.thumb_func
.global _fini
.type _fini, %function
_fini:
    bx lr
.size _fini, . - _fini
