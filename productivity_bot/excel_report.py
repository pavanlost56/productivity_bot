from __future__ import annotations
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

EXCEL_FILE = DATA_DIR / "progress.xlsx"


def log_task_update(task_title: str, status: str, date: datetime | None = None):
    """Append a row (date, task, status) to the Excel log."""
    date = date or datetime.now()
    row = {"date": date.strftime("%Y-%m-%d"), "task": task_title, "status": status}

    # Load existing or create new
    if EXCEL_FILE.exists():
        df = pd.read_excel(EXCEL_FILE)
    else:
        df = pd.DataFrame(columns=["date", "task", "status"])

    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)


def generate_report() -> tuple[str, str]:
    """Generate Excel and PNG chart. Returns (xlsx_path, png_path)."""
    if not EXCEL_FILE.exists():
        raise FileNotFoundError("No progress data yet. Log some tasks first.")

    df = pd.read_excel(EXCEL_FILE)

# Aggregate by date
daily = df.groupby(["date", "status"]).size().unstack(fill_value=0)

# Chart
fig, ax = plt.subplots(figsize=(6, 4))
daily.plot(kind="bar", stacked=True, ax=ax)
ax.set_ylabel("Tasks")
ax.set_title("Daily Progress")
plt.tight_layout()

png_path = DATA_DIR / "progress.png"
fig.savefig(png_path)
plt.close(fig)

return str(EXCEL_FILE), str(png_path)
