import pyautogui
import time
import sys
import numpy as np
import pytesseract
import shutil
import os
import calendar
import math
from PIL import ImageGrab, Image
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# Tesseract auto-detect
# ─────────────────────────────────────────────
def configure_tesseract():
    env_path = os.environ.get("TESSERACT_CMD") or os.environ.get("TESSERACT")

    if env_path and os.path.isfile(env_path):
        pytesseract.pytesseract.tesseract_cmd = env_path
        return

    which = shutil.which("tesseract")
    if which:
        pytesseract.pytesseract.tesseract_cmd = which
        return

    for c in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
    ]:
        if os.path.isfile(c):
            pytesseract.pytesseract.tesseract_cmd = c
            return

    print("WARNING: Tesseract not found. OCR may fail.")

configure_tesseract()

# ─────────────────────────────────────────────
# Reference Resolution
# ─────────────────────────────────────────────
REF_W = 1920
REF_H = 1080

screen_w, screen_h = pyautogui.size()

# ─────────────────────────────────────────────
# Collectible Row Positions
# ─────────────────────────────────────────────
ROW_Y_POSITIONS = [
    390,
    447,
    499,
    551,
    605,
    661,
    714,
    766,
    818,
    872
]

ROWS_PER_PAGE = len(ROW_Y_POSITIONS)

ROW_Y_OFFSET = 50
ROW_CLICK_X = 998

# ─────────────────────────────────────────────
# Pagination Button Ratios
# Recalculated every time dynamically
# ─────────────────────────────────────────────
NEXT_PAGE_X_RATIO = 1187 / REF_W
NEXT_PAGE_Y_RATIO = 992 / REF_H

# ─────────────────────────────────────────────
# Core Helpers
# ─────────────────────────────────────────────
def sc(x, y):
    return (
        int(x * screen_w / REF_W),
        int(y * screen_h / REF_H)
    )

def get_next_page_xy():
    return (
        int(screen_w * NEXT_PAGE_X_RATIO),
        int(screen_h * NEXT_PAGE_Y_RATIO)
    )

def click(x, y, label="", delay=1.0):
    cx, cy = sc(x, y)

    print(f"    → [{label}] at ({cx},{cy})")
    sys.stdout.flush()

    pyautogui.moveTo(cx, cy, duration=0.4)
    pyautogui.click()

    time.sleep(delay)

def scroll_to_top():
    print("    → Scrolling to top")
    sys.stdout.flush()

    pyautogui.hotkey("ctrl", "home")

    time.sleep(1.5)

def triple_type(x, y, value, label=""):
    cx, cy = sc(x, y)

    print(f"    → Setting [{label}] = '{value}'")
    sys.stdout.flush()

    pyautogui.moveTo(cx, cy, duration=0.3)

    pyautogui.tripleClick()

    time.sleep(0.2)

    pyautogui.typewrite(str(value), interval=0.12)

    time.sleep(0.4)

def read_ampm():
    x1, y1 = sc(1004, 624)
    x2, y2 = sc(1036, 647)

    ss = ImageGrab.grab(bbox=(x1, y1, x2, y2))

    ss = ss.resize(
        (ss.width * 4, ss.height * 4),
        Image.NEAREST
    )

    text = pytesseract.image_to_string(
        ss,
        config="--psm 8 -c tessedit_char_whitelist=AMP"
    ).strip().upper()

    print(f"    → OCR AM/PM raw = '{text}'")
    sys.stdout.flush()

    return "AM" if "AM" in text else "PM"

