"""Parsed Allegro message center models and message templates."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

CATEGORY_INVOICE = "invoice"
CATEGORY_ORDER_STATUS = "order_status"
CATEGORY_OTHER = "other"
CATEGORIES = (CATEGORY_ORDER_STATUS, CATEGORY_INVOICE, CATEGORY_OTHER)

PREVIEW_LENGTH = 200
ATTACHMENT_HOST = "upload.allegro.pl"

# A message is an invoice when it names a sales document right next to a word that
# says it is attached, sent or linked. Checked before the order status templates, so
# invoice mails that also thank for the order are never treated as noise.
_DOCUMENT = r"(?:faktur|dokument\w* sprzeda|paragon)"
_ATTACHED = r"(?:załącz|przesy[łl]|dołącz|wysy[łl]am)"
INVOICE_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        rf"{_DOCUMENT}\w*[^.]{{0,80}}{_ATTACHED}",
        rf"{_ATTACHED}\w*[^.]{{0,80}}{_DOCUMENT}",
        r"^faktura\b",
        r"link do dokument\w* sprzeda",
    )
)
# Returns, complaints and cancellations are written by hand or need a reaction.
_NEEDS_ATTENTION = re.compile(r"zwrot|reklamac|anulowan|odstąpieni")

# Automatic order status templates sent by shops. Matched on the lowercased,
# whitespace-collapsed preview. Add a pattern here to recognise a new shop template.
ORDER_STATUS_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(pattern)
    for pattern in (
        r"zamówienie jest realizowane",
        r"trafiło do realizacji",
        r"czeka na realizację",
        r"w trakcie kompletowania",
        r"zamówienie (?:zostało )?(?:przyjęte|przekazane do realizacji)",
        r"dziękujemy za (?:zakupy|złożenie zamówienia|zamówienie|zaufanie)",
        r"zamówienie\b[^.!?]{0,60}(?:przygotowan|skompletowan|spakowan|zrealizowan)",
        (
            r"(?:zamówienie|przesyłka|paczka)\b[^.!?]{0,40}"
            r"(?:zostało|została|zostanie) (?:nadan|wysłan)"
        ),
        r"potwierdzenie (?:zamówienia|zakupu|wysyłki)",
    )
)


def _collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def classify_message(preview: str) -> str:
    """Return the message category for a thread preview."""
    text = _collapse(preview).casefold()
    if any(pattern.search(text) for pattern in INVOICE_PATTERNS):
        return CATEGORY_INVOICE
    # A question or free-form text from a person is never automatic noise.
    if "?" in text or _NEEDS_ATTENTION.search(text):
        return CATEGORY_OTHER
    if any(pattern.search(text) for pattern in ORDER_STATUS_PATTERNS):
        return CATEGORY_ORDER_STATUS
    return CATEGORY_OTHER


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class MessageThread:
    """Single conversation in the Allegro message center."""

    id: str
    seller: str
    preview: str
    timestamp: str | None
    read: bool
    category: str

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> MessageThread:
        """Create a thread from a `threads/view/list` item."""
        preview = str(item.get("subtitle") or "")
        return cls(
            id=str(item.get("id") or ""),
            seller=str(item.get("title") or ""),
            preview=preview,
            timestamp=item.get("timestamp"),
            read=bool(item.get("read", True)),
            category=classify_message(preview),
        )

    def age_days(self, now: datetime) -> float | None:
        """Days since the last message, or None when the timestamp is unusable."""
        parsed = _parse_timestamp(self.timestamp)
        if parsed is None or parsed.tzinfo is None:
            return None
        return (now - parsed).total_seconds() / 86400

    def as_attributes(self) -> dict[str, Any]:
        """State attributes for dashboards."""
        return {
            "thread_id": self.id,
            "seller": self.seller,
            "category": self.category,
            "timestamp": self.timestamp,
            "read": self.read,
            "preview": _collapse(self.preview)[:PREVIEW_LENGTH],
        }

    def as_read(self) -> MessageThread:
        """Copy of the thread marked as read."""
        return MessageThread(
            id=self.id,
            seller=self.seller,
            preview=self.preview,
            timestamp=self.timestamp,
            read=True,
            category=self.category,
        )


@dataclass(frozen=True, slots=True)
class Attachment:
    """File attached to a message, for example an invoice PDF."""

    url: str
    file_name: str


@dataclass(frozen=True, slots=True)
class Messages:
    """Unread counter and the most recent threads."""

    unread: int = 0
    threads: tuple[MessageThread, ...] = field(default_factory=tuple)

    @property
    def unread_threads(self) -> list[MessageThread]:
        return [thread for thread in self.threads if not thread.read]

    @property
    def invoices(self) -> list[MessageThread]:
        return [t for t in self.threads if t.category == CATEGORY_INVOICE]

    def get(self, thread_id: str) -> MessageThread | None:
        return next((t for t in self.threads if t.id == thread_id), None)

    def unread_in_category(self, category: str) -> list[MessageThread]:
        return [t for t in self.unread_threads if t.category == category]

    def with_read(self, thread_ids: set[str]) -> Messages:
        """Copy with the given threads marked as read and the counter lowered."""
        newly_read = sum(1 for t in self.threads if t.id in thread_ids and not t.read)
        return Messages(
            unread=max(0, self.unread - newly_read),
            threads=tuple(
                t.as_read() if t.id in thread_ids else t for t in self.threads
            ),
        )

    def auto_read_candidates(
        self, active_sellers: set[str], days: float, now: datetime
    ) -> list[MessageThread]:
        """Unread automatic order messages that no longer need attention.

        A message qualifies when the seller has no order still on its way, or when
        the message is at least `days` old.
        """
        candidates = []
        for thread in self.unread_in_category(CATEGORY_ORDER_STATUS):
            age = thread.age_days(now)
            if thread.seller not in active_sellers or (age is not None and age >= days):
                candidates.append(thread)
        return candidates


def parse_messages(unread: int, payloads: list[dict[str, Any]]) -> Messages:
    """Build messages from the counter and pages of `threads/view/list`."""
    threads: list[MessageThread] = []
    seen: set[str] = set()
    for payload in payloads:
        for item in payload.get("threads") or []:
            if not isinstance(item, dict):
                continue
            thread = MessageThread.from_api(item)
            if thread.id and thread.id not in seen:
                seen.add(thread.id)
                threads.append(thread)
    return Messages(unread=unread, threads=tuple(threads))


def parse_attachments(chat: Any) -> list[Attachment]:
    """Collect downloadable attachments from a `facade/chats/{id}` payload."""
    found: list[Attachment] = []
    seen: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            action = node.get("action")
            if isinstance(action, dict) and action.get("actionType") == "DOWNLOAD":
                params = action.get("params")
                params = params if isinstance(params, dict) else {}
                url = params.get("absolutePath")
                if isinstance(url, str) and url not in seen:
                    seen.add(url)
                    found.append(
                        Attachment(url=url, file_name=str(params.get("fileName") or ""))
                    )
            for value in node.values():
                walk(value)

    walk(chat)
    return found
