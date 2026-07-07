import base64
import html
import os
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

load_dotenv()

_INVISIBLE_CHARS = re.compile(r"[​‌‍‎‏͏﻿­⁠]+")


def _clean_snippet(text: str | None) -> str | None:
    if not text:
        return text
    return _INVISIBLE_CHARS.sub("", html.unescape(text)).strip()


SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailService:
    def __init__(self):
        client_id = os.environ.get("GMAIL_CLIENT_ID")
        client_secret = os.environ.get("GMAIL_CLIENT_SECRET")
        refresh_token = os.environ.get("GMAIL_REFRESH_TOKEN")

        if not all([client_id, client_secret, refresh_token]):
            raise ValueError(
                "GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, and GMAIL_REFRESH_TOKEN must be set"
            )

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            client_id=client_id,
            client_secret=client_secret,
            token_uri="https://oauth2.googleapis.com/token",
            scopes=SCOPES,
        )
        creds.refresh(Request())
        self.service = build("gmail", "v1", credentials=creds)

    # --- Search / Read ---

    def search(self, query: str, max_results: int = 75) -> list[dict]:
        result = (
            self.service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )

        messages = result.get("messages", [])
        return [self._get_summary(m["id"]) for m in messages]

    def get_message(self, message_id: str) -> dict:
        msg = (
            self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
        )
        return self._parse_full(msg)

    # --- Draft ---

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        reply_to_id: str | None = None,
        thread_id: str | None = None,
    ) -> dict:
        mime = self._build_mime(to, subject, body)
        raw = base64.urlsafe_b64encode(mime.as_bytes()).decode()
        draft_body: dict = {"message": {"raw": raw}}
        if thread_id:
            draft_body["message"]["threadId"] = thread_id

        draft = self.service.users().drafts().create(userId="me", body=draft_body).execute()
        return {"draft_id": draft["id"], "thread_id": draft.get("message", {}).get("threadId")}

    # --- Manage ---

    def mark_read(self, message_id: str) -> None:
        self.service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
        ).execute()

    def mark_unread(self, message_id: str) -> None:
        self.service.users().messages().modify(
            userId="me", id=message_id, body={"addLabelIds": ["UNREAD"]}
        ).execute()

    def archive(self, message_id: str) -> None:
        self.service.users().messages().modify(
            userId="me", id=message_id, body={"removeLabelIds": ["INBOX"]}
        ).execute()

    def trash(self, message_id: str) -> None:
        self.service.users().messages().trash(userId="me", id=message_id).execute()

    def add_label(self, message_id: str, label_name: str) -> None:
        label_id = self._get_or_create_label(label_name)
        self.service.users().messages().modify(
            userId="me", id=message_id, body={"addLabelIds": [label_id]}
        ).execute()

    # --- Helpers ---

    def _get_summary(self, message_id: str) -> dict:
        msg = (
            self.service.users()
            .messages()
            .get(
                userId="me",
                id=message_id,
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            )
            .execute()
        )

        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        return {
            "id": msg["id"],
            "thread_id": msg.get("threadId"),
            "snippet": _clean_snippet(msg.get("snippet")),
            "from": headers.get("From"),
            "to": headers.get("To"),
            "subject": headers.get("Subject"),
            "date": headers.get("Date"),
            "labels": msg.get("labelIds", []),
        }

    def _parse_full(self, msg: dict) -> dict:
        summary = self._get_summary(msg["id"])
        body = self._extract_body(msg.get("payload", {}))
        return {**summary, "body": body}

    def _extract_body(self, payload: dict) -> str:
        if payload.get("body", {}).get("data"):
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                "utf-8", errors="replace"
            )
        for part in payload.get("parts", []):
            if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                return base64.urlsafe_b64decode(part["body"]["data"]).decode(
                    "utf-8", errors="replace"
                )
        return ""

    def _build_mime(self, to: str, subject: str, body: str) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        return msg

    def _get_or_create_label(self, name: str) -> str:
        labels = self.service.users().labels().list(userId="me").execute().get("labels", [])
        for label in labels:
            if label["name"].lower() == name.lower():
                return label["id"]
        created = self.service.users().labels().create(userId="me", body={"name": name}).execute()
        return created["id"]


gmail_service = GmailService()
