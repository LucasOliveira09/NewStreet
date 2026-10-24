/* Test harness only. The two function bodies are generated from the local ELF. */
#include "ppu_recomp.h"
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    uint64_t address = strtoull(argv[1], NULL, 16);
    void (*selected)(ppu_context *) = NULL;
    for (uint64_t i = 0; i < function_table_count; ++i)
        if (function_table[i].addr == address) selected = function_table[i].func;
    if (!selected) return 3;
    uint64_t value;
    while (scanf("%" SCNx64, &value) == 1) {
        ppu_context ctx = {0};
        ctx.gpr[3] = value;
        selected(&ctx);
        printf("%016" PRIx64 "\n", ctx.gpr[3]);
    }
    return ferror(stdin) ? 4 : 0;
}
