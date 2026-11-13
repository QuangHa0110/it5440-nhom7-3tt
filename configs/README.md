# configs/

Cấu hình có phiên bản, được tag Git khóa trước khi chạy tập `eval` (xem docs/git-workflow.md).

| Thư mục | Nội dung |
|---|---|
| `semgrep/` | Luật Semgrep/CodeQL tùy biến. Mỗi luật ghi nguồn gốc, viết tay hay do LLM sinh, và kết quả "báo trên bản lỗi, im trên bản vá" |
| `prompts/` | Prompt cho cách B và C, có phiên bản |
| `schemas/` | JSON schema đầu ra của LLM và schema nhãn |
| `eval/` | Manifest khóa cho mỗi lần chạy `eval`: hash prompt, schema, ngưỡng, phiên bản mô hình |
