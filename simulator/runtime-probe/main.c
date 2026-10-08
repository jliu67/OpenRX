/* Linux runtime controls for OpenRX. No performance or power measurements. */
#define _GNU_SOURCE
#include <errno.h>
#include <setjmp.h>
#include <signal.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/resource.h>
#include <sys/syscall.h>
#include <unistd.h>

#if defined(__riscv) && __riscv_xlen == 64
#define ARCH "riscv64"
#define FLUSH "linux-riscv-flush-icache"
#elif defined(__x86_64__)
#define ARCH "x86_64"
#define FLUSH "compiler-builtin"
#else
#error "Runtime probe supports Linux RV64 and x86_64 only"
#endif

static sigjmp_buf recovery;
static volatile sig_atomic_t expected_signal;
static volatile sig_atomic_t received_signal;
static unsigned checks;
static void handler(int sig) {
    if (sig != expected_signal) _exit(120);
    received_signal = sig;
    siglongjmp(recovery, 1);
}
static void check(const char *name, int actual, int expected) {
    ++checks;
    printf("{\"type\":\"check\",\"name\":\"%s\",\"actual\":%d,\"expected\":%d,\"status\":\"%s\"}\n",
           name, actual, expected, actual == expected ? "pass" : "fail");
    fflush(stdout);
    if (actual != expected) exit(1);
}
static void fail(const char *operation) {
    printf("{\"type\":\"fatal\",\"operation\":\"%s\",\"errno\":%d}\n", operation, errno);
    exit(1);
}
static void protect(void *page, size_t size, int mode) {
    if (mprotect(page, size, mode) != 0) fail("mprotect");
}
static void emit(void *page, unsigned value) {
#if defined(__riscv)
    uint32_t code[2] = {(value << 20) | 0x00000513u, 0x00008067u};
    memcpy(page, code, sizeof(code)); /* addi a0,zero,value; ret */
#else
    unsigned char code[6] = {0xb8, (unsigned char)value, 0, 0, 0, 0xc3};
    memcpy(page, code, sizeof(code)); /* mov eax,value; ret */
#endif
}
static int flush(void *page, size_t size) {
#if defined(__riscv)
    /* Flags 0 requests the Linux process-wide icache ABI, not just a local fence. */
    return (int)syscall(__NR_riscv_flush_icache, page, (char *)page + size, 0);
#else
    __builtin___clear_cache((char *)page, (char *)page + size);
    return 0;
#endif
}

int main(void) {
    struct rlimit no_core = {0, 0};
    if (setrlimit(RLIMIT_CORE, &no_core) != 0) fail("setrlimit");
    struct sigaction action;
    memset(&action, 0, sizeof(action));
    action.sa_handler = handler;
    if (sigemptyset(&action.sa_mask) != 0 ||
        sigaction(SIGILL, &action, NULL) != 0 ||
        sigaction(SIGSEGV, &action, NULL) != 0) fail("sigaction");
    printf("{\"type\":\"config\",\"schema_version\":1,\"architecture\":\"%s\",\"flush_path\":\"%s\",\"functional_only\":true}\n", ARCH, FLUSH);
    fflush(stdout);
    expected_signal = SIGILL;
    received_signal = 0;
    if (sigsetjmp(recovery, 1) == 0) {
#if defined(__riscv)
        __asm__ volatile(".word 0");
#else
        __asm__ volatile("ud2");
#endif
    }
    expected_signal = 0;
    check("sigill-recovery", received_signal, SIGILL);
    long page_size = sysconf(_SC_PAGESIZE);
    if (page_size <= 0) fail("page-size");
    void *page = mmap(NULL, (size_t)page_size, PROT_READ | PROT_WRITE,
                      MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (page == MAP_FAILED) fail("mmap");
    emit(page, 7);
    expected_signal = SIGSEGV;
    received_signal = 0;
    if (sigsetjmp(recovery, 1) == 0) (void)((int (*)(void))page)();
    expected_signal = 0;
    check("rw-execution-denied", received_signal, SIGSEGV);
    protect(page, (size_t)page_size, PROT_READ | PROT_EXEC);
    check("initial-cache-flush", flush(page, (size_t)page_size), 0);
    check("generated-return", ((int (*)(void))page)(), 7);
    expected_signal = SIGSEGV;
    received_signal = 0;
    if (sigsetjmp(recovery, 1) == 0) *(volatile unsigned char *)page = 0;
    expected_signal = 0;
    check("rx-write-denied", received_signal, SIGSEGV);
    protect(page, (size_t)page_size, PROT_READ | PROT_WRITE);
    emit(page, 19);
    protect(page, (size_t)page_size, PROT_READ | PROT_EXEC);
    check("overwrite-cache-flush", flush(page, (size_t)page_size), 0);
    check("overwritten-return", ((int (*)(void))page)(), 19);
    protect(page, (size_t)page_size, PROT_READ | PROT_WRITE);
    emit(page, 7);
    protect(page, (size_t)page_size, PROT_READ | PROT_EXEC);
    check("restore-cache-flush", flush(page, (size_t)page_size), 0);
    check("restored-return", ((int (*)(void))page)(), 7);
    if (munmap(page, (size_t)page_size) != 0) fail("munmap");
    printf("{\"type\":\"summary\",\"checks\":%u,\"status\":\"pass\",\"functional_only\":true}\n", checks);
    return 0;
}
