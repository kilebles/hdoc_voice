"""
Voicer API client — https://voiceapiru.csv666.ru/docs
"""

import time
from typing import Literal, Optional

import httpx
from pydantic import BaseModel, Field, UUID4

from settings import settings as _default_settings, Settings


# ------------------------------------------------------------------ #
# Request models                                                       #
# ------------------------------------------------------------------ #

class VoiceSettings(BaseModel):
    stability: float = Field(default=0.5, ge=0.0, le=1.0)
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0)
    style: float = Field(default=0.0, ge=0.0, le=1.0)
    use_speaker_boost: bool = True
    speed: float = Field(default=1.0, gt=0.0)


class VoiceTemplate(BaseModel):
    model_id: str = "eleven_v3"
    voice_id: str
    public_owner_id: Optional[str] = None
    voice_settings: VoiceSettings = Field(default_factory=VoiceSettings)
    voice_result_type: Literal["paragraph", "chunks", "default"] = "default"
    subtitles: bool = False
    voice_engine: Literal["default", "alt"] = "default"

    def to_api_dict(self) -> dict:
        d = self.model_dump(exclude={"public_owner_id"}, exclude_none=False)
        if self.public_owner_id is None:
            d.pop("public_owner_id", None)
        d["voice_settings"] = self.voice_settings.model_dump()
        return d


# ------------------------------------------------------------------ #
# Response models                                                      #
# ------------------------------------------------------------------ #

class TaskCreatedResponse(BaseModel):
    task_id: int
    message: str


class TaskStatus(BaseModel):
    task_id: int
    status: Literal["waiting", "processing", "ending", "ending_processed", "error", "error_handled"]
    status_label: str
    created_at: str
    error: Optional[str] = None


class TaskListItem(BaseModel):
    id: int
    status: str
    status_label: str
    created_at: str
    has_result: bool
    file_available: bool
    error: Optional[str] = None
    result_ext: Optional[str] = None
    text_length: int


class TaskListResponse(BaseModel):
    tasks: list[TaskListItem]
    total: int


class TemplateResponse(BaseModel):
    uuid: UUID4
    name: str
    settings: dict
    created_at: str
    broken: bool


class BalanceDescription(BaseModel):
    en: str
    ru: str


class BalanceResponse(BaseModel):
    telegram_id: int
    balance: int
    balance_text: str
    balance_description: BalanceDescription


class OperationResponse(BaseModel):
    status: Literal["pending", "processing", "success", "error"]
    result: Optional[list[str]] = None
    cost_charged: Optional[int] = None
    error: Optional[str] = None


# ------------------------------------------------------------------ #
# Client                                                               #
# ------------------------------------------------------------------ #

