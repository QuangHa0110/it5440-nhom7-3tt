# <Tên kế hoạch: thay đổi gì, trong một dòng>

- **Status:** queued | active | done | failed
- **Người làm:**
- **Đóng:** mục nợ, RQ hoặc ADR mà kế hoạch này hoàn thành
- **Quyết định cho phép:** liên kết ADR hoặc quyết định của nhóm
- **Nhánh:** `{dev}/{slug}/{nội dung}`
- **Bắt đầu / Kết thúc:** YYYY-MM-DD / —

---

## Bối cảnh

Vì sao việc này cần làm *bây giờ*. Dẫn chứng bằng liên kết.

## Ngoài phạm vi

Việc lân cận cố ý không làm, và lý do.

## Hiện trạng đã kiểm chứng

Điều đã kiểm tra thay vì giả định, kèm ngày và lệnh.

---

## Task

Mỗi dòng là **một commit** với điều kiện hoàn thành **quan sát được**: lệnh in ra gì, test khẳng định gì, file chứa gì.

| # | Task | Xong khi | Phụ thuộc |
|---|---|---|---|
| T1 | | | — |
| T2 | | | T1 |

## Cổng

Lệnh phải qua trước khi chuyển kế hoạch sang `done/`.

```bash
make check
```

## Rủi ro và cách nhận biết

| Rủi ro | Dấu hiệu | Làm gì khi xảy ra |
|---|---|---|
| | | |

---

## Kết quả

*Điền khi đóng kế hoạch. Không sửa phần thân phía trên.*

- **Kết quả:**
- **Khác kế hoạch ở đâu:**
- **Ghi ở:** devlog, mục nợ, ADR
