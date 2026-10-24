.text
.base:
.org 0x10000
.globl synthetic_switch
.type synthetic_switch,@function
synthetic_switch:
    stdu 1,-32(1)
    std 31,16(1)
    cmplwi 3,2
    bgt .default
    lwz 11,0(2)
    slwi 9,3,2
    lwzx 0,9,11
    extsw 0,0
    add 0,0,11
    mtctr 0
    bctr
.table:
    .long .case0-.table
    .long .case1-.table
    .long .case2-.table
.case0:
    li 31,7
    b .return
.case1:
    li 31,-9
    b .return
.case2:
    li 31,123
    b .return
.default:
    li 31,99
.return:
    mr 3,31
    ld 31,16(1)
    addi 1,1,32
    blr
.size synthetic_switch,.-synthetic_switch
.org 0x18000
    .long .table-.base
