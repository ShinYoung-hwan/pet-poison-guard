import asyncio
import pytest
from app.services.queue_service import QueueManager, enqueue, process_task_item
from app.services.worker_service import start_workers, stop_workers


class Dummy:
    def __init__(self):
        self.called = False
        self.saved = None

    async def fake_request_ai(self, tmp_path, timeout=15.0, top_k=10):
        return [{"name": "dummy", "toxic": False}]

    async def fake_save(self, task_id, result):
        self.called = True
        self.saved = (task_id, result)


def test_enqueue_and_worker_process(tmp_path):
    async def _runner():
        qm = QueueManager()
        # start a single worker using the test queue manager and a partial process fn
        dummy = Dummy()

        async def proc(task_id, file_tuple):
            await process_task_item(task_id, file_tuple, request_ai_fn=dummy.fake_request_ai, save_fn=dummy.fake_save)

        shutdown = await start_workers(num_workers=1, qm=qm, process_fn=proc)

        # create a temp file
        f = tmp_path / "img.jpg"
        f.write_bytes(b"fake-image-bytes")
        await qm.enqueue("t1", (str(f), "img.jpg", "image/jpeg"))

        # wait for the queue to be processed
        await asyncio.wait_for(qm.ensure().join(), timeout=2.0)

        # give worker a moment to call save
        await asyncio.sleep(0.1)
        assert dummy.called is True
        assert dummy.saved[0] == "t1"

        # shutdown workers
        await stop_workers(shutdown, qm=qm)

    asyncio.run(_runner())