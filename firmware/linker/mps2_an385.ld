/*
 * Linker Script for ARM Cortex-M3 (MPS2 AN385 Platform)
 * Memory layout: FLASH (4MB) and SRAM (4MB)
 */

ENTRY(Reset_Handler)

/* Memory Layout for MPS2 AN385 */
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x00000000, LENGTH = 4M
    RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 4M
}

/* Define Top of Stack (End of RAM) */
_estack = ORIGIN(RAM) + LENGTH(RAM);

/* Minimum stack and heap memory reservations */
_Min_Heap_Size  = 0x400; /* 1KB minimum heap */
_Min_Stack_Size = 0x800; /* 2KB minimum stack */

SECTIONS
{
    /* Vector Table and Executable Code (FLASH) */
    .text :
    {
        . = ALIGN(4);
        KEEP(*(.isr_vector)) /* Vector table */
        *(.text)             /* .text sections (code) */
        *(.text*)            /* .text* sections (code) */
        *(.glue_7)           /* glue arm to thumb code */
        *(.glue_7t)          /* glue thumb to arm code */
        *(.eh_frame)

        KEEP (*(.init))
        KEEP (*(.fini))

        . = ALIGN(4);
        _etext = .;          /* Global symbol at end of code */
    } > FLASH

    .ARM.extab :
    {
        *(.ARM.extab* .gnu.linkonce.armextab.*)
    } > FLASH

    .ARM.exidx :
    {
        __exidx_start = .;
        *(.ARM.exidx* .gnu.linkonce.armexidx.*)
        __exidx_end = .;
    } > FLASH

    /* Read-only data (Constants, Strings, TFLite Model Array) */
    .rodata :
    {
        . = ALIGN(4);
        *(.rodata)           /* .rodata sections */
        *(.rodata*)          /* .rodata* sections */
        . = ALIGN(4);
    } > FLASH

    /* C++ Constructors / Destructors Table */
    .preinit_array :
    {
        PROVIDE_HIDDEN (__preinit_array_start = .);
        KEEP (*(.preinit_array*))
        PROVIDE_HIDDEN (__preinit_array_end = .);
    } > FLASH

    .init_array :
    {
        PROVIDE_HIDDEN (__init_array_start = .);
        KEEP (*(SORT(.init_array.*)))
        KEEP (*(.init_array*))
        PROVIDE_HIDDEN (__init_array_end = .);
    } > FLASH

    .fini_array :
    {
        PROVIDE_HIDDEN (__fini_array_start = .);
        KEEP (*(SORT(.fini_array.*)))
        KEEP (*(.fini_array*))
        PROVIDE_HIDDEN (__fini_array_end = .);
    } > FLASH

    /* Initialized Data Section (Copied from FLASH to RAM at startup) */
    _sidata = LOADADDR(.data);

    .data :
    {
        . = ALIGN(4);
        _sdata = .;        /* Global symbol at data start */
        *(.data)           /* .data sections */
        *(.data*)          /* .data* sections */
        . = ALIGN(4);
        _edata = .;        /* Global symbol at data end */
    } > RAM AT > FLASH

    /* Uninitialized Data Section (BSS - Zero initialized at startup) */
    .bss :
    {
        . = ALIGN(4);
        _sbss = .;         /* Global symbol at bss start */
        __bss_start__ = _sbss;
        *(.bss)
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;         /* Global symbol at bss end */
        __bss_end__ = _ebss;
    } > RAM

    /* User Heap and Stack verification */
    ._user_heap_stack :
    {
        . = ALIGN(8);
        PROVIDE ( end = . );
        PROVIDE ( _end = . );
        . = . + _Min_Heap_Size;
        . = . + _Min_Stack_Size;
        . = ALIGN(8);
    } > RAM
}
