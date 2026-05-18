import pyautogui
import time
import sys
import numpy as np
import pytesseract
import shutil
import os
import calendar
import math
import random
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
# Collectible Row Positions  (ref 1920×1080)
# These are the TOP-EDGE Y coords of each row.
# All clicks and scans use row_y + ROW_Y_OFFSET
# to hit the vertical centre of each row.
# ─────────────────────────────────────────────
ROW_Y_POSITIONS = [
    390, 447, 499, 551, 605,
    661, 714, 766, 818, 872
]
ROWS_PER_PAGE = len(ROW_Y_POSITIONS)

ROW_Y_OFFSET = 50   # shift from row top-edge → row centre (clicks AND scans)
ROW_CLICK_X  = 998

# ─────────────────────────────────────────────
# Pagination
# ─────────────────────────────────────────────
NEXT_PAGE_X_RATIO = 1187 / REF_W
NEXT_PAGE_Y_RATIO = 992  / REF_H

# ═══════════════════════════════════════════════════════════════
# SKIP-DETECTION CONSTANTS  (ref 1920×1080)
#
# All X coords reference the rarity icon and supply column.
# Scans are performed at (row_y + ROW_Y_OFFSET) so they align
# with the actual vertical centre of each row — matching the
# click target exactly.
# ═══════════════════════════════════════════════════════════════
RARITY_ICON_X      = 1227   # ref X centre of rarity icon
RARITY_ICON_HALF_W = 16     # ±px around centre (horizontal)
RARITY_ICON_HALF_H = 8      # ±px around centre (vertical)

SUPPLY_SCAN_X1     = 1280   # ref left  edge of supply column
SUPPLY_SCAN_X2     = 1420   # ref right edge of supply column
SUPPLY_SCAN_HALF_H = 12     # ±px around row centre (vertical)

# Skip thresholds
PINK_SKIP_SUPPLY   = 5      # pink  icon + supply==5  → skip
WHITE_SKIP_SUPPLY  = 1      # white icon + supply==1  → skip


# ─────────────────────────────────────────────
# Core Helpers
# ─────────────────────────────────────────────
def sc(x, y):
    """Scale reference coords (1920×1080) to actual screen resolution."""
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
    ss = ss.resize((ss.width * 4, ss.height * 4), Image.NEAREST)
    text = pytesseract.image_to_string(
        ss, config="--psm 8 -c tessedit_char_whitelist=AMP"
    ).strip().upper()
    print(f"    → OCR AM/PM raw = '{text}'")
    sys.stdout.flush()
    return "AM" if "AM" in text else "PM"


# ═══════════════════════════════════════════════════════════════
#  RARITY + SUPPLY DETECTION
#
#  BUG FIX (v3): Both detect_rarity_color() and read_supply_value()
#  previously scanned at raw `row_y` (the top-edge of the row).
#  This caused every scan to read ~50px above the intended row,
#  resulting in an off-by-one skip error (e.g. row 2 skipped
#  instead of row 1, or vice-versa).
#
#  Fix: scan at `scan_y = row_y + ROW_Y_OFFSET` — identical to
#  the Y coordinate used for clicking — so the scan window is
#  centred on the same pixel the click targets.
# ═══════════════════════════════════════════════════════════════

def detect_rarity_color(row_y):
    """
    Grab the rarity-icon pixel patch and classify as 'pink', 'white', or 'other'.

    Scans at row_y + ROW_Y_OFFSET to align with the actual vertical
    centre of the row (same Y as the click target).

    Pink  (rare)   : R>180, G<140, B<160, R dominates
    White (common) : R>190, G>190, B>190
    """
    scan_y = row_y + ROW_Y_OFFSET          # ← FIXED (was: row_y)

    sx1, sy1 = sc(RARITY_ICON_X - RARITY_ICON_HALF_W,
                  scan_y         - RARITY_ICON_HALF_H)
    sx2, sy2 = sc(RARITY_ICON_X + RARITY_ICON_HALF_W,
                  scan_y         + RARITY_ICON_HALF_H)

    ss     = ImageGrab.grab(bbox=(sx1, sy1, sx2, sy2))
    pixels = ss.load()
    w, h   = ss.size

    pink_count = white_count = 0
    for px in range(w):
        for py in range(h):
            r, g, b = pixels[px, py][:3]
            if r > 180 and g < 140 and b < 160 and r > g + 60:
                pink_count += 1
            elif r > 190 and g > 190 and b > 190:
                white_count += 1

    print(f"    [rarity] scan_y={scan_y}  pink_px={pink_count}  "
          f"white_px={white_count}  area={w*h}")
    sys.stdout.flush()

    if pink_count >= 3 and pink_count > white_count:
        return "pink"
    elif white_count >= 3 and white_count > pink_count:
        return "white"
    return "other"