# ─────────────────────────────────────────────
# Calendar Date Selection
# ─────────────────────────────────────────────
def click_specific_date(target_dt):

    col_xs = [
        812,
        850,
        881,
        921,
        956,
        994,
        1027
    ]

    row_ys = [
        447,
        476,
        509,
        541,
        570,
        605
    ]

    today = datetime.now()

    months_diff = (
        (target_dt.year - today.year) * 12
        + (target_dt.month - today.month)
    )

    for _ in range(months_diff):
        click(738, 283, "Next month →", delay=0.6)

    first_weekday_mon = calendar.monthrange(
        target_dt.year,
        target_dt.month
    )[0]

    first_col = (first_weekday_mon + 1) % 7

    day_index = first_col + (target_dt.day - 1)

    cell_row = min(day_index // 7, len(row_ys) - 1)

    cell_col = day_index % 7

    nx = col_xs[cell_col]
    ny = row_ys[cell_row]

    print(
        f"    → Date {target_dt.day} "
        f"→ row={cell_row} col={cell_col}"
    )

    sys.stdout.flush()

    click(nx, ny, f"Date {target_dt.day}", delay=0.8)

# ─────────────────────────────────────────────
# Set Time
# ─────────────────────────────────────────────
def set_time(hour_12, minute, ampm):

    triple_type(846, 638, f"{hour_12:02d}", "Hour")

    triple_type(950, 638, f"{minute:02d}", "Minutes")

    current = read_ampm()

    if current != ampm:

        print(f"    → Switching {current} → {ampm}")
        sys.stdout.flush()

        click(
            1023,
            638,
            f"Toggle to {ampm}",
            delay=0.8
        )

    else:
        print(f"    → Already {ampm} ✓")
        sys.stdout.flush()

# ─────────────────────────────────────────────
# Process One Collectible
# ─────────────────────────────────────────────
def process_one(global_index, row_y, target_dt):

    h24 = target_dt.hour

    minute = target_dt.minute

    ampm = "AM" if h24 < 12 else "PM"

    h12 = h24 % 12 or 12

    print(f"\n{'═'*60}")
    print(
        f"  COLLECTIBLE #{global_index+1}  →  "
        f"{target_dt.strftime('%d/%m/%Y  %I:%M %p')}"
    )
    print(f"{'═'*60}")

    sys.stdout.flush()

    click(
        ROW_CLICK_X,
        row_y + ROW_Y_OFFSET,
        f"Row #{global_index+1}",
        delay=2.5
    )

    click(1422, 351, "New Store", delay=2.0)

    click(950, 399, "Clear Date", delay=0.5)

    click(850, 361, "Date/time field", delay=0.5)

    click_specific_date(target_dt)

    set_time(h12, minute, ampm)

    click(1050, 899, "Save", delay=1.0)

    click(32, 99, "Browser back", delay=2.0)

    # Scroll to top after every back
    scroll_to_top()

    print(f"  ✅ #{global_index+1} done!")

    sys.stdout.flush()

# ─────────────────────────────────────────────
# Go To Next Page
# ─────────────────────────────────────────────
def go_next_page():

    print(f"\n  ─── Navigating to next page ──►")

    sys.stdout.flush()

    x, y = get_next_page_xy()

    print(f"    → Next page button at ({x},{y})")

    pyautogui.moveTo(x, y, duration=0.4)

    pyautogui.click()

    time.sleep(3)

    # Scroll top again after page change
    scroll_to_top()

# ═════════════════════════════════════════════
# Input Helpers
# ═════════════════════════════════════════════
def parse_datetime(raw):

    try:
        return datetime.strptime(
            raw.strip(),
            "%d/%m/%Y %I:%M %p"
        )

    except ValueError:
        return None

def ask_datetime(label):

    print(f"\n  Enter {label}")

    print("  Format  : DD/MM/YYYY HH:MM AM/PM")

    print("  Example : 12/05/2026 12:17 AM")

    sys.stdout.flush()

    while True:

        raw = input("  >> ").strip()

        dt = parse_datetime(raw)

        if dt:
            return dt

        print("  ❌ Invalid format")
        sys.stdout.flush()

def ask_int(prompt, lo, hi):

    while True:

        try:
            v = int(
                input(f"  {prompt} [{lo}-{hi}]: ").strip()
            )

            if lo <= v <= hi:
                return v

            print(f"  ❌ Enter between {lo}-{hi}")

        except ValueError:
            print("  ❌ Invalid number")

        sys.stdout.flush()

def ask_increment():

    print("\n  Time increment between collectibles/groups")

    while True:

        try:
            v = int(input("  >> ").strip())

            if v >= 0:
                return v

            print("  ❌ Must be positive")

        except ValueError:
            print("  ❌ Invalid number")

        sys.stdout.flush()

# ═════════════════════════════════════════════
# Schedule Builder
# ═════════════════════════════════════════════
def build_schedule(
    total,
    mode,
    start_dt,
    increment_min,
    group_size=1
):

    schedules = []

    for i in range(total):

        if mode == "group":

            group_index = i // group_size

            dt = start_dt + timedelta(
                minutes=increment_min * group_index
            )

        else:

            dt = start_dt + timedelta(
                minutes=increment_min * i
            )

        schedules.append(dt)

    return schedules

# ═════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════
print("\n" + "★"*60)

print("  DRIP Collectibles — Multi-Page Automation")

print("★"*60)

sys.stdout.flush()

# Total collectibles
total = ask_int(
    "How many total collectibles to schedule",
    1,
    550
)

# Mode
print("""
  Scheduling mode:

    1. GROUP
       Multiple collectibles share same time

    2. INDIVIDUAL
       Every collectible gets unique time
""")

while True:

    mode_input = input(
        "  Enter 1 or 2: "
    ).strip()

    if mode_input in ("1", "2"):
        break

    print("  ❌ Enter 1 or 2")

group_size = 1

if mode_input == "1":

    group_size = ask_int(
        "How many collectibles per group",
        1,
        total
    )

# Start datetime
start_dt = ask_datetime(
    "start date & time"
)

# Increment
increment_min = ask_increment()

# Starting row
start_row = ask_int(
    "Which row to start on",
    1,
    ROWS_PER_PAGE
) - 1  # Convert to 0-indexed

mode = (
    "group"
    if mode_input == "1"
    else "individual"
)

schedules = build_schedule(
    total,
    mode,
    start_dt,
    increment_min,
    group_size
)

# Summary
total_groups = (
    math.ceil(total / group_size)
    if mode == "group"
    else total
)

pages_needed = math.ceil(
    total / ROWS_PER_PAGE
)

print("\n" + "─"*60)

print("  SCHEDULE SUMMARY")

print("─"*60)

print(f"  Total collectibles : {total}")

print(
    f"  Mode               : "
    f"{'GROUP' if mode=='group' else 'INDIVIDUAL'}"
)

print(f"  Increment          : {increment_min} min")

print(f"  Pages needed       : {pages_needed}")

print("─"*60)

# Preview
preview_count = min(total, 30)

for i in range(preview_count):

    dt = schedules[i]

    print(
        f"  #{i+1:03d} → "
        f"{dt.strftime('%d/%m/%Y  %I:%M %p')}"
    )

if total > 30:
    print(f"  ... {total-30} more")

print("─"*60)

sys.stdout.flush()

confirm = input(
    "\n  Start automation? (y/n): "
).strip().lower()

if confirm != "y":

    print("\n  Cancelled.")

    exit()

# Countdown
print("\n" + "★"*60)

print("  Starting in 5 seconds!")

print("  Open DRIP collectibles page NOW")

print("★"*60)

for i in range(5, 0, -1):

    print(f"  {i}...")

    sys.stdout.flush()

    time.sleep(1)

print("  GO!\n")

# Initial scroll to top
scroll_to_top()

# ─────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────
processed = 0

current_page = 0

first_page = True

while processed < total:

    # Always scroll to top at start of page
    scroll_to_top()

    rows_this_page = min(
        ROWS_PER_PAGE,
        total - processed
    )

    print(f"\n{'▓'*60}")

    print(
        f"  PAGE {current_page + 1} "
        f"— rows 1-{rows_this_page}"
    )

    print(f"{'▓'*60}")

    sys.stdout.flush()

    # On first page, start from start_row; on subsequent pages, start from 0
    row_start = start_row if first_page else 0

    # How many rows we can process on this page starting from row_start
    available_slots = ROWS_PER_PAGE - row_start
    items_on_page = min(rows_this_page, available_slots)

    for i in range(items_on_page):
        row_slot = row_start + i
        global_index = processed + i

        row_y = ROW_Y_POSITIONS[row_slot]
        target_dt = schedules[global_index]

        process_one(
            global_index,
            row_y,
            target_dt
        )

    # Increase processed by actual items handled on this page
    processed += items_on_page

    first_page = False

    # Next page
    if processed < total:
        go_next_page()

        current_page += 1

print(f"\n\n🎉 All {total} collectibles scheduled successfully!")