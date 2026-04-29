"""Wysyłka maili z załącznikami przez SMTP."""
from __future__ import annotations

import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from typing import Iterable

import streamlit as st


def _smtp_config() -> dict:
    return dict(st.secrets["smtp"])


def send_email(
    to: str,
    subject: str,
    body: str,
    attachments: Iterable[tuple[str, bytes]] = (),
) -> None:
    """Wysyła email z opcjonalnymi załącznikami DOCX.

    attachments: iterable of (filename, content_bytes).
    """
    cfg = _smtp_config()
    msg = EmailMessage()
    msg["From"] = formataddr((cfg.get("from_name", ""), cfg["user"]))
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    for filename, data in attachments:
        msg.add_attachment(
            data,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=filename,
        )

    with smtplib.SMTP(cfg["host"], int(cfg["port"])) as smtp:
        smtp.starttls()
        smtp.login(cfg["user"], cfg["password"])
        smtp.send_message(msg)
