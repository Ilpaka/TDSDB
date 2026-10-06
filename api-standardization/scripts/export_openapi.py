"""Экспортировать фактически генерируемую OpenAPI-схему в файл.

Схема сохраняется в ``docs/openapi/openapi.json`` и является формальным
контрактом API v1. Тест ``test_exported_schema_matches_application``
проверяет, что файл соответствует текущей реализации.

Пример::

    python -m scripts.export_openapi
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402

OUTPUT = ROOT / "docs" / "openapi" / "openapi.json"


def export_openapi(out: Path = OUTPUT) -> Path:
    """Записать OpenAPI-схему приложения в файл.

    Args:
        out: Путь к файлу результата.

    Returns:
        Путь к записанному файлу.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(app.openapi(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out


if __name__ == "__main__":
    path = export_openapi()
    print(f"OpenAPI schema written to {path.relative_to(ROOT)}")
