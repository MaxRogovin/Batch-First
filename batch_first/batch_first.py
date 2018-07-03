from cffi import FFI

ffi = FFI()
ffi.set_source('_batchfirst_ffi', '#include "Batch_first.h"')

ffi.cdef('''\
typedef int... khint64_t;

static inline void *Batch_first_function(void);

''')

if __name__ == '__main__':
    ffi.compile(verbose=True)
