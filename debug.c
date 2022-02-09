#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdarg.h>

#include "debug.h"

void init_debugger(Debugger *debugger, const char *filename, const char *prefix,
    const int minimum_debug_level, const int *current_debug_level) 
{
    debugger->fd = creat(filename, S_IRUSR | S_IWUSR);
    debugger->prefix = prefix;
    debugger->prefix_length = strlen(prefix);
    debugger->minimum_debug_level = minimum_debug_level;
    debugger->current_debug_level = current_debug_level;
}// end void init_debugger

void debug(const Debugger *debugger, const char *fmt, ...)
{
    write(debugger->fd, debugger->prefix, debugger->prefix_length);
    va_list argptr;
    va_start(argptr, fmt);
    dprintf(debugger->fd, fmt, argptr);
    va_end(argptr);
    write(debugger->fd, "\n", 1);
}// end void debug