def read_supply_value(row_y):
    """
    OCR the Supply column for this row.

    Scans at row_y + ROW_Y_OFFSET to align with the actual vertical
    centre of the row (same Y as the click target).

    Returns int or None on failure.
    """
    scan_y = row_y + ROW_Y_OFFSET          # ← FIXED (was: row_y)

    sx1, sy1 = sc(SUPPLY_SCAN_X1, scan_y - SUPPLY_SCAN_HALF_H)
    sx2, sy2 = sc(SUPPLY_SCAN_X2, scan_y + SUPPLY_SCAN_HALF_H)

    ss     = ImageGrab.grab(bbox=(sx1, sy1, sx2, sy2))
    scale  = 4
    ss_big = ss.resize((ss.width * scale, ss.height * scale), Image.LANCZOS)

    try:
        text   = pytesseract.image_to_string(
            ss_big,
            config="--psm 7 -c tessedit_char_whitelist=0123456789"
        ).strip()
        digits = ''.join(c for c in text if c.isdigit())
        if digits:
            val = int(digits)
            print(f"    [supply OCR] scan_y={scan_y}  raw='{text}'  parsed={val}")
            sys.stdout.flush()
            return val
        print(f"    [supply OCR] scan_y={scan_y}  no digits in '{text}'")
    except Exception as e:
        print(f"    ⚠  Supply OCR error: {e}")
    sys.stdout.flush()
    return None


def should_skip_row(row_y):
    """
    Returns (skip: bool, reason: str).

    Rules:
      pink  icon + supply == PINK_SKIP_SUPPLY  → skip
      white icon + supply == WHITE_SKIP_SUPPLY → skip
    """
    rarity = detect_rarity_color(row_y)
    supply = read_supply_value(row_y)

    if supply is None:
        msg = "supply unreadable — NOT skipping (safe default)"
        print(f"    ⚠  {msg}")
        sys.stdout.flush()
        return False, msg

    if rarity == "pink"  and supply == PINK_SKIP_SUPPLY:
        return True, f"pink icon, supply={supply}"
    if rarity == "white" and supply == WHITE_SKIP_SUPPLY:
        return True, f"white icon, supply={supply}"

    return False, f"rarity={rarity}, supply={supply} — OK"


