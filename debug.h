#ifndef __DEBUG_H__
#define __DEBUG_H__

#include <stdarg.h>

typedef struct _Debugger
{
    char *filename;
    int debug_level;
    char *prefix;
} Debugger;

extern void init_debugger(Debugger * debugger,
                          const char *filename,
                          const char *prefix, const int debug_level);

extern void debugf(const Debugger * debugger, const int debug_threshold,
                   const char *fmt, ...);

#endif
