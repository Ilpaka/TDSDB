"""Конфигурация Sphinx для документации Document Center API."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

# Документация собирается без .env: задаём безопасные значения для импорта модулей.
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

from app.core.config import settings  # noqa: E402

project = "Document Center API"
author = "Команда разработки Document Center API"
copyright = "2026, ИП «Северный Контур»"
version = settings.APP_VERSION
release = settings.APP_VERSION
language = "ru"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
templates_path = []
exclude_patterns = []

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_mock_imports = []

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_use_rtype = False

html_theme = "furo"
html_title = f"Document Center API {release}"
html_static_path = ["_static"]
napoleon_use_ivar = True


def _skip_parametrized_generics(app, what, name, obj, skip, options):
    """Не документировать параметризованные Pydantic-модели вида ``Page[X]``.

    Pydantic регистрирует их в пространстве имён модулей-потребителей, из-за
    чего autodoc повторно описывает ``Page`` в каждом роутере.
    """
    metadata = getattr(obj, "__pydantic_generic_metadata__", None)
    if metadata and metadata.get("origin") is not None:
        return True
    return skip


def setup(app):
    """Подключить обработчики событий autodoc."""
    app.connect("autodoc-skip-member", _skip_parametrized_generics)
