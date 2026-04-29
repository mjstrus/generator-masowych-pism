"""Generowanie dokumentów DOCX z szablonów docxtpl."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

from docxtpl import DocxTemplate


def render_template(template_path: str | Path, context: Mapping[str, Any]) -> bytes:
    """Renderuje szablon DOCX z podanym kontekstem i zwraca bajty pliku."""
    tpl = DocxTemplate(str(template_path))
    tpl.render(dict(context))
    buffer = BytesIO()
    tpl.save(buffer)
    return buffer.getvalue()


def list_template_variables(template_path: str | Path) -> list[str]:
    """Zwraca listę zmiennych Jinja użytych w szablonie."""
    tpl = DocxTemplate(str(template_path))
    return sorted(tpl.get_undeclared_template_variables())
