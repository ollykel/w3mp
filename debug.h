#ifndef __DEBUG_H__
#define __DEBUG_H__

#include <stdarg.h>

typedef struct _Debugger {
    char	*filename;
    int		minimum_debug_level;
    int		*current_debug_level;
    char	*prefix;
} Debugger;

extern void init_debugger(
    Debugger *debugger,
    const char *filename,
    const char *prefix,
    const int minimum_debug_level,
    const int *current_debug_level
);

extern void debug(const Debugger *debugger, const char *fmt, ...);

#endif