# ─────────────────────────────────────────────
# Calendar Date Selection
# ─────────────────────────────────────────────
def click_specific_date(target_dt):
    col_xs = [812, 850, 881, 921, 956, 994, 1027]
    row_ys = [447, 476, 509, 541, 570, 605]

    today = datetime.now()
    months_diff = (
        (target_dt.year  - today.year)  * 12
        + (target_dt.month - today.month)
    )
    for _ in range(months_diff):
        click(738, 283, "Next month →", delay=0.6)

    first_weekday_mon = calendar.monthrange(target_dt.year, target_dt.month)[0]
    first_col  = (first_weekday_mon + 1) % 7
    day_index  = first_col + (target_dt.day - 1)
    cell_row   = min(day_index // 7, len(row_ys) - 1)
    cell_col   = day_index % 7
    nx, ny     = col_xs[cell_col], row_ys[cell_row]

    print(f"    → Date {target_dt.day} → row={cell_row} col={cell_col}")
    sys.stdout.flush()
    click(nx, ny, f"Date {target_dt.day}", delay=0.8)


# ─────────────────────────────────────────────
# Set Time
# ─────────────────────────────────────────────
def set_time(hour_12, minute, ampm):
    triple_type(846, 638, f"{hour_12:02d}", "Hour")
    triple_type(950, 638, f"{minute:02d}",  "Minutes")
    current = read_ampm()
    if current != ampm:
        print(f"    → Switching {current} → {ampm}")
        click(1023, 638, f"Toggle to {ampm}", delay=0.8)
    else:
        print(f"    → Already {ampm} ✓")
    sys.stdout.flush()


# ─────────────────────────────────────────────
# Process One Collectible
# ─────────────────────────────────────────────
def process_one(global_index, row_y, target_dt):
    h24    = target_dt.hour
    minute = target_dt.minute
    ampm   = "AM" if h24 < 12 else "PM"
    h12    = h24 % 12 or 12

    print(f"\n{'═'*60}")
    print(f"  COLLECTIBLE #{global_index+1}  →  "
          f"{target_dt.strftime('%d/%m/%Y  %I:%M %p')}")
    print(f"{'═'*60}")
    sys.stdout.flush()

    click(ROW_CLICK_X, row_y + ROW_Y_OFFSET, f"Row #{global_index+1}", delay=2.5)
    click(1422, 351, "New Store",       delay=2.0)
    click(950,  399, "Clear Date",      delay=0.5)
    click(850,  361, "Date/time field", delay=0.5)

    click_specific_date(target_dt)
    set_time(h12, minute, ampm)

    click(1050, 899, "Save",         delay=1.0)
    click(32,   99,  "Browser back", delay=2.0)

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
    scroll_to_top()


# ═════════════════════════════════════════════
# Input Helpers
# ═════════════════════════════════════════════
def parse_datetime(raw):
    try:
        return datetime.strptime(raw.strip(), "%d/%m/%Y %I:%M %p")
    except ValueError:
        return None

def ask_datetime(label):
    print(f"\n  Enter {label}")
    print("  Format  : DD/MM/YYYY HH:MM AM/PM")
    print("  Example : 12/05/2026 12:17 AM")
    sys.stdout.flush()
    while True:
        raw = input("  >> ").strip()
        dt  = parse_datetime(raw)
        if dt:
            return dt
        print("  ❌ Invalid format")
        sys.stdout.flush()

def ask_int(prompt, lo, hi):
    while True:
        try:
            v = int(input(f"  {prompt} [{lo}-{hi}]: ").strip())
            if lo <= v <= hi:
                return v
            print(f"  ❌ Enter between {lo}-{hi}")
        except ValueError:
            print("  ❌ Invalid number")
        sys.stdout.flush()

def ask_increment():
    print("\n  Time increment between collectibles/groups (in minutes)")
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
def build_schedule(total, mode, order_mode, start_dt, increment_min, group_size=1):
    """
    Returns a list of datetimes, one per non-skipped collectible slot.

    We pre-generate 2× total slots so the pool never exhausts even
    if many rows are skipped at runtime.
    """
    pool_size  = total * 2
    num_groups = math.ceil(pool_size / group_size)

    if mode == "group":
        if order_mode == "reverse":
            group_times = [
                start_dt + timedelta(minutes=increment_min * (num_groups - 1 - g))
                for g in range(num_groups)
            ]
        else:
            group_times = [
                start_dt + timedelta(minutes=increment_min * g)
                for g in range(num_groups)
            ]
    else:
        if order_mode == "reverse":
            group_times = [
                start_dt + timedelta(minutes=increment_min * (pool_size - 1 - i))
                for i in range(pool_size)
            ]
        else:
            group_times = [
                start_dt + timedelta(minutes=increment_min * i)
                for i in range(pool_size)
            ]

    if mode != "group" or order_mode != "random":
        schedules = []
        for i in range(pool_size):
            g = i // group_size if mode == "group" else i
            schedules.append(group_times[g])
        return schedules

    # RANDOM (Latin-square shuffle within groups)
    base = list(range(num_groups))
    random.shuffle(base)
    latin = []
    for g in range(num_groups):
        row = base[g:] + base[:g]
        latin.append(row)

    schedules = []
    for g in range(num_groups):
        start_item     = g * group_size
        end_item       = min(start_item + group_size, pool_size)
        items_in_group = end_item - start_item
        for pos in range(items_in_group):
            slot_index = latin[g][pos % num_groups]
            schedules.append(group_times[slot_index])

    return schedules


# ═════════════════════════════════════════════
# MAIN
# ═════════════════════════════════════════════
print("\n" + "★"*60)
print("  DRIP Store Scheduler v3  (Scan-Y Bug Fixed)")
print("★"*60)
print()
print("  Skip rules (checked BEFORE opening each row):")
print(f"    • PINK  icon + supply == {PINK_SKIP_SUPPLY}  → SKIP")
print(f"    • WHITE icon + supply == {WHITE_SKIP_SUPPLY}  → SKIP")
print("    • Skipped rows do NOT consume a schedule slot")
print("    • Scan now uses row_y + ROW_Y_OFFSET (same Y as click)")
print()
sys.stdout.flush()

# ── Total collectibles ────────────────────────
total = ask_int("How many total collectibles to schedule (including skippable)", 1, 800)

# ── Scheduling mode ───────────────────────────
print("""
  Scheduling mode:
    1. GROUP      — multiple collectibles share the same time
    2. INDIVIDUAL — every collectible gets a unique time
""")
while True:
    mode_input = input("  Enter 1 or 2: ").strip()
    if mode_input in ("1", "2"):
        break
    print("  ❌ Enter 1 or 2")

group_size = 1
if mode_input == "1":
    group_size = ask_int(
        "How many collectibles per group (skipped rows do NOT fill a slot)",
        1, total
    )

# ── Order mode ────────────────────────────────
print("""
  Order mode:
    1. START   — times assigned sequentially (G1→T1, G2→T2, …)
    2. RANDOM  — shuffled Latin-square within each group
    3. REVERSE — times in reverse order
""")
while True:
    order_input = input("  Enter 1, 2 or 3: ").strip()
    if order_input in ("1", "2", "3"):
        break
    print("  ❌ Enter 1, 2 or 3")

order_mode_map = {"1": "start", "2": "random", "3": "reverse"}
order_mode     = order_mode_map[order_input]

# ── Start datetime ────────────────────────────
start_dt      = ask_datetime("start date & time")
increment_min = ask_increment()

# ── Starting row ──────────────────────────────
start_row = ask_int("Which row to start on", 1, ROWS_PER_PAGE) - 1

mode = "group" if mode_input == "1" else "individual"

# ── Build schedule pool ───────────────────────
schedule_pool = build_schedule(
    total, mode, order_mode, start_dt, increment_min, group_size
)
pool_idx = 0   # next datetime to consume from pool

# ── Summary ───────────────────────────────────
pages_needed = math.ceil(total / ROWS_PER_PAGE)

print("\n" + "─"*60)
print("  SCHEDULE SUMMARY")
print("─"*60)
print(f"  Total rows to visit : {total}")
print(f"  Mode                : {'GROUP (size='+str(group_size)+')' if mode=='group' else 'INDIVIDUAL'}")
print(f"  Order               : {order_mode.upper()}")
print(f"  Increment           : {increment_min} min")
print(f"  Pages needed        : {pages_needed}")
print(f"  Skip rules          : pink+supply={PINK_SKIP_SUPPLY}  |  white+supply={WHITE_SKIP_SUPPLY}")
print(f"  Scan Y              : row_y + {ROW_Y_OFFSET}  (aligned with click target)")
print("─"*60)
print("  First 20 schedule slots (consumed only by non-skipped rows):")
for i in range(min(20, len(schedule_pool))):
    g_label = f" G{i // group_size + 1}" if mode == "group" else ""
    print(f"    slot {i+1:03d}{g_label} → {schedule_pool[i].strftime('%d/%m/%Y  %I:%M %p')}")
if len(schedule_pool) > 20:
    print(f"  ... ({len(schedule_pool)-20} more pre-generated slots)")
print("─"*60)
sys.stdout.flush()

confirm = input("\n  Start automation? (y/n): ").strip().lower()
if confirm != "y":
    print("\n  Cancelled.")
    exit()

# ── Countdown ─────────────────────────────────
print("\n" + "★"*60)
print("  Starting in 5 seconds!")
print("  Open DRIP collectibles page NOW")
print("★"*60)
for i in range(5, 0, -1):
    print(f"  {i}...")
    sys.stdout.flush()
    time.sleep(1)
print("  GO!\n")

scroll_to_top()

# ═════════════════════════════════════════════
#  MAIN LOOP
#
#  Counters:
#    visited        — rows we have looked at (drives pagination)
#    group_slot     — position within the current group
#                     advances ONLY for non-skipped rows
#    assigned       — rows that received a datetime (non-skipped)
#    skipped_total  — rows that were skipped
# ═════════════════════════════════════════════
visited       = 0
group_slot    = 0
assigned      = 0
skipped_total = 0
current_page  = 0
first_page    = True

while visited < total:

    scroll_to_top()

    if first_page:
        row_start   = start_row
        avail_slots = ROWS_PER_PAGE - row_start
        items_page  = min(avail_slots, total - visited)
    else:
        row_start   = 0
        items_page  = min(ROWS_PER_PAGE, total - visited)

    print(f"\n{'▓'*60}")
    print(f"  PAGE {current_page+1}  —  "
          f"slots {row_start+1}–{row_start+items_page}  |  "
          f"visited={visited}  assigned={assigned}  skipped={skipped_total}")
    print(f"{'▓'*60}")
    sys.stdout.flush()

    for i in range(items_page):
        row_slot     = row_start + i
        row_y        = ROW_Y_POSITIONS[row_slot]
        global_index = visited + i

        print(f"\n  ── Row slot {row_slot+1}  |  visited #{global_index+1}  "
              f"|  group_slot={group_slot}  |  scan_y={row_y + ROW_Y_OFFSET}")
        sys.stdout.flush()

        # ── SKIP DETECTION ──────────────────────────────────────
        # Both detect_rarity_color() and read_supply_value() now
        # scan at row_y + ROW_Y_OFFSET (the fix).
        skip, reason = should_skip_row(row_y)

        if skip:
            skipped_total += 1
            print(f"  ⏭  SKIP row #{global_index+1}: {reason}")
            print(f"      group_slot stays at {group_slot}  "
                  f"(skipped={skipped_total})")
            sys.stdout.flush()
            continue   # group_slot NOT incremented; pool_idx NOT advanced

        # ── CONSUME NEXT SCHEDULE SLOT ──────────────────────────
        if pool_idx >= len(schedule_pool):
            # Extend pool if we've somehow exhausted it (many skips)
            last_dt    = schedule_pool[-1]
            extra_step = group_size if mode == "group" else 1
            schedule_pool.append(
                last_dt + timedelta(minutes=increment_min * extra_step)
            )

        target_dt = schedule_pool[pool_idx]
        pool_idx += 1

        # ── PROCESS ─────────────────────────────────────────────
        process_one(global_index, row_y, target_dt)
        assigned += 1

        # Advance group_slot (non-skipped rows only)
        group_slot += 1
        if mode == "group" and group_slot >= group_size:
            group_slot = 0
            print(f"\n  ◆ Group of {group_size} complete — slot reset")
            sys.stdout.flush()

    visited    += items_page
    first_page  = False

    if visited < total:
        go_next_page()
        current_page += 1

print(f"\n\n🎉  Done!")
print(f"    Rows visited : {visited}")
print(f"    Scheduled    : {assigned}")
print(f"    Skipped      : {skipped_total}")
print(f"    (pink supply={PINK_SKIP_SUPPLY} or white supply={WHITE_SKIP_SUPPLY})")
sys.stdout.flush()