class VoicerClient:
    def __init__(self, cfg: Settings = _default_settings):
        self._cfg = cfg
        self._client = httpx.Client(
            base_url=str(cfg.voicer_base_url),
            headers={"X-API-Key": cfg.voice_secret_key.get_secret_value()},
            timeout=cfg.voicer_timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "VoicerClient":
        return self

    def __exit__(self, *_) -> None:
        self.close()

    # ------------------------------------------------------------------ #
    # Balance                                                              #
    # ------------------------------------------------------------------ #

    def get_balance(self) -> BalanceResponse:
        r = self._client.get("/balance")
        r.raise_for_status()
        return BalanceResponse.model_validate(r.json())

    # ------------------------------------------------------------------ #
    # Templates                                                            #
    # ------------------------------------------------------------------ #

    def get_templates(self) -> list[TemplateResponse]:
        r = self._client.get("/templates")
        r.raise_for_status()
        return [TemplateResponse.model_validate(t) for t in r.json()]

    # ------------------------------------------------------------------ #
    # TTS Tasks                                                            #
    # ------------------------------------------------------------------ #

    def create_task(
        self,
        text: str,
        template_uuid: Optional[str] = None,
        template: Optional[VoiceTemplate] = None,
        chunk_size: Optional[int] = None,
        pause_settings: Optional[dict] = None,
        stress_settings: Optional[dict] = None,
    ) -> TaskCreatedResponse:
        payload: dict = {"text": text}
        if template_uuid:
            payload["template_uuid"] = template_uuid
        if template:
            payload["template"] = template.to_api_dict()
        if chunk_size is not None:
            payload["chunk_size"] = chunk_size
        if pause_settings:
            payload["pause_settings"] = pause_settings
        if stress_settings:
            payload["stress_settings"] = stress_settings

        r = self._client.post("/tasks", json=payload)
        r.raise_for_status()
        return TaskCreatedResponse.model_validate(r.json())

    def get_tasks(self, limit: int = 50, offset: int = 0) -> TaskListResponse:
        r = self._client.get("/tasks", params={"limit": limit, "offset": offset})
        r.raise_for_status()
        return TaskListResponse.model_validate(r.json())

    def get_task_status(self, task_id: int) -> TaskStatus:
        r = self._client.get(f"/tasks/{task_id}/status")
        r.raise_for_status()
        return TaskStatus.model_validate(r.json())

    def download_result(self, task_id: int) -> bytes:
        r = self._client.get(f"/tasks/{task_id}/result")
        if r.status_code == 202:
            raise RuntimeError("Task result is not ready yet")
        r.raise_for_status()
        return r.content

    def wait_for_task(self, task_id: int) -> TaskStatus:
        """Poll until task reaches terminal status. Uses timeouts from settings."""
        deadline = time.monotonic() + self._cfg.voicer_task_timeout
        while time.monotonic() < deadline:
            status = self.get_task_status(task_id)
            if status.status in ("ending", "ending_processed"):
                return status
            if status.status in ("error", "error_handled"):
                raise RuntimeError(f"Task {task_id} failed: {status.error}")
            time.sleep(self._cfg.voicer_poll_interval)
        raise TimeoutError(f"Task {task_id} did not complete within {self._cfg.voicer_task_timeout}s")

    def synthesize(
        self,
        text: str,
        template_uuid: Optional[str] = None,
        template: Optional[VoiceTemplate] = None,
        chunk_size: Optional[int] = None,
    ) -> bytes:
        """High-level helper: create task → wait → return audio bytes (MP3 or ZIP)."""
        created = self.create_task(text, template_uuid=template_uuid, template=template, chunk_size=chunk_size)
        self.wait_for_task(created.task_id)
        return self.download_result(created.task_id)

    # ------------------------------------------------------------------ #
    # Image generation                                                     #
    # ------------------------------------------------------------------ #

    def generate_image_flow(
        self,
        prompt: str,
        model: Literal["GEM_PIX_2", "IMAGEN_3_5", "NARWHAL"] = "GEM_PIX_2",
        aspect_ratio: Literal["16:9", "4:3", "1:1", "3:4", "9:16"] = "1:1",
        seed: Optional[int] = None,
        reference_images: Optional[list[str]] = None,
    ) -> str:
        """Returns operation_id."""
        payload: dict = {"prompt": prompt, "model": model, "aspect_ratio": aspect_ratio}
        if seed is not None:
            payload["seed"] = seed
        if reference_images:
            payload["reference_images"] = reference_images
        r = self._client.post("/api/v4/flow/image/generate", json=payload)
        r.raise_for_status()
        return r.json()["operation_id"]

    def generate_image_flower(
        self,
        prompt: str,
        aspect_ratio: Literal["16:9", "9:16", "1:1"] = "1:1",
        reference_image: Optional[str] = None,
    ) -> str:
        """Returns operation_id."""
        payload: dict = {"prompt": prompt, "aspect_ratio": aspect_ratio}
        if reference_image:
            payload["reference_image"] = reference_image
        r = self._client.post("/api/v4/flower/image/generate", json=payload)
        r.raise_for_status()
        return r.json()["operation_id"]

    def generate_image_openai(
        self,
        prompt: str,
        aspect_ratio: str = "1:1",
        reference_images: Optional[list[str]] = None,
    ) -> str:
        """Returns operation_id."""
        payload: dict = {"prompt": prompt, "aspect_ratio": aspect_ratio}
        if reference_images:
            payload["reference_images"] = reference_images
        r = self._client.post("/api/v4/openai/image/generate", json=payload)
        r.raise_for_status()
        return r.json()["operation_id"]

    def get_operation(self, operation_id: str) -> OperationResponse:
        r = self._client.get(f"/api/v4/operations/{operation_id}")
        r.raise_for_status()
        return OperationResponse.model_validate(r.json())

    def wait_for_image(self, operation_id: str) -> list[str]:
        """Poll until image operation succeeds. Returns list of base64 data-URI strings."""
        deadline = time.monotonic() + self._cfg.voicer_image_timeout
        while time.monotonic() < deadline:
            op = self.get_operation(operation_id)
            if op.status == "success":
                return op.result or []
            if op.status == "error":
                raise RuntimeError(f"Image generation failed: {op.error}")
            time.sleep(self._cfg.voicer_poll_interval)
        raise TimeoutError(f"Operation {operation_id} did not complete within {self._cfg.voicer_image_timeout}s")
