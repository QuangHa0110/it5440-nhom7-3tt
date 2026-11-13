from pr_triage.llm.client import ChatResult
from pr_triage.llm.config import LlmConfig


class ScriptedClient:
    """Trả lần lượt các phản hồi đã định sẵn. Phần tử `Exception` được ném ra."""

    def __init__(self, replies: list[str | Exception], finish: str = "stop") -> None:
        self.replies = list(replies)
        self.calls: list[list[dict[str, str]]] = []
        self.finish = finish
        self._cfg = LlmConfig(
            base_url="http://localhost/v1", model="test-model", allow_external=True
        )

    @property
    def config(self) -> LlmConfig:
        return self._cfg

    def chat(self, messages: list[dict[str, str]]) -> ChatResult:
        self.calls.append(messages)
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return ChatResult(r, 100, 20, 5, self.finish, "test-model")
