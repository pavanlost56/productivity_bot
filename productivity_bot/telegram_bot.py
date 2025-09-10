from __future__ import annotations

import logging
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from .config import TELEGRAM_BOT_TOKEN, DEFAULT_TIMEZONE
from .google_calendar import list_events_between, add_event
from .utils import today_bounds, fmt_hhmm
from .voice_input import ogg_bytes_to_wav_bytes, transcribe_wav_bytes
from .ai_assistant import parse_task
from .excel_report import generate_report, EXCEL_FILE, DATA_DIR, log_task_update
from .gmail_client import send_report_email
from .message_store import (
    send_text, send_animation, send_photo, send_document, clear_recent
)

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("productivity_bot.telegram")


def _format_event(e: dict, tz_name: str) -> str:
    tz = ZoneInfo(tz_name)
    start = e.get("start", {})
    end = e.get("end", {})
    if "dateTime" in start:
        s = datetime.fromisoformat(start["dateTime"]).astimezone(tz)
        e_end = end.get("dateTime")
        if e_end:
            en = datetime.fromisoformat(e_end).astimezone(tz)
            return f"📝 {e.get('summary', '(no title)')}  ⏰ {fmt_hhmm(s)}–{fmt_hhmm(en)}"
        else:
            return f"📝 {e.get('summary', '(no title)')}  ⏰ {fmt_hhmm(s)}"
    else:
        return f"📝 {e.get('summary', '(no title)')}  📌 All day"


# === Commands ===

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("📅 Today", callback_data="today")],
        [InlineKeyboardButton("➕ Add Task", callback_data="add_task")],
        [InlineKeyboardButton("📊 Report", callback_data="report")],
        [InlineKeyboardButton("✅ Done", callback_data="done_info")],
        [InlineKeyboardButton("⏳ Pending", callback_data="pending_info")],
        [InlineKeyboardButton("🗑️ Clear Data", callback_data="clear")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = (
        "👋 *Welcome to Productivity Bot!*\n\n"
        "✨ I help you manage your day better.\n"
        "─────────────────────\n"
        "⚡ Commands:\n"
        "• `/today` → View today’s schedule\n"
        "• `/addtask <text>` → Add a task\n"
        "• `/done <task>` → Mark a task done (logs to Excel)\n"
        "• `/pending <task>` → Mark a task pending (logs to Excel)\n"
        "• `/report` → See progress report (Excel + chart)\n"
        "• `/clear` → Reset stats & remove recent bot messages\n"
        "─────────────────────\n"
        "🎙️ You can also send me a *voice note* to create tasks automatically."
    )
    await send_text(update.effective_chat, msg, parse_mode="Markdown", reply_markup=reply_markup)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)


