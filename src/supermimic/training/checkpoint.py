"""Atomic torch checkpoints with bounded dirty-page cache on small-RAM Linux hosts."""
from __future__ import annotations

import ctypes
import gc
import os
from pathlib import Path
import time

import torch


class CacheLimitedWriter:
    def __init__(self,path):
        self.file=open(path,"xb",buffering=0)
        self.dirty=0

    def write(self,data):
        view=memoryview(data)
        written=0
        while written<len(view):
            size=self.file.write(view[written:])
            if not size:raise OSError("checkpoint write made no progress")
            written+=size
        self.dirty+=written
        if self.dirty>=1024*1024:
            self.flush_cache()
        return written

    def flush_cache(self):
        self.file.flush()
        os.fdatasync(self.file.fileno())
        os.posix_fadvise(self.file.fileno(),0,0,os.POSIX_FADV_DONTNEED)
        self.dirty=0

    def flush(self):
        self.file.flush()

    def close(self):
        self.flush_cache()
        self.file.close()

    def __getattr__(self,name):
        return getattr(self.file,name)


def atomic_torch_save(payload,destination):
    destination=Path(destination)
    temporary=destination.with_name(f".{destination.name}.{time.time_ns()}.tmp")
    writer=CacheLimitedWriter(temporary)
    try:
        torch.save(payload,writer)
        writer.close()
        temporary.replace(destination)
    except BaseException:
        if not writer.file.closed:writer.file.close()
        # Preserve any partial file as evidence; never promote it to a valid checkpoint.
        raise
    finally:
        gc.collect()
        allocator=ctypes.CDLL(None)
        if hasattr(allocator,"malloc_trim"):allocator.malloc_trim(0)
