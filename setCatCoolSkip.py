import pyautogui
import pyperclip
import time
import math
import os
from PIL import ImageGrab, Image

# ── OCR import (pytesseract) ──────────────────────────────────
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠  pytesseract not installed — OCR features limited")
    print("   Install: pip install pytesseract\n")

# ─────────────────────────────────────────────
# Reference dimensions — matched to 1456 x 816 screenshot
# ─────────────────────────────────────────────
REF_W = 1456
REF_H = 816

screen_w, screen_h = pyautogui.size()

# ─────────────────────────────────────────────
# ROW Y POSITIONS (collectibles list)
# ─────────────────────────────────────────────
ROW_Y_POSITIONS = [329, 369, 409, 449, 489, 530, 570, 610, 650, 690]
ROWS_PER_PAGE   = len(ROW_Y_POSITIONS)

# 3-dot (⋯) button — far right column
THREE_DOT_X = 1108

# Next page ">" button
NEXT_PAGE_X = 898
NEXT_PAGE_Y = 749

# ─────────────────────────────────────────────
# RARITY ICON SCAN — column X range in ref coords
# The rarity icon sits in the "Rarity" column
# From screenshot: icon is around x=930, centred on row_y
# We sample a small patch to detect color
# ─────────────────────────────────────────────
RARITY_ICON_X       = 930   # ref X centre of rarity icon
RARITY_ICON_HALF_W  = 6     # ±pixels around centre
RARITY_ICON_HALF_H  = 6

# ─────────────────────────────────────────────
# SUPPLY VALUE SCAN — column X range in ref coords
# "Supply" column is around x=995-1050
# We OCR a small strip to read the number
# ─────────────────────────────────────────────
SUPPLY_SCAN_X1      = 985
SUPPLY_SCAN_X2      = 1060
SUPPLY_SCAN_HALF_H  = 10    # ±pixels around row_y

# ─────────────────────────────────────────────
# SKIP RULES
#   PINK icon  (rare)   → skip if supply == 5
#   WHITE icon (common) → skip if supply == 1
# ─────────────────────────────────────────────
PINK_SKIP_SUPPLY   = 5
WHITE_SKIP_SUPPLY  = 1

# ─────────────────────────────────────────────
# DROPDOWN SCAN REGION
# ─────────────────────────────────────────────
DROPDOWN_SCAN_X1 = 970
DROPDOWN_SCAN_X2 = 1135
DROPDOWN_SCAN_Y1 = 310
DROPDOWN_SCAN_Y2 = 440

# Fallback fixed offset when OCR fails
EDIT_FALLBACK_X      = 1001
EDIT_FALLBACK_Y_OFF  = 71

# Categories to apply
CATEGORIES = [
    "Art",
    "Illustration",
    "Abstract",
    "AI Art",
    "Avatars & PFPs",
    "Portraits & People",
    "Fantasy & Mythology",
    "Anime & Manga",
    "Fashion & Style",
    "Mixed Media",
]

# ─────────────────────────────────────────────
# Core helpers
# ─────────────────────────────────────────────
def sc(x, y):
    """Scale reference coords to actual screen resolution."""
    return int(x * screen_w / REF_W), int(y * screen_h / REF_H)

def click(x, y, label="", delay=1.0):
    cx, cy = sc(x, y)
    print(f"    → [{label}] click at ref({x},{y}) → screen({cx},{cy})")
    pyautogui.moveTo(cx, cy, duration=0.4)
    pyautogui.click()
    time.sleep(delay)

def click_screen(sx, sy, label="", delay=1.0):
    print(f"    → [{label}] click at screen({sx},{sy})")
    pyautogui.moveTo(sx, sy, duration=0.4)
    pyautogui.click()
    time.sleep(delay)


# ═══════════════════════════════════════════════════════════════
#  RARITY + SUPPLY DETECTION
# ═══════════════════════════════════════════════════════════════

def detect_rarity_color(row_y):
    """
    Grab the rarity icon pixel patch for this row and determine
    whether it's PINK (rare) or WHITE (common) or OTHER.

    Returns: "pink", "white", or "other"

    Color logic (approximate RGB):
      Pink  → R high, G low-mid, B low-mid  (e.g. R>180, G<130, B<150)
      White → all channels high              (e.g. R>200, G>200, B>200)
    """
    sx1, sy1 = sc(RARITY_ICON_X - RARITY_ICON_HALF_W,
                  row_y         - RARITY_ICON_HALF_H)
    sx2, sy2 = sc(RARITY_ICON_X + RARITY_ICON_HALF_W,
                  row_y         + RARITY_ICON_HALF_H)

    ss      = ImageGrab.grab(bbox=(sx1, sy1, sx2, sy2))
    pixels  = ss.load()
    w, h    = ss.size

    pink_count  = 0
    white_count = 0
    total       = w * h

    for px in range(w):
        for py in range(h):
            pixel = pixels[px, py]
            r, g, b = pixel[0], pixel[1], pixel[2]

            # Pink / magenta hue: R dominant, G and B lower
            if r > 180 and g < 140 and b < 160 and r > g + 60:
                pink_count += 1
            # White / light grey: all channels high
            elif r > 190 and g > 190 and b > 190:
                white_count += 1

    print(f"    [rarity scan] pink_px={pink_count}  white_px={white_count}  total={total}")

    # Decision: need at least 3 clearly-coloured pixels to be sure
    if pink_count >= 3 and pink_count > white_count:
        return "pink"
    elif white_count >= 3 and white_count > pink_count:
        return "white"
    else:
        return "other"


def read_supply_value(row_y):
    """
    OCR the Supply column for this row.
    Returns the integer supply value, or None if OCR fails.
    """
    sx1, sy1 = sc(SUPPLY_SCAN_X1, row_y - SUPPLY_SCAN_HALF_H)
    sx2, sy2 = sc(SUPPLY_SCAN_X2, row_y + SUPPLY_SCAN_HALF_H)

    ss = ImageGrab.grab(bbox=(sx1, sy1, sx2, sy2))

    # Scale up 4× for better OCR on small numbers
    scale  = 4
    ss_big = ss.resize((ss.width * scale, ss.height * scale), Image.LANCZOS)

    if not OCR_AVAILABLE:
        print("    ⚠  OCR unavailable — cannot read supply, defaulting to None")
        return None

    try:
        text = pytesseract.image_to_string(
            ss_big,
            config="--psm 7 -c tessedit_char_whitelist=0123456789"
        ).strip()
        # strip non-digits
        digits = ''.join(c for c in text if c.isdigit())
        if digits:
            val = int(digits)
            print(f"    [supply OCR] raw='{text}'  parsed={val}")
            return val
        else:
            print(f"    [supply OCR] no digits found in '{text}'")
            return None
    except Exception as e:
        print(f"    ⚠  Supply OCR error: {e}")
        return None


def should_skip_row(row_y, global_index):
    """
    Detect rarity icon color and supply number for this row.
    Return (skip: bool, reason: str)

    Skip rules:
      • pink  icon + supply == 5  → skip
      • white icon + supply == 1  → skip
    """
    rarity = detect_rarity_color(row_y)
    supply = read_supply_value(row_y)

    if supply is None:
        print(f"    ⚠  Supply unreadable — NOT skipping (safe default)")
        return False, "supply_unreadable"

    if rarity == "pink" and supply == PINK_SKIP_SUPPLY:
        return True, f"pink icon, supply={supply} (skip threshold={PINK_SKIP_SUPPLY})"
    if rarity == "white" and supply == WHITE_SKIP_SUPPLY:
        return True, f"white icon, supply={supply} (skip threshold={WHITE_SKIP_SUPPLY})"

    return False, f"rarity={rarity}, supply={supply} — OK"


# ═══════════════════════════════════════════════════════════════
#  OCR — find and click "Edit" in the dropdown
# ═══════════════════════════════════════════════════════════════

