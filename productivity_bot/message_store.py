# productivity_bot/message_store.py
from __future__ import annotations
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Deque, Tuple

# chat_id -> deque[(message_id, utc_timestamp)]
_STORE: dict[int, Deque[Tuple[int, datetime]]] = defaultdict(deque)

# keep only this many message IDs per chat
_MAX_KEEP = 300


def _remember(chat_id: int, message_id: int) -> None:
    dq = _STORE[chat_id]
    dq.append((message_id, datetime.utcnow()))
    if len(dq) > _MAX_KEEP:
        dq.popleft()


async def send_text(chat, text: str, **kwargs):
    """Send a text message & remember it."""
    m = await chat.send_message(text, **kwargs)
    _remember(chat.id, m.message_id)
    return m


async def send_animation(chat, animation: str, **kwargs):
    """Send an animation (GIF) & remember it."""
    m = await chat.send_animation(animation, **kwargs)
    _remember(chat.id, m.message_id)
    return m


async def send_photo(chat, photo, **kwargs):
    """Send a photo & remember it."""
    m = await chat.send_photo(photo, **kwargs)
    _remember(chat.id, m.message_id)
    return m


async def send_document(chat, document, **kwargs):
    """Send a document (Excel, PDF, etc.) & remember it."""
    m = await chat.send_document(document, **kwargs)
    _remember(chat.id, m.message_id)
    return m


async def clear_recent(bot, chat_id: int, within_hours: int = 48) -> int:
    """
    Delete remembered bot messages for this chat that are not older than `within_hours`.
    Returns number of messages successfully deleted.
    """
    dq = _STORE.get(chat_id)
    if not dq:
        return 0

    cutoff = datetime.utcnow() - timedelta(hours=within_hours)
    deleted = 0

    # newest-first (more likely deletable)
    for mid, ts in reversed(list(dq)):
        if ts >= cutoff:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=mid)
                deleted += 1
            except Exception:
                # ignore failures (too old, already gone, permissions)
                pass

    _STORE[chat_id].clear()
    return deleted
