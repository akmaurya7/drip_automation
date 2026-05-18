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
    for c in [r"C:\Program Files\Tesseract-OCR\tesseract.exe",
              r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"]:
        if os.path.isfile(c):
            pytesseract.pytesseract.tesseract_cmd = c
            return
    print("WARNING: Tesseract not found. AM/PM OCR may fail.")

configure_tesseract()

# ─────────────────────────────────────────────
# Reference dimensions — actual screen: 1920 x 1080
# Measured directly from screenshot pixel analysis
# ─────────────────────────────────────────────
REF_W = 1920
REF_H = 1080

screen_w, screen_h = pyautogui.size()

# ── Row Y positions (pixel-accurate, measured from center of each row) ──
# Carefully measured from screenshot - center point of each collectible row
ROW_Y_POSITIONS = [390, 447, 499, 551, 605, 661, 714, 766, 818, 872]
ROWS_PER_PAGE   = len(ROW_Y_POSITIONS)

# Offset below the row center to click (adjust this value as needed)
ROW_Y_OFFSET    = 0

# X coordinate to click a row (center of the Name column)
ROW_CLICK_X = 998

# ── Pagination: ">" next-page button (pixel-accurate from screenshot) ──
# Clusters found: <<(974) <(1008) 1(1039) 3(1070) 4(1101) ...(1124) 78(1148) >(1179) >>(1203)
NEXT_PAGE_X = 1188
NEXT_PAGE_Y = 951

# ─────────────────────────────────────────────
# Core helpers
# ─────────────────────────────────────────────
def sc(x, y):
    """Scale reference coords to actual screen coords."""
    return int(x * screen_w / REF_W), int(y * screen_h / REF_H)

def click(x, y, label="", delay=1.0):
    cx, cy = sc(x, y)
    print(f"    → [{label}] at ({cx},{cy})")
    sys.stdout.flush()
    pyautogui.moveTo(cx, cy, duration=0.4)
    pyautogui.click()
    time.sleep(delay)

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
    ss = ss.resize((ss.width * 4, ss.height * 4), Image.NEAREST)
    text = pytesseract.image_to_string(
        ss, config="--psm 8 -c tessedit_char_whitelist=AMP"
    ).strip().upper()
    print(f"    → OCR AM/PM raw = '{text}'")
    sys.stdout.flush()
    return "AM" if "AM" in text else "PM"

# ─────────────────────────────────────────────
# Click a specific date on the open calendar
# ─────────────────────────────────────────────
def click_specific_date(target_dt):
    col_xs = [812, 850, 881, 921, 956, 994, 1027]  # Sun → Sat (calendar columns)
    row_ys = [447, 476, 509, 541, 570, 605]       # 6 rows of dates (calendar rows)

    today = datetime.now()
    months_diff = (target_dt.year - today.year) * 12 + (target_dt.month - today.month)
    for _ in range(months_diff):
        click(738, 283, "Next month →", delay=0.6)

    first_weekday_mon = calendar.monthrange(target_dt.year, target_dt.month)[0]
    first_col  = (first_weekday_mon + 1) % 7
    day_index  = first_col + (target_dt.day - 1)
    cell_row   = min(day_index // 7, len(row_ys) - 1)
    cell_col   = day_index % 7

    nx = col_xs[cell_col]
    ny = row_ys[cell_row]
    print(f"    → Date {target_dt.day} → grid row={cell_row} col={cell_col}")
    sys.stdout.flush()
    click(nx, ny, f"Date {target_dt.day}", delay=1.2)

# ─────────────────────────────────────────────
# Set hour / minute / AM/PM in calendar picker
# ─────────────────────────────────────────────
def set_time(hour_12, minute, ampm):
    triple_type(846, 638, f"{hour_12:02d}", "Hour")
    triple_type(950, 638, f"{minute:02d}",  "Minutes")
    current = read_ampm()
    if current != ampm:
        print(f"    → Currently {current} → switching to {ampm}")
        sys.stdout.flush()
        click(1023, 638, f"Toggle to {ampm}", delay=0.8)
    else:
        print(f"    → Already {ampm} ✓")
        sys.stdout.flush()

# ─────────────────────────────────────────────
# Full flow for one collectible row
# ─────────────────────────────────────────────
def process_one(global_index, row_y, target_dt):
    h24    = target_dt.hour
    minute = target_dt.minute
    ampm   = "AM" if h24 < 12 else "PM"
    h12    = h24 % 12 or 12

    print(f"\n{'═'*60}")
    print(f"  COLLECTIBLE #{global_index+1}  →  {target_dt.strftime('%d/%m/%Y  %I:%M %p')}")
    print(f"{'═'*60}")
    sys.stdout.flush()

    click(ROW_CLICK_X, row_y + ROW_Y_OFFSET,  f"Row #{global_index+1}",  delay=2.5)
    click(1422, 351,           "New Store",                delay=2.0)
    click(950,  399,           "Clear Date",               delay=1.2)
    click(850,  361,           "Date/time field",          delay=1.5)
    click_specific_date(target_dt)
    set_time(h12, minute, ampm)
    click(1050,  899,           "Save",                     delay=2.5)
    click(32,   99,            "Browser back",             delay=2.0)
    print(f"  ✅ #{global_index+1} done!")
    sys.stdout.flush()

# ─────────────────────────────────────────────
# Navigate to next page
# ─────────────────────────────────────────────
def go_next_page():
    print(f"\n  ─── Navigating to next page ──►")
    sys.stdout.flush()
    click(NEXT_PAGE_X, NEXT_PAGE_Y, "Next page >", delay=2.5)


# ════════════════════════════════════════════════════════
#  INPUT HELPERS
# ════════════════════════════════════════════════════════

def parse_datetime(raw):
    try:
        return datetime.strptime(raw.strip(), "%d/%m/%Y %I:%M %p")
    except ValueError:
        return None

def ask_datetime(label):
    print(f"\n  Enter {label}")
    sys.stdout.flush()
    print("  Format  : DD/MM/YYYY HH:MM AM/PM")
    print("  Example : 12/05/2026 12:17 AM")
    sys.stdout.flush()
    while True:
        raw = input("  >> ").strip()
        dt  = parse_datetime(raw)
        if dt:
            return dt
        print("  ❌  Invalid! Use exactly: DD/MM/YYYY HH:MM AM/PM")
        print("      e.g. 12/05/2026 12:17 AM  or  12/05/2026 01:30 PM")
        sys.stdout.flush()

def ask_int(prompt, lo, hi):
    while True:
        try:
            v = int(input(f"  {prompt} [{lo}-{hi}]: ").strip())
            if lo <= v <= hi:
                return v
            print(f"  ❌  Enter a number between {lo} and {hi}")
            sys.stdout.flush()
        except ValueError:
            print("  ❌  Please enter a valid whole number")
            sys.stdout.flush()

def ask_increment():
    print("\n  Time increment between GROUPS or collectibles (minutes)")
    print("  Example: 30 → each group/collectible is +30 min from previous")
    sys.stdout.flush()
    while True:
        try:
            v = int(input("  >> ").strip())
            if v >= 0:
                return v
            print("  ❌  Enter 0 or a positive number")
            sys.stdout.flush()
        except ValueError:
            print("  ❌  Please enter a valid whole number")
            sys.stdout.flush()


# ════════════════════════════════════════════════════════
#  BUILD SCHEDULE
# ════════════════════════════════════════════════════════

def build_schedule(total, mode, start_dt, increment_min, group_size=1):
    """
    Returns list of datetime objects, one per collectible.

    mode='group':
      - collectibles are grouped in chunks of `group_size`
      - all items in a group share the same time
      - each group increments by `increment_min`

    mode='individual':
      - each collectible gets start + (index * increment_min)
    """
    schedules = []
    for i in range(total):
        if mode == "group":
            group_index = i // group_size
            dt = start_dt + timedelta(minutes=increment_min * group_index)
        else:
            dt = start_dt + timedelta(minutes=increment_min * i)
        schedules.append(dt)
    return schedules


# ════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════

print("\n" + "★"*60)
print("  DRIP Collectibles — Multi-Page Automation")
print("★"*60)
sys.stdout.flush()

# ── Q1: Total collectibles ──────────────────────────────
print()
sys.stdout.flush()
total = ask_int("How many total collectibles to schedule", 1, 800)

# ── Q2: Mode ───────────────────────────────────────────
print("""
  Scheduling mode:
    1. GROUP      → N collectibles share the same time, then increment
    2. INDIVIDUAL → each collectible gets start time + increment
""")
sys.stdout.flush()
while True:
    mode_input = input("  Enter 1 (Group) or 2 (Individual): ").strip()
    if mode_input in ("1", "2"):
        break
    print("  ❌  Please enter 1 or 2")
    sys.stdout.flush()

group_size = 1
if mode_input == "1":
    group_size = ask_int("How many collectibles per group", 1, total)

# ── Q3: Start date & time ──────────────────────────────
start_dt = ask_datetime("start date & time for the first collectible/group")

# ── Q4: Increment ─────────────────────────────────────
increment_min = ask_increment()

# ── Build full schedule ────────────────────────────────
mode      = "group" if mode_input == "1" else "individual"
schedules = build_schedule(total, mode, start_dt, increment_min, group_size)

# ── Summary ────────────────────────────────────────────
total_groups = math.ceil(total / group_size) if mode == "group" else total
pages_needed = math.ceil(total / ROWS_PER_PAGE)

print("\n" + "─"*60)
print("  SCHEDULE SUMMARY")
print("─"*60)
print(f"  Total collectibles : {total}")
print(f"  Mode               : {'GROUP ('+str(group_size)+' per group)' if mode=='group' else 'INDIVIDUAL'}")
print(f"  Increment          : {increment_min} min")
print(f"  Pages to process   : {pages_needed}")
print("─"*60)
sys.stdout.flush()

# Show preview (max 30 lines to avoid flood)
preview_count = min(total, 30)
for i in range(preview_count):
    dt = schedules[i]
    print(f"  #{i+1:03d}  →  {dt.strftime('%d/%m/%Y   %I:%M %p')}")
    sys.stdout.flush()
if total > 30:
    print(f"  ... ({total - 30} more not shown)")
print("─"*60)
sys.stdout.flush()

confirm = input("\n  Start automation? (y/n): ").strip().lower()
if confirm != "y":
    print("\n  Cancelled.")
    sys.stdout.flush()
    exit()

# ── Countdown ──────────────────────────────────────────
print("\n" + "★"*60)
print("  Starting in 5 seconds!")
print("  Switch to browser → collectibles list PAGE 1 NOW!")
print("★"*60)
sys.stdout.flush()
for i in range(5, 0, -1):
    print(f"  {i}...")
    sys.stdout.flush()
    time.sleep(1)
print("  GO!\n")
sys.stdout.flush()

# ── Run — page by page ─────────────────────────────────
processed    = 0
current_page = 0   # 0-indexed

while processed < total:
    # How many rows to process on this page
    rows_this_page = min(ROWS_PER_PAGE, total - processed)

    print(f"\n{'▓'*60}")
    print(f"  PAGE {current_page + 1}  —  processing rows 1-{rows_this_page}")
    print(f"{'▓'*60}")
    sys.stdout.flush()

    for row_slot in range(rows_this_page):
        global_index = processed + row_slot
        row_y        = ROW_Y_POSITIONS[row_slot]
        target_dt    = schedules[global_index]
        process_one(global_index, row_y, target_dt)

    processed += rows_this_page

    # If more collectibles remain, go to next page
    if processed < total:
        go_next_page()
        current_page += 1

print(f"\n\n🎉  All {total} collectibles scheduled successfully!")
sys.stdout.flush()
