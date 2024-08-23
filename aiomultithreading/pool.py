"""Combines multiprocessing + threading and asyncio alltogether
into one mega-beast called aiomultithreading
"""

# TODO: (Vizonex) Reorganize the imports.

import asyncio
import os
import queue
from multiprocessing import get_context
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

from aiomultiprocess import Process
from aiomultiprocess.pool import (
    CHILD_CONCURRENCY,
    MAX_TASKS_PER_CHILD,
    Pool,
    RoundRobin,
)
from aiomultiprocess.scheduler import Scheduler
from aiomultiprocess.types import LoopInitializer, Queue, QueueID, TaskID, TracebackStr
from aiothreading import ThreadPool
from aiothreading.scheduler import RoundRobin as ThreadRoundRobin
from aiothreading.scheduler import Scheduler as ThreadScheduler

from .types import PoolTask, ProcessTID, ThreadTID


class ProcessWorker(Process):
    def __init__(
        self,
        tx: Queue,
        rx: Queue,
        threads:Optional[int] = None,
        queuecount:Optional[int] = None,
        ttl: int = MAX_TASKS_PER_CHILD,
        concurrency: int = CHILD_CONCURRENCY,
        scheduler:Optional[ThreadScheduler] = None,
        *,
        initializer: Optional[Callable] = None,
        initargs: Sequence[Any] = (),
        loop_initializer: Optional[LoopInitializer] = None,
        exception_handler: Optional[Callable[[BaseException], None]] = None,
    ) -> None:
        super().__init__(
            target=self.run,
            initializer=initializer,
            initargs=initargs,
            loop_initializer=loop_initializer,
        )
        self.loop_initializer = loop_initializer
        self.exception_handler = exception_handler
        self.initargs = initargs
        self.initializer = initializer
        self.queuecount = queuecount
        self.scheduler = scheduler or ThreadRoundRobin()
        # NOTE: ttl & concurrency should really be multiplied because we need to take 
        # all the addtional threads into consideration which would 
        # be a significant speedup

        # Make sure threads gets initalized...
        self.threads = min(32, threads or ((os.cpu_count() or 1) + 4))

        self.concurrency = max(1, concurrency * self.threads)
        self.exception_handler = exception_handler
        self.ttl = max(0, ttl * self.threads)
        self.tx = tx
        self.rx = rx

        

    async def run(self) -> None:
        """Pick up work, execute work, return results, rinse, repeat."""
        
        # Since Execution is not happening in this worker besides the inner threadpool
        # We can be a lot more lax about what were carrying so we should really only be carrying
        # The TaskIDs setup as {ProcessTID, ThreadTID}
        
        pending: Dict[ProcessTID, ThreadTID] = {}
        completed = 0
        running = True
        async with ThreadPool(
            threads=self.threads,
            initializer=self.initializer,
            initargs=self.initargs,
            maxtasksperchild=self.ttl // self.threads,
            childconcurrency=self.concurrency // self.threads,
            queuecount=self.queuecount,
            scheduler=self.scheduler,
            loop_initializer=self.loop_initializer,
            exception_handler=self.exception_handler
        ) as thread_pool:
            while running or pending:
                # TTL, Tasks To Live, determines how many tasks to execute before dying
                if self.ttl and completed >= self.ttl:
                    running = False

                # pick up new work as long as we're "running" and we have open slots
                while running and len(pending) < self.concurrency:
                    try:
                        task: PoolTask = self.tx.get_nowait()
                    except queue.Empty:
                        break

                    if task is None:
                        running = False
                        break
                    
                    # To make things less confusing I'm naming tid to process_id
                    process_id, func, args, kwargs = task
                    pending[process_id] = thread_pool.queue_work(func, args, kwargs)

                if not pending:
                    await asyncio.sleep(0.005)
                    continue

                # return results and/or exceptions when completed

                for process_id, thread_id in pending.copy().items():
                    if thread_id in thread_pool._results:
                        # Result and traceback have already been taken care of on the threadpool...
                        result, tb = thread_pool._results.pop(
                            # Remove pending process_id
                            pending.pop(process_id)
                        )
                        self.rx.put_nowait((process_id, result, tb))
                        completed += 1
                
                await asyncio.sleep(0.005)




class MultiPool(Pool):
    """Multiprocessing + Threading + Asyncio. All in one box. All creating the biggest 
    worker possible all unified with one task.

    Each Process carries with it a threadpool of it's own
    Allowing the number of tasks to be multiplied rapidly 
    
    from 96 tasks (6 threads * 16 children)
    when multiplied with (4 processes) we get (384 tasks by default)
    enough to do some serious damage.

    """

    def __init__(
        self,
        processes:Optional[int] = None,
        threads:Optional[int] = None,
        initializer: Callable[..., None] = None,
        initargs: Sequence[Any] = (),
        maxtasksperchild: int = MAX_TASKS_PER_CHILD,
        childconcurrency: int = CHILD_CONCURRENCY,
        queuecount: Optional[int] = None,
        scheduler: Scheduler = None,
        loop_initializer: Optional[LoopInitializer] = None,
        exception_handler: Optional[Callable[[BaseException], None]] = None,
    ) -> None:
        self.context = get_context()

        self.scheduler = scheduler or RoundRobin()
        self.process_count = max(1, processes or os.cpu_count() or 2)
        self.queue_count = max(1, queuecount or 1)
        self.thread_count = min(32, threads or ((os.cpu_count() or 1) + 4))

        if self.queue_count > self.process_count:
            raise ValueError("queue count must be <= process count")

        self.initializer = initializer
        self.initargs = initargs
        self.loop_initializer = loop_initializer
        self.maxtasksperchild = max(0, maxtasksperchild)
        self.childconcurrency = max(1, childconcurrency)
        self.exception_handler = exception_handler

        self.processes: Dict[Process, QueueID] = {}
        self.queues: Dict[QueueID, Tuple[Queue, Queue]] = {}

        self.running = True
        self.last_id = 0
        self._results: Dict[TaskID, Tuple[Any, Optional[TracebackStr]]] = {}

        self.init()
        self._loop = asyncio.ensure_future(self.loop())

    def create_worker(self, qid: QueueID) -> ProcessWorker:
        """
        Create a worker process + threadpool attached to the given transmit and receive queues.

        :meta private:
        """
       
        # TODO: (Vizonex) Seperate Schedulers...
        tx, rx = self.queues[qid]
        process = ProcessWorker(
            tx,
            rx,
            threads=self.thread_count,
            queuecount=self.queue_count,
            ttl=self.maxtasksperchild,
            concurrency=self.childconcurrency,
            initializer=self.initializer,
            initargs=self.initargs,
            loop_initializer=self.loop_initializer,
            exception_handler=self.exception_handler,
        )
        process.start()
        return process

    # Everything from here has already been written thank goodness...

    # TODO: Allow futures to return from a map in the order that everything is finishing 
    # where what is finished returns first...
    