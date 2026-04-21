import json
import os
from datetime import datetime
from config.settings import LOGS_PATH


def log_login(username: str, success: bool, confidence: float = 0.0) -> None:
    """Ghi log mỗi lần đăng nhập vào file JSON."""
    logs = _load_logs()
    logs.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "username": username if username else "unknown",
        "success": success,
        "confidence": confidence,
    })
    with open(LOGS_PATH, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


def get_logs(limit: int = 50) -> list[dict]:
    """Trả về danh sách log gần nhất."""
    logs = _load_logs()
    return logs[-limit:][::-1]  # Mới nhất trước


def _load_logs() -> list:
    if not os.path.exists(LOGS_PATH):
        return []
    with open(LOGS_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return []