def ocr_click_edit(row_y):
    sx1, sy1 = sc(DROPDOWN_SCAN_X1, DROPDOWN_SCAN_Y1)
    sx2, sy2 = sc(DROPDOWN_SCAN_X2, DROPDOWN_SCAN_Y2)

    ss     = ImageGrab.grab(bbox=(sx1, sy1, sx2, sy2))
    scale  = 3
    ss_big = ss.resize((ss.width * scale, ss.height * scale), Image.LANCZOS)

    if not OCR_AVAILABLE:
        _fallback_edit_click(row_y)
        return

    try:
        data = pytesseract.image_to_data(
            ss_big,
            output_type=pytesseract.Output.DICT,
            config="--psm 6"
        )
    except Exception as e:
        print(f"    ⚠  OCR error: {e} → using fallback")
        _fallback_edit_click(row_y)
        return

    found = False
    n = len(data["text"])
    for i in range(n):
        word = data["text"][i].strip()
        if word.lower() == "edit" and int(data["conf"][i]) > 30:
            bx, by = data["left"][i], data["top"][i]
            bw, bh = data["width"][i], data["height"][i]
            cx_scaled  = bx + bw // 2
            cy_scaled  = by + bh // 2
            cx_screen  = sx1 + cx_scaled // scale
            cy_screen  = sy1 + cy_scaled // scale
            print(f"    ✅ OCR found 'Edit' → screen({cx_screen},{cy_screen})  conf={data['conf'][i]}")
            click_screen(cx_screen, cy_screen, "Edit [OCR]", delay=2.0)
            found = True
            break

    if not found:
        print("    ⚠  OCR could not locate 'Edit' → using fallback")
        _fallback_edit_click(row_y)


def _fallback_edit_click(row_y):
    edit_ref_y = row_y + EDIT_FALLBACK_Y_OFF
    print(f"    → Fallback Edit click at ref({EDIT_FALLBACK_X}, {edit_ref_y})")
    click(EDIT_FALLBACK_X, edit_ref_y, "Edit [FALLBACK]", delay=2.0)


# ═══════════════════════════════════════════════════════════════
#  Tag × delete — pixel-scan
# ═══════════════════════════════════════════════════════════════
TAG_ROW_REF_Y   = 380
TAG_SCAN_X1     = 587
TAG_SCAN_X2     = 875
TAG_SCAN_HALF_H = 8

def find_and_click_category_delete():
    sx1, sy1 = sc(TAG_SCAN_X1, TAG_ROW_REF_Y - TAG_SCAN_HALF_H)
    sx2, sy2 = sc(TAG_SCAN_X2, TAG_ROW_REF_Y + TAG_SCAN_HALF_H)

    ss     = ImageGrab.grab(bbox=(sx1, sy1, sx2, sy2))
    pixels = ss.load()
    w, h   = ss.size

    BRIGHTNESS_THRESHOLD = 90
    found_x_screen = None
    found_y_screen = sy1 + h // 2

    for px in range(w - 1, -1, -1):
        bright_rows = 0
        for py in range(h):
            r, g, b = pixels[px, py][:3]
            if r > BRIGHTNESS_THRESHOLD or g > BRIGHTNESS_THRESHOLD or b > BRIGHTNESS_THRESHOLD:
                bright_rows += 1
        if bright_rows >= 2:
            found_x_screen = sx1 + px
            break

    if found_x_screen is None:
        print("    ⚠  Pixel scan found nothing → using fallback x=660")
        found_x_screen, _ = sc(660, TAG_ROW_REF_Y)

    print(f"    → Clicking × at screen ({found_x_screen}, {found_y_screen})")
    pyautogui.moveTo(found_x_screen, found_y_screen, duration=0.35)
    pyautogui.click()
    time.sleep(0.6)


# ═══════════════════════════════════════════════════════════════
#  Category input + dropdown
# ═══════════════════════════════════════════════════════════════
INPUT_FIELD_LEFT_QUARTER_X = 650
INPUT_FIELD_Y              = 355
DROPDOWN_RESULT_Y          = 395

def enter_category(category_text):
    print(f"    → Pasting category: '{category_text}'")
    cx, cy = sc(INPUT_FIELD_LEFT_QUARTER_X, INPUT_FIELD_Y)
    pyautogui.moveTo(cx, cy, duration=0.3)
    pyautogui.click()
    time.sleep(0.4)

    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('delete')
    time.sleep(0.3)

    pyperclip.copy(category_text)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.3)

    click(INPUT_FIELD_LEFT_QUARTER_X + 30, DROPDOWN_RESULT_Y,
          f"Dropdown: {category_text}", delay=0.9)


