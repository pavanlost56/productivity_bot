from __future__ import annotations

from .telegram_bot import build_app


def main():
    app = build_app()
    print("🚀 Bot starting... Press Ctrl+C to stop.")
    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
