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
    """
    시나리오: QueueManager에 작업을 enqueued한 뒤, 워커 프로세스가 해당 작업을 소비하여
    AI 요청(request_ai_fn)을 호출하고 결과를 저장(save_fn)하는 전체 흐름을 통합적으로 검증한다.

    절차:
    1. 테스트 전용 `QueueManager` 인스턴스를 생성한다.
    2. 더미(Dummy) 객체를 만들어 `fake_request_ai`와 `fake_save` 함수를 주입한다.
    3. 워커를 하나 시작하고, 처리 함수(proc)는 `process_task_item`을 호출하되 더미 함수를 주입해 외부 의존을 격리한다.
    4. 임시 이미지 파일을 만들고 `enqueue`로 작업을 큐에 넣는다.
    5. 큐가 처리될 때까지 대기하고, 더미의 `saved` 속성이 적절히 설정되는지 확인한다.
    6. 워커를 종료한다.

    예상 결과: 워커가 큐에서 작업을 받아 `fake_request_ai`를 통해 결과를 생성하고,
    `fake_save`가 호출되어 저장 콜백이 발생해야 한다. 더미의 `saved` 튜플 첫 항목은 enqueued한 task_id여야 한다.
    """
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