# ═══════════════════════════════════════════════════════════════
#  Save / Back
# ═══════════════════════════════════════════════════════════════
SAVE_BUTTON_X = 665
SAVE_BUTTON_Y = 580
BACK_ARROW_X  = 25
BACK_ARROW_Y  = 71


# ═══════════════════════════════════════════════════════════════
#  Full flow for one collectible row
# ═══════════════════════════════════════════════════════════════
def process_one(global_index, row_y, category):
    print(f"\n{'═'*60}")
    print(f"  COLLECTIBLE #{global_index+1}  →  Category: '{category}'")
    print(f"{'═'*60}")

    click(THREE_DOT_X, row_y, f"3-dot row #{global_index+1}", delay=1.5)
    ocr_click_edit(row_y)
    find_and_click_category_delete()
    time.sleep(0.5)
    enter_category(category)
    time.sleep(0.5)
    click(SAVE_BUTTON_X, SAVE_BUTTON_Y, "Save", delay=2.0)
    click(BACK_ARROW_X, BACK_ARROW_Y, "Back ← (1st)", delay=1.5)
    click(BACK_ARROW_X, BACK_ARROW_Y, "Back ← (2nd)", delay=2.0)

    print(f"  ✅  #{global_index+1} done!")


# ═══════════════════════════════════════════════════════════════
#  Navigate to next page
# ═══════════════════════════════════════════════════════════════
def go_next_page():
    print(f"\n  ─── Navigating to next page ──►")
    click(NEXT_PAGE_X, NEXT_PAGE_Y, "Next page >", delay=2.5)


# ═══════════════════════════════════════════════════════════════
#  INPUT HELPERS
# ═══════════════════════════════════════════════════════════════
def ask_int(prompt, lo, hi):
    while True:
        try:
            v = int(input(f"  {prompt} [{lo}-{hi}]: ").strip())
            if lo <= v <= hi:
                return v
            print(f"  ❌  Enter a number between {lo} and {hi}")
        except ValueError:
            print("  ❌  Please enter a valid whole number")


def ask_category_mode():
    print("""
  Category assignment mode:
    1. SAME      → all collectibles get the same category (you choose which)
    2. CYCLE     → cycle through all 10 categories in groups (see group size below)
    3. EACH_ALL  → apply ALL 10 categories to every collectible
""")
    while True:
        m = input("  Enter 1 / 2 / 3: ").strip()
        if m in ("1", "2", "3"):
            return m
        print("  ❌  Enter 1, 2, or 3")


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

print("\n" + "★"*60)
print("  DRIP Collectibles — Category Automation v2 (Skip Logic)")
print("★"*60)
print()
print("  Skip rules:")
print(f"    • PINK  icon + supply == {PINK_SKIP_SUPPLY}  → SKIP row")
print(f"    • WHITE icon + supply == {WHITE_SKIP_SUPPLY}  → SKIP row")
print("    • Skipped rows count toward total but NOT toward group slot")
print()

if OCR_AVAILABLE:
    print("  ✅  pytesseract OCR available")
else:
    print("  ⚠   pytesseract not found — supply OCR unavailable (no skipping!)")
print()

total      = ask_int("How many total collectibles to process", 1, 800)
start_row  = ask_int("Start from which collectible on the page (1-10)", 1, 10)
mode       = ask_category_mode()

group_size = 10   # default: one full cycle = 10 categories
if mode == "2":
    group_size = ask_int("How many collectibles per group (group size)", 1, 50)

chosen_category = None
if mode == "1":
    print("\n  Available categories:")
    for i, c in enumerate(CATEGORIES, 1):
        print(f"    {i:2d}. {c}")
    idx = ask_int("Choose category number", 1, len(CATEGORIES))
    chosen_category = CATEGORIES[idx - 1]

pages_needed = math.ceil(total / ROWS_PER_PAGE)

# ─────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────
print("\n" + "─"*60)
print("  SCHEDULE SUMMARY")
print("─"*60)
print(f"  Total collectibles : {total}")
print(f"  Start from row     : {start_row}")
if mode == "1":
    print(f"  Mode               : SAME ({chosen_category})")
