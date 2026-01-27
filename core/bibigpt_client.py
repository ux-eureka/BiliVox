import os
import time
from typing import Any

import requests


class BibiGPTClient:
    def __init__(self, api_token: str | None = None, base_url: str | None = None, timeout_sec: float = 30.0):
        self.api_token = (api_token or os.getenv("BIBIGPT_API_TOKEN") or os.getenv("BIBIGPT_API_KEY") or "").strip()
        self.base_url = (base_url or os.getenv("BIBIGPT_BASE_URL") or "https://api.bibigpt.co/api").rstrip("/")
        self.timeout_sec = float(timeout_sec)

        if not self.api_token:
            raise ValueError("未配置 BibiGPT API Token：请设置环境变量 BIBIGPT_API_TOKEN")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_token}"}

    def create_summary_task(self, url: str) -> dict[str, Any]:
        r = requests.get(
            f"{self.base_url}/v1/createSummaryTask",
            params={"url": url},
            headers=self._headers(),
            timeout=self.timeout_sec,
        )
        r.raise_for_status()
        return r.json()

    def get_summary_task_status(self, task_id: str, include_detail: bool = True) -> dict[str, Any]:
        params: dict[str, Any] = {"taskId": task_id}
        if include_detail:
            params["includeDetail"] = "true"
        r = requests.get(
            f"{self.base_url}/v1/getSummaryTaskStatus",
            params=params,
            headers=self._headers(),
            timeout=self.timeout_sec,
        )
        r.raise_for_status()
        return r.json()

    def wait_summary(self, url: str, poll_interval_sec: float = 3.0, max_wait_sec: float = 1800.0, include_detail: bool = True, on_poll=None) -> dict[str, Any]:
        created = self.create_summary_task(url)
        task_id = str(created.get("taskId") or "").strip()
        if not task_id:
            raise ValueError(f"BibiGPT 创建任务失败：{created}")

        started_at = time.time()
        last_status = None
        while True:
            if time.time() - started_at > max_wait_sec:
                raise TimeoutError(f"BibiGPT 任务超时（{int(max_wait_sec)}s）：taskId={task_id}")

            payload = self.get_summary_task_status(task_id, include_detail=include_detail)
            status = str(payload.get("status") or "").strip().lower()
            if status and status != last_status and on_poll:
                try:
                    on_poll({"taskId": task_id, "status": status, "payload": payload})
                except Exception:
                    pass
            last_status = status

            if payload.get("summary"):
                return payload
            if status in ("failed", "error", "canceled", "cancelled"):
                raise ValueError(payload.get("message") or f"BibiGPT 任务失败：status={status}")

            time.sleep(max(0.5, float(poll_interval_sec)))

