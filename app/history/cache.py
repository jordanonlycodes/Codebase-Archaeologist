"""Bounded process-local public evidence cache; no disk, credentials or browser state."""
import asyncio
import base64
from collections import OrderedDict
from concurrent.futures import Future
from copy import deepcopy
from dataclasses import asdict, is_dataclass, astuple
from functools import wraps
import json
import threading
import time

from app.errors import AnalysisError


def encoded_size(value):
    def encode(item):
        if is_dataclass(item):
            return asdict(item)
        if isinstance(item, bytes):
            return base64.b64encode(item).decode('ascii')
        raise TypeError('Unsupported evidence type')
    return len(json.dumps(value, default=encode, ensure_ascii=False).encode('utf-8'))


class EvidenceCache:
    """LRU+TTL, defensive copies, independent per-key flights across event-loop callers.

    Canceling an awaiter leaves the bounded producer alive. Its own client/deadline owns
    the network work; failed producers are removed and never retained as cached failures.
    """
    def __init__(self, *, entries=256, byte_limit=16*1024*1024, entry_bytes=2*1024*1024,
                 flights=2, clock=time.monotonic):
        self.entries=entries; self.byte_limit=byte_limit; self.entry_bytes=entry_bytes
        self.max_flights=flights; self.clock=clock; self.lock=threading.RLock()
        self.values=OrderedDict(); self.pending={}; self.bytes=0
        self.hits=0; self.misses=0; self.coalesced=0; self.evictions=0

    def _prune(self):
        for key, (_, expiry, size) in list(self.values.items()):
            if expiry <= self.clock():
                del self.values[key]; self.bytes-=size

    def diagnostics(self):
        with self.lock:
            self._prune()
            return dict(entries=len(self.values), bytes=self.bytes, flights=len(self.pending),
                        hits=self.hits, misses=self.misses, coalesced=self.coalesced,
                        evictions=self.evictions)

    async def obtain(self, key, factory, ttl):
        with self.lock:
            self._prune()
            if key in self.values:
                value, _, _=self.values[key]; self.values.move_to_end(key); self.hits+=1
                return deepcopy(value), 'hit'
            if key in self.pending:
                future, _=self.pending[key]; self.coalesced+=1; state='coalesced'
            else:
                if len(self.pending)>=self.max_flights:
                    raise AnalysisError('Two GitHub evidence requests are already running. Retry shortly.', 'busy', 429)
                future=Future(); self.misses+=1; state='miss'
                task=asyncio.create_task(self._produce(key, future, factory, ttl))
                self.pending[key]=(future, task)
        wrapped=asyncio.wrap_future(future)
        # An abandoned consumer must not produce an unhandled exception warning later.
        wrapped.add_done_callback(lambda f: f.exception() if not f.cancelled() else None)
        value=await asyncio.shield(wrapped)
        return deepcopy(value), state

    async def _produce(self, key, future, factory, ttl):
        try:
            value=await factory(); size=encoded_size(value)
            with self.lock:
                self._prune()
                if ttl>0 and self.entries>0 and size<=min(self.entry_bytes,self.byte_limit):
                    while self.values and (len(self.values)>=self.entries or self.bytes+size>self.byte_limit):
                        _, (_, _, old)=self.values.popitem(last=False); self.bytes-=old; self.evictions+=1
                    self.values[key]=(deepcopy(value),self.clock()+ttl,size); self.bytes+=size
                self.pending.pop(key,None)
            future.set_result(value)
        except BaseException as error:
            with self.lock:
                self.pending.pop(key,None)
            if isinstance(error,asyncio.CancelledError):
                future.cancel()
            else:
                future.set_exception(error)


CACHE=EvidenceCache()


def evidence(ttl=900):
    """Cache only successfully parsed/validated method output, never raw error bodies."""
    def decorate(method):
        @wraps(method)
        async def wrapped(self,*args):
            key=('history-v2',self.scope,self.repo.owner.lower(),self.repo.name.lower(),
                 method.__name__,args,astuple(self.limits))
            async def produce():
                return await asyncio.wait_for(method(self,*args),self.limits.seconds)
            value,state=await self.cache.obtain(key,produce,ttl)
            self.cache_states.append(state)
            return value
        return wrapped
    return decorate
