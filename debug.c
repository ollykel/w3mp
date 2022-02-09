#include <stdio.h>
#include <stdarg.h>

#include "debug.h"

void init_debugger(Debugger *debugger, const char *filename, const char *prefix,
    const int minimum_debug_level, const int *current_debug_level) 
{
    debugger->filename = filename;
    debugger->prefix = prefix;
    debugger->minimum_debug_level = minimum_debug_level;
    debugger->current_debug_level = current_debug_level;
}// end void init_debugger

void debugf(const Debugger *debugger, const char *fmt, ...)
{
    if (*(debugger->current_debug_level) < debugger->minimum_debug_level)
	return;
    FILE *f = fopen(debugger->filename, "a");
    fputs(debugger->prefix, f);
    va_list argptr;
    va_start(argptr, fmt);
    vfprintf(f, fmt, argptr);
    va_end(argptr);
    fputc('\n', f);
    fclose(f);
}// end void debug
