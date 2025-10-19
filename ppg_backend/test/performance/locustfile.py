import os
import time
import logging
import matplotlib.pyplot as plt
from locust import HttpUser, task, between, events
import math

def on_test_stop(environment, **kwargs):

    perf_path = "test/performance/performance.txt"
    hist_path = "test/performance/performance_histogram.png"

    print("Locust test finished. Processing results...")

    if not os.path.exists(perf_path):
        print(f"{perf_path} not found, nothing to process.")
        return

    info = ""
    seconds = []
    with open(perf_path, "r") as f:
        for i, line in enumerate(f):
            if i <= 2 and "INFO/locust.runners" in line:
                info = ' '.join(line.strip().split()[-11:])
            if "[Completed]" in line:
                seconds.append(float(line.strip().split()[-2]))

    if not seconds:
        print("No completed tasks found in performance.txt.")
    else:
        try:
            avg = sum(seconds) / len(seconds)
            std = (sum((x - avg) ** 2 for x in seconds) / len(seconds)) ** 0.5

            # percentiles (95th and 99th) using simple rank method
            sorted_seconds = sorted(seconds)
            n = len(sorted_seconds)

            def percentile(sorted_list, pct):
                # rank-based percentile: ceil(pct/100 * n) - 1, clamped
                idx = max(0, min(n - 1, math.ceil((pct / 100.0) * n) - 1))
                return sorted_list[idx]

            p95 = percentile(sorted_seconds, 95)
            p99 = percentile(sorted_seconds, 99)

            min_val = sorted_seconds[0]
            max_val = sorted_seconds[-1]

            print(f"Min time for completed tasks: {min_val:.2f} seconds")
            print(f"Max time for completed tasks: {max_val:.2f} seconds")
            print(f"Average time for completed tasks: {avg:.2f} seconds")
            print(f"Std deviation: {std:.2f} seconds")
            print(f"95th percentile: {p95:.2f} seconds")
            print(f"99th percentile: {p99:.2f} seconds")

            plt.figure(figsize=(8, 4))
            plt.hist(seconds, bins=20, color="skyblue", edgecolor="black")
            plt.title(
                f"Distribution of Completion Times of {len(seconds)} requests ~ N({avg:.2f}, {std:.2f})\n{info}"
            )
            plt.xlabel("Time (seconds)")
            plt.ylabel("Frequency")
            # 평균값 및 percentiles 세로선 추가
            plt.axvline(avg, color="red", linestyle="dashed", linewidth=2, label=f"Average: {avg:.2f}s")
            plt.axvline(p95, color="green", linestyle="dashed", linewidth=2, label=f"95th: {p95:.2f}s")
            plt.axvline(p99, color="purple", linestyle="dotted", linewidth=2, label=f"99th: {p99:.2f}s")
            plt.axvline(min_val, color="orange", linestyle="solid", linewidth=1.5, label=f"Min: {min_val:.2f}s")
            plt.axvline(max_val, color="yellow", linestyle="solid", linewidth=1.5, label=f"Max: {max_val:.2f}s")
            plt.legend()
            plt.tight_layout()
            plt.savefig(hist_path)
            print(f"Histogram saved to {hist_path}")
        except Exception as e:
            print(f"Error processing completion times: {e}")

    try:
        open(perf_path, "w").close()
        print(f"{perf_path} Cleared.")
    except Exception as e:
        print(f"Error removing {perf_path}: {e}")

events.test_stop.add_listener(on_test_stop)

class AnalyzeImageUser(HttpUser):
    wait_time = between(1, 2)

    @task
    def analyze_and_poll(self):
        # 1. 이미지 업로드 (POST /api/analyze)
        with open("test/performance/bibimbap.jpeg", "rb") as img_file:
            img_bytes = img_file.read()
            files = {
                "file": ("bibimbap.jpeg", img_bytes, "image/jpeg")
            }
        # POST 시점부터 시간 측정 시작
        workflow_start = time.time()
        with self.client.post("/api/analyze", files=files, name="/api/analyze", catch_response=True) as response:
            if response.status_code == 202:
                task_id = response.json()["taskId"]
                response.success()
            else:
                response.failure("Failed to start analysis")
                return

        # 2. 폴링 (GET /api/task/{taskId})
        timeout_seconds = 30
        while time.time() - workflow_start < timeout_seconds:
            with self.client.get(f"/api/task/{task_id}", name="/api/task/[id]", catch_response=True) as poll_resp:
                if poll_resp.status_code == 200:
                    data = poll_resp.json()
                    status = data.get("status")
                    if status == "completed":
                        elapsed = time.time() - workflow_start
                        logging.info(f"[Completed] Total time from POST to completed: {elapsed:.2f} seconds")
                        poll_resp.success()
                        return
                    elif status == "failed":
                        elapsed = time.time() - workflow_start
                        logging.info(f"[Failed] Total time from POST to failed: {elapsed:.2f} seconds")
                        poll_resp.failure(f"Task failed: {data.get('detail')}")
                        return
                    else:
                        poll_resp.success()
                else:
                    poll_resp.failure(f"Status check failed for {task_id}")
                    return
            time.sleep(1) # 1초 단위로 polling
        # 타임아웃
        # Locust는 태스크 실행 시간을 기록하므로 별도 실패 처리 없이 종료해도 됩니다.