async def today(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tz = DEFAULT_TIMEZONE
    start_dt, end_dt = today_bounds(tz)
    try:
        events = list_events_between(start_dt, end_dt, tz)
        if not events:
            await send_animation(
                update.effective_chat,
                "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
                caption="☀️ *No events today!* Relax, recharge, and focus 🎯",
                parse_mode="Markdown",
            )
            return

        lines = [f"📅 *Today's Schedule* _(Timezone: {tz})_", "─────────────────────"]
        for e in events:
            lines.append(_format_event(e, tz))

        keyboard = [
            [InlineKeyboardButton("➕ Add Task", callback_data="add_task")],
            [InlineKeyboardButton("📊 Report", callback_data="report")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await send_text(
            update.effective_chat,
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=reply_markup,
        )
    except Exception as e:
        log.exception("Failed to fetch today's events: %s", e)
        await send_text(update.effective_chat, "❌ Couldn’t fetch events. Check Google auth.")


async def addtask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(context.args) if context.args else None
    if not text:
        await send_text(update.effective_chat, "Usage: `/addtask <task description>`", parse_mode="Markdown")
        return

    parsed = parse_task(text, DEFAULT_TIMEZONE)
    if not parsed:
        await send_text(update.effective_chat, "❌ Sorry, I couldn’t understand that task.")
        return

    try:
        start_dt = datetime.fromisoformat(parsed["start"]).astimezone(ZoneInfo(DEFAULT_TIMEZONE))
        end_dt = datetime.fromisoformat(parsed["end"]).astimezone(ZoneInfo(DEFAULT_TIMEZONE))
        add_event(parsed["title"], start_dt, end_dt)

        await send_animation(
            update.effective_chat,
            "https://media.giphy.com/media/26xBukh7Pn9xq/200w.gif",
            caption=(
                f"✅ *Task Added!*\n"
                "─────────────────────\n"
                f"📝 {parsed['title']}\n"
                f"📅 {start_dt.strftime('%Y-%m-%d')}\n"
                f"⏰ {start_dt.strftime('%H:%M')} - {end_dt.strftime('%H:%M')}\n"
                "─────────────────────\n"
                "📌 Added to Google Calendar!"
            ),
            parse_mode="Markdown",
        )
    except Exception as e:
        log.exception("Addtask failed: %s", e)
        await send_text(update.effective_chat, "❌ Failed to add event.")


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(context.args).strip()
    if not text:
        await send_text(update.effective_chat, "Usage: `/done <task title>`", parse_mode="Markdown")
        return
    try:
        log_task_update(text, "done")
        await send_text(update.effective_chat, f"✅ Task marked as *done*: {text}", parse_mode="Markdown")
    except Exception as e:
        log.exception("Done failed: %s", e)
        await send_text(update.effective_chat, "❌ Could not mark as done.")


async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = " ".join(context.args).strip()
    if not text:
        await send_text(update.effective_chat, "Usage: `/pending <task title>`", parse_mode="Markdown")
        return
    try:
        log_task_update(text, "pending")
        await send_text(update.effective_chat, f"⏳ Task marked as *pending*: {text}", parse_mode="Markdown")
    except Exception as e:
        log.exception("Pending failed: %s", e)
        await send_text(update.effective_chat, "❌ Could not mark as pending.")


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        xlsx_path, png_path = generate_report()

        await send_text(update.effective_chat, "📊 *Your Progress Report!*", parse_mode="Markdown")
        # context managers to close files
        with open(xlsx_path, "rb") as f1:
            await send_document(update.effective_chat, document=f1)
        with open(png_path, "rb") as f2:
            await send_photo(update.effective_chat, photo=f2)

        # Also email it
        send_report_email(
            to_email="pavankumar22119@gmail.com",
            subject="📊 Productivity Report",
            body="Attached is your latest productivity report with Excel and chart.",
            attachments=[xlsx_path, png_path],
        )
        await send_text(update.effective_chat, "📧 Report also sent to your Gmail!")
    except FileNotFoundError:
        await send_text(update.effective_chat, "ℹ️ No data yet. Try adding and completing tasks first!")
    except Exception as e:
        log.exception("Report failed: %s", e)
        await send_text(update.effective_chat, "❌ Could not generate report.")


async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    try:
        # 1) delete bot messages we sent in this chat (≤48h)
        deleted = await clear_recent(context.bot, chat_id, within_hours=48)

        # 2) wipe local stats artifacts
        if EXCEL_FILE.exists():
            os.remove(EXCEL_FILE)
        png_file = DATA_DIR / "progress.png"
        if png_file.exists():
            os.remove(png_file)

        await send_text(
            update.effective_chat,
            f"🗑️ Chat cleaned.\n"
            f"• Deleted {deleted} recent bot messages\n"
            f"• Cleared progress data\n\n"
            f"✨ Fresh start!",
        )
    except Exception as e:
        log.exception("Clear failed: %s", e)
        await send_text(update.effective_chat, "❌ Could not clear data.")


# === Voice handler ===

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.voice:
        return
    try:
        tg_file = await update.message.voice.get_file()
        ogg_bytes = await tg_file.download_as_bytearray()
        wav_bytes = ogg_bytes_to_wav_bytes(bytes(ogg_bytes))
        text = transcribe_wav_bytes(wav_bytes)

        if text:
            await send_animation(
                update.effective_chat,
                "https://media.giphy.com/media/xT0xeJpnrWC4XWblEk/giphy.gif",
                caption=f"🗣️ You said: *{text}*",
                parse_mode="Markdown",
            )
            # OPTIONAL: auto-create tasks from voice
            # parsed = parse_task(text, DEFAULT_TIMEZONE)
            # if parsed:
            #     start_dt = datetime.fromisoformat(parsed["start"]).astimezone(ZoneInfo(DEFAULT_TIMEZONE))
            #     end_dt = datetime.fromisoformat(parsed["end"]).astimezone(ZoneInfo(DEFAULT_TIMEZONE))
            #     add_event(parsed["title"], start_dt, end_dt)
            #     await send_text(update.effective_chat, f"✅ Added task: {parsed['title']}")
        else:
            await send_text(update.effective_chat, "Hmm, I didn’t catch that. Try again?")
    except Exception as e:
        log.exception("Voice transcription failed: %s", e)
        await send_text(update.effective_chat, "❌ Voice transcription failed. Check FFmpeg + API key.")


# === Inline button handler ===

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query:
        return

    await query.answer()

    if query.data == "today":
        await today(update, context)
    elif query.data == "add_task":
        await send_text(update.effective_chat, "💡 Use `/addtask <task description>` to add a task.")
    elif query.data == "report":
        await report(update, context)
    elif query.data == "clear":
        await clear(update, context)
    elif query.data == "done_info":
        await send_text(update.effective_chat, "✅ Usage: `/done <task title>`", parse_mode="Markdown")
    elif query.data == "pending_info":
        await send_text(update.effective_chat, "⏳ Usage: `/pending <task title>`", parse_mode="Markdown")


# === Bot builder ===

def build_app() -> Application:
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set. Add it to your .env")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("addtask", addtask))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(CommandHandler("pending", pending))
    app.add_handler(CommandHandler("report", report))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(CallbackQueryHandler(button_handler))  # Inline buttons
    return app