elif mode == "2":
    print(f"  Mode               : CYCLE  (group_size={group_size})")
else:
    print(f"  Mode               : ALL CATEGORIES EACH")
print(f"  Pages to process   : {pages_needed}")
print("─"*60)

confirm = input("\n  Start automation? (y/n): ").strip().lower()
if confirm != "y":
    print("\n  Cancelled.")
    exit()

# Countdown
print("\n" + "★"*60)
print("  Starting in 10 seconds!")
print("  Switch to browser → collectibles list PAGE 1 NOW!")
print("★"*60)
for i in range(10, 0, -1):
    print(f"  {i}...")
    time.sleep(1)
print("  GO!\n")


# ═══════════════════════════════════════════════════════════════
#  RUN — page by page
#
#  Key counters:
#    processed       = how many rows we have VISITED (for page math)
#    group_slot      = position WITHIN the current group (0..group_size-1)
#                      only incremented when a row is NOT skipped
#    total_assigned  = how many collectibles actually received a category
#    skipped_total   = how many rows were skipped
# ═══════════════════════════════════════════════════════════════

processed      = 0   # rows visited (for pagination)
group_slot     = 0   # position in current group (counts only non-skipped)
total_assigned = 0
skipped_total  = 0
current_page   = 0
first_page     = True

while processed < total:

    # Calculate which row slots to process on this page
    if first_page:
        start_row_slot  = start_row - 1
        available_rows  = ROWS_PER_PAGE - start_row_slot
        rows_this_page  = min(available_rows, total - processed)
    else:
        start_row_slot  = 0
        rows_this_page  = min(ROWS_PER_PAGE, total - processed)

    print(f"\n{'▓'*60}")
    print(f"  PAGE {current_page + 1}  —  "
          f"row slots {start_row_slot + 1}–{start_row_slot + rows_this_page}")
    print(f"{'▓'*60}")

    for slot_offset in range(rows_this_page):
        row_slot     = start_row_slot + slot_offset
        row_y        = ROW_Y_POSITIONS[row_slot]
        global_index = processed + slot_offset   # 0-based index in total list

        print(f"\n  ── Row slot {row_slot+1}  |  Global #{global_index+1}  "
              f"|  group_slot={group_slot}")

        # ── SKIP DETECTION ───────────────────────────────────
        skip, reason = should_skip_row(row_y, global_index)

        if skip:
            skipped_total += 1
            print(f"  ⏭  SKIPPING row #{global_index+1}: {reason}")
            print(f"      (skipped_total={skipped_total}, "
                  f"group_slot stays at {group_slot})")
            continue   # DO NOT increment group_slot; DO count in processed

        # ── CATEGORY ASSIGNMENT ──────────────────────────────
        if mode == "1":
            cats = [chosen_category]

        elif mode == "2":
            # group_slot advances only for non-skipped rows
            cat_index = group_slot % len(CATEGORIES)
            cats      = [CATEGORIES[cat_index]]

        else:  # EACH_ALL
            cats = CATEGORIES[:]

        # ── PROCESS ─────────────────────────────────────────
        if len(cats) == 1:
            process_one(global_index, row_y, cats[0])
        else:
            for cat_pass, cat in enumerate(cats):
                print(f"\n  ── Category pass {cat_pass+1}/{len(cats)}: '{cat}'")
                process_one(global_index, row_y, cat)

        total_assigned += 1

        # Advance group_slot (only for successfully processed rows)
        group_slot += 1
        if mode == "2" and group_slot >= group_size:
            group_slot = 0   # reset group at each group boundary
            print(f"\n  ◆ Group of {group_size} complete — resetting group slot")

    processed  += rows_this_page
    first_page  = False

    if processed < total:
        go_next_page()
        current_page += 1

print(f"\n\n🎉  Done!")
print(f"    Visited     : {processed} rows")
print(f"    Assigned    : {total_assigned} collectibles")
print(f"    Skipped     : {skipped_total} rows")
print(f"    (pink supply={PINK_SKIP_SUPPLY} or white supply={WHITE_SKIP_SUPPLY})")