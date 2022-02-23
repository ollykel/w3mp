#include <stdio.h>
#include <stdarg.h>

#include "debug.h"

void
init_debugger(Debugger * debugger, const char *filename, const char *prefix,
              const int debug_level)
{
    debugger->filename = filename;
    debugger->prefix = prefix;
    debugger->debug_level = debug_level;
}                               // end void init_debugger

void
debugf(const Debugger * debugger, const int debug_threshold, const char *fmt,
       ...)
{
    if (debugger->debug_level < debug_threshold)
        return;
    FILE *f = fopen(debugger->filename, "a");
    fputs(debugger->prefix, f);
    va_list argptr;
    va_start(argptr, fmt);
    vfprintf(f, fmt, argptr);
    va_end(argptr);
    fputc('\n', f);
    fclose(f);
}                               // end void debug
