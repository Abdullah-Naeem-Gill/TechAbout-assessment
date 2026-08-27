import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


class DiskCache:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _file_for(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self.root / f"{digest}.json"

    def get(self, url: str) -> dict | None:
        path = self._file_for(url)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def set(self, url: str, status_code: int, body: str, content_type: str = "") -> None:
        payload = {
            "url": url,
            "status_code": status_code,
            "content_type": content_type,
            "body": body,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._file_for(url).write_text(json.dumps(payload), encoding="utf-8")
