import asyncio
import logging
import uuid
from typing import Any, Callable, Optional, TYPE_CHECKING
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from infrastructure.queue.queue_store import QueueStore

logger = logging.getLogger(__name__)


class QueueInterface(ABC):
    @abstractmethod
    async def add(self, item: Any) -> Any:
        pass
    
    @abstractmethod
    async def start(self) -> None:
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        pass
    
    @abstractmethod
    def get_status(self) -> dict:
        pass


class QueuedRequest:
    __slots__ = ('album_mbid', 'future', 'job_id', 'retry_count', 'recovered')
    
    def __init__(
        self,
        album_mbid: str,
        future: Optional[asyncio.Future] = None,
        job_id: str = "",
        recovered: bool = False,
    ):
        self.album_mbid = album_mbid
        self.future: asyncio.Future = future if future is not None else asyncio.get_event_loop().create_future()
        self.job_id = job_id or str(uuid.uuid4())
        self.retry_count = 0
        self.recovered = recovered


class RequestQueue(QueueInterface):
    def __init__(
        self,
        processor: Callable,
        maxsize: int = 200,
        store: "QueueStore | None" = None,
        max_retries: int = 3,
    ):
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=maxsize)
        self._processor = processor
        self._processor_task: Optional[asyncio.Task] = None
        self._processing = False
        self._maxsize = maxsize
        self._store = store
        self._max_retries = max_retries
    
    async def add(self, album_mbid: str) -> dict:
        await self.start()
        
        request = QueuedRequest(album_mbid)
        await self._queue.put(request)
        if self._store:
            self._store.enqueue(request.job_id, album_mbid)
        
        result = await request.future
        return result
    
    async def start(self) -> None:
        if self._processor_task is None or self._processor_task.done():
            self._processor_task = asyncio.create_task(self._process_queue())
            logger.info("Queue processor started")
            self._recover_pending()
    
    async def stop(self) -> None:
        if self._processor_task and not self._processor_task.done():
            await self.drain()
            
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
            self._processor_task = None
            logger.info("Queue processor stopped")
    
    async def drain(self, timeout: float = 30.0) -> None:
        try:
            await asyncio.wait_for(self._queue.join(), timeout=timeout)
            logger.info("Queue drained successfully")
        except asyncio.TimeoutError:
            remaining = self._queue.qsize()
            logger.warning("Queue drain timeout: %d items remaining", remaining)
    
    def get_status(self) -> dict:
        status = {
            "queue_size": self._queue.qsize(),
            "max_size": self._maxsize,
            "processing": self._processing,
        }
        if self._store:
            status["dead_letter_count"] = self._store.get_dead_letter_count()
            status["persisted_pending"] = len(self._store.get_all())
        return status
    
    def _recover_pending(self) -> None:
        if not self._store:
            return
        self._store.reset_processing()
        pending = self._store.get_pending()
        recovered = 0
        for row in pending:
            request = QueuedRequest(
                album_mbid=row["album_mbid"],
                job_id=row["id"],
                recovered=True,
            )
            try:
                self._queue.put_nowait(request)
                recovered += 1
            except asyncio.QueueFull:
                logger.warning("Queue full during recovery, %d items deferred to next restart",
                               len(pending) - recovered)
                break
        if recovered:
            logger.info("Recovered %d pending jobs from store", recovered)

        self._retry_dead_letters()

    def _retry_dead_letters(self) -> None:
        if not self._store:
            return
        retryable = self._store.get_retryable_dead_letters()
        enqueued = 0
        for row in retryable:
            if self._store.has_pending_mbid(row["album_mbid"]):
                self._store.remove_dead_letter(row["id"])
                continue
            self._store.remove_dead_letter(row["id"])
            inserted = self._store.enqueue(row["id"], row["album_mbid"])
            if not inserted:
                continue
            request = QueuedRequest(
                album_mbid=row["album_mbid"],
                job_id=row["id"],
                recovered=True,
            )
            request.retry_count = row["retry_count"]
            try:
                self._queue.put_nowait(request)
                enqueued += 1
            except asyncio.QueueFull:
                logger.warning("Queue full during dead-letter retry, remaining deferred")
                break
        if enqueued:
            logger.info("Re-enqueued %d dead-letter jobs for retry", enqueued)

    async def _process_queue(self) -> None:
        while True:
            try:
                request: QueuedRequest = await self._queue.get()
                self._processing = True
                
                if self._store:
                    self._store.mark_processing(request.job_id)

                try:
                    if request.recovered:
                        logger.info("Processing recovered job %s for album %s", request.job_id[:8], request.album_mbid[:8])
                    result = await self._processor(request.album_mbid)
                    if not request.future.done():
                        request.future.set_result(result)
                    if self._store:
                        self._store.dequeue(request.job_id)
                except Exception as e:  # noqa: BLE001
                    logger.error("Error processing request for %s (attempt %d/%d): %s",
                                 request.album_mbid[:8], request.retry_count + 1, self._max_retries, e)
                    if not request.future.done():
                        request.future.set_exception(e)
                    if self._store:
                        self._store.dequeue(request.job_id)
                        self._store.add_dead_letter(
                            job_id=request.job_id,
                            album_mbid=request.album_mbid,
                            error_message=str(e),
                            retry_count=request.retry_count + 1,
                            max_retries=self._max_retries,
                        )
                finally:
                    self._queue.task_done()
                    self._processing = False
            
            except asyncio.CancelledError:
                logger.info("Queue processor cancelled")
                break
            except Exception as e:  # noqa: BLE001
                logger.error("Queue processor error: %s", e)
                self._processing = False
