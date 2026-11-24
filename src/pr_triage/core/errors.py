"""Các lỗi miền, để pipeline phân biệt khi suy giảm (kiến trúc mục 7.4)."""


class ScanError(Exception):
    """Công cụ quét lỗi hoặc quá thời gian."""


class ContextError(Exception):
    """Không trích được ngữ cảnh."""


class LlmError(Exception):
    """Gọi mô hình lỗi: mạng, mã trạng thái, hay đầu ra bị cắt."""


class BudgetExceeded(LlmError):
    """Hết ngân sách token hoặc chi phí."""


class ScmError(Exception):
    """Gọi SCM lỗi."""
