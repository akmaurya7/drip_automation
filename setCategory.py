import pyautogui
import pyperclip
import time
import math
import os
from PIL import ImageGrab, Image

# ─────────────────────────────────────────────
# Reference dimensions — matched to your 1456 x 816 screenshot
# ─────────────────────────────────────────────
REF_W = 1456
REF_H = 816

screen_w, screen_h = pyautogui.size()

# ─────────────────────────────────────────────
# ROW Y POSITIONS — measured from Image 1 (collectibles list)
# Rows visible: The Pose(299), Rope Dance(339), The Ghaghra(379),
# Break Dance(419), Ballerina In(459), Indian kathak(500),
# An Indian Classical Dance(540), An Ice Skater(580),
# Waccking Dance(620), Ukrainian Hopak(660)
# ─────────────────────────────────────────────
ROW_Y_POSITIONS = [299, 339, 379, 419, 459, 500, 540, 580, 620, 660]
ROWS_PER_PAGE   = len(ROW_Y_POSITIONS)

# 3-dot (⋯) button — far right column, measured from Image 1
THREE_DOT_X = 1108

# Next page ">" button — measured from pagination row in Image 1
NEXT_PAGE_X = 899
NEXT_PAGE_Y = 721

# Categories to apply (in order — script cycles through all)
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

def move_to(x, y, label=""):
    cx, cy = sc(x, y)
    print(f"    → [MOVE {label}] ref({x},{y}) → screen({cx},{cy})")
    pyautogui.moveTo(cx, cy, duration=0.4)

# ─────────────────────────────────────────────
# Tag × delete button — measured from Image 2 (edit modal)
#
# The "ILLUSTRATION ×" tag sits at ref y≈380.
# The tag pill spans roughly x=587→670.
# The × (delete) icon is on the RIGHT side of the pill, at ~x=660.
# ─────────────────────────────────────────────
TAG_ROW_REF_Y   = 380          # vertical centre of the tag row (Image 2)
TAG_SCAN_X1     = 587          # left edge of tag scan area (ref)
TAG_SCAN_X2     = 875          # right edge of scan area (ref)
TAG_SCAN_HALF_H = 8            # ±8 ref px vertical window


def find_and_click_category_delete():
    """
    Pixel-scans the tag row right-to-left for the × icon (a bright pixel
    cluster on the dark modal background), then clicks it.
    Falls back to a fixed coord if scan fails.
    """
    sx1, sy1 = sc(TAG_SCAN_X1, TAG_ROW_REF_Y - TAG_SCAN_HALF_H)
    sx2, sy2 = sc(TAG_SCAN_X2, TAG_ROW_REF_Y + TAG_SCAN_HALF_H)

    ss = ImageGrab.grab(bbox=(sx1, sy1, sx2, sy2))
    pixels = ss.load()
    w, h = ss.size

    BRIGHTNESS_THRESHOLD = 90   # above this = not dark modal background

    found_x_screen = None
    found_y_screen = sy1 + h // 2

    # Right-to-left: the × is the rightmost bright element on the tag row
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
        # Fallback: the × icon is roughly at ref x=660, y=380 for short tags
        print("    ⚠  Pixel scan found nothing → using fallback x=660")
        found_x_screen, _ = sc(660, TAG_ROW_REF_Y)

    print(f"    → Clicking × at screen ({found_x_screen}, {found_y_screen})")
    pyautogui.moveTo(found_x_screen, found_y_screen, duration=0.35)
    pyautogui.click()
    time.sleep(0.6)


def debug_save_tag_strip(filename="tag_strip_debug.png"):
    """Call manually to save the scanned strip for visual inspection."""
    sx1, sy1 = sc(TAG_SCAN_X1, TAG_ROW_REF_Y - TAG_SCAN_HALF_H)
    sx2, sy2 = sc(TAG_SCAN_X2, TAG_ROW_REF_Y + TAG_SCAN_HALF_H)
    ss = ImageGrab.grab(bbox=(sx1, sy1, sx2, sy2))
    ss_big = ss.resize((ss.width * 6, ss.height * 6), Image.NEAREST)
    ss_big.save(filename)
    print(f"    → Saved debug strip to {filename}")


# ─────────────────────────────────────────────
# Category input — measured from Image 2 (edit modal)
#
# The input field (above the ILLUSTRATION tag) spans roughly:
#   x: 587 → 875,  y: 345 → 365
# Left-quarter click target: x≈650, y≈355
# First dropdown result appears at y≈395 (just below input)
# ─────────────────────────────────────────────
INPUT_FIELD_LEFT_QUARTER_X = 650   # left ~1/4 of input box (ref)
INPUT_FIELD_Y              = 355   # vertical centre of input field (ref)
DROPDOWN_RESULT_Y          = 395   # first dropdown result Y (ref)


def enter_category(category_text):
    """
    Activate the category input, clear it, paste new text, select dropdown.
    """
    print(f"    → Clicking left-quarter of input to activate")
    cx, cy = sc(INPUT_FIELD_LEFT_QUARTER_X, INPUT_FIELD_Y)
    pyautogui.moveTo(cx, cy, duration=0.3)
    pyautogui.click()
    time.sleep(0.4)

    # Clear residual text
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('delete')
    time.sleep(0.3)

    # Paste via clipboard — handles spaces, &, all special chars reliably
    print(f"    → Pasting category: '{category_text}'")
    pyperclip.copy(category_text)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.3)   # wait for dropdown to render

    # Click the first dropdown suggestion
    click(INPUT_FIELD_LEFT_QUARTER_X + 30, DROPDOWN_RESULT_Y,
          f"Dropdown: {category_text}", delay=0.9)


# ─────────────────────────────────────────────
# "Edit" option in the 3-dot dropdown
#
# From Image 1: 3-dot is in the rightmost column.
# The dropdown opens downward; "Edit" is typically the first item,
# appearing ~70 px below the row Y in ref coords.
# X for the Edit option: ~989 (centre of dropdown menu)
# ─────────────────────────────────────────────
EDIT_OPTION_X      = 989
EDIT_OPTION_Y_OFF  = 71    # ref px offset from row_y → "Edit" item


# ─────────────────────────────────────────────
# Save button — measured from Image 2
# Save is at roughly ref x=665, y=580
# ─────────────────────────────────────────────
SAVE_BUTTON_X = 665
SAVE_BUTTON_Y = 580

# Back arrow (top-left of page) — same position as original
BACK_ARROW_X = 25
BACK_ARROW_Y = 71


# ─────────────────────────────────────────────
# Full flow for one collectible row
# ─────────────────────────────────────────────
def process_one(global_index, row_y, category):
    print(f"\n{'═'*60}")
    print(f"  COLLECTIBLE #{global_index+1}  →  Category: '{category}'")
    print(f"{'═'*60}")

    # 1. Click the 3-dot menu on the row
    click(THREE_DOT_X, row_y, f"3-dot row #{global_index+1}", delay=1.5)

    # 2. Click "Edit" — row_y + fixed offset
    edit_y = row_y + EDIT_OPTION_Y_OFF
    print(f"    → Dropdown Edit at ref y={edit_y} (row_y={row_y} + {EDIT_OPTION_Y_OFF})")
    click(EDIT_OPTION_X, edit_y, "Edit", delay=2.0)

    # 3. Modal open — find and click × on existing category tag
    find_and_click_category_delete()
    time.sleep(0.5)

    # 4. Click left-quarter of input, type new category, select dropdown
    enter_category(category)
    time.sleep(0.5)

    # 5. Click Save (ref x=665, y=580 from Image 2)
    click(SAVE_BUTTON_X, SAVE_BUTTON_Y, "Save", delay=2.0)

    # 6. Click back arrow TWICE to return to collectibles list
    click(BACK_ARROW_X, BACK_ARROW_Y, "Back ← (1st)", delay=1.5)
    click(BACK_ARROW_X, BACK_ARROW_Y, "Back ← (2nd)", delay=2.0)

    print(f"  ✅  #{global_index+1} done!")


# ─────────────────────────────────────────────
# Navigate to next page
# ─────────────────────────────────────────────
def go_next_page():
    print(f"\n  ─── Navigating to next page ──►")
    click(NEXT_PAGE_X, NEXT_PAGE_Y, "Next page >", delay=2.5)


# ════════════════════════════════════════════════════════
#  INPUT HELPERS
# ════════════════════════════════════════════════════════

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
    2. CYCLE     → cycle through all 10 categories repeatedly
    3. EACH_ALL  → apply ALL 10 categories to every collectible
""")
    while True:
        m = input("  Enter 1 / 2 / 3: ").strip()
        if m in ("1", "2", "3"):
            return m
        print("  ❌  Enter 1, 2, or 3")


# ════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════

print("\n" + "★"*60)
print("  DRIP Collectibles — Category Automation")
print("★"*60)

# ── Q1: Total collectibles ──────────────────────────────
print()
total = ask_int("How many total collectibles to process", 1, 550)

# ── Q2: Category mode ──────────────────────────────────
mode = ask_category_mode()

chosen_category = None
if mode == "1":
    print("\n  Available categories:")
    for i, c in enumerate(CATEGORIES, 1):
        print(f"    {i:2d}. {c}")
    idx = ask_int("Choose category number", 1, len(CATEGORIES))
    chosen_category = CATEGORIES[idx - 1]

# ── Build assignment list ──────────────────────────────
assignments = []
for i in range(total):
    if mode == "1":
        assignments.append([chosen_category])
    elif mode == "2":
        assignments.append([CATEGORIES[i % len(CATEGORIES)]])
    else:  # mode == "3" — all categories per collectible
        assignments.append(CATEGORIES[:])

pages_needed = math.ceil(total / ROWS_PER_PAGE)

# ── Summary ────────────────────────────────────────────
print("\n" + "─"*60)
print("  SCHEDULE SUMMARY")
print("─"*60)
print(f"  Total collectibles : {total}")
print(f"  Mode               : {'SAME ('+chosen_category+')' if mode=='1' else 'CYCLE' if mode=='2' else 'ALL CATEGORIES EACH'}")
print(f"  Pages to process   : {pages_needed}")
print("─"*60)

preview_count = min(total, 20)
for i in range(preview_count):
    cats = assignments[i]
    print(f"  #{i+1:03d}  →  {', '.join(cats)}")
if total > 20:
    print(f"  ... ({total - 20} more not shown)")
print("─"*60)

confirm = input("\n  Start automation? (y/n): ").strip().lower()
if confirm != "y":
    print("\n  Cancelled.")
    exit()

# ── Countdown ──────────────────────────────────────────
print("\n" + "★"*60)
print("  Starting in 10 seconds!")
print("  Switch to browser → collectibles list PAGE 1 NOW!")
print("★"*60)
for i in range(10, 0, -1):
    print(f"  {i}...")
    time.sleep(1)
print("  GO!\n")

# ── Run — page by page ─────────────────────────────────
processed    = 0
current_page = 0

while processed < total:
    rows_this_page = min(ROWS_PER_PAGE, total - processed)

    print(f"\n{'▓'*60}")
    print(f"  PAGE {current_page + 1}  —  processing rows 1-{rows_this_page}")
    print(f"{'▓'*60}")

    for row_slot in range(rows_this_page):
        global_index = processed + row_slot
        row_y        = ROW_Y_POSITIONS[row_slot]
        cats         = assignments[global_index]

        if len(cats) == 1:
            process_one(global_index, row_y, cats[0])
        else:
            # Multiple categories — multiple edit passes for same row
            for cat_pass, cat in enumerate(cats):
                print(f"\n  ── Category pass {cat_pass+1}/{len(cats)}: '{cat}'")
                process_one(global_index, row_y, cat)

    processed += rows_this_page

    if processed < total:
        go_next_page()
        current_page += 1

print(f"\n\n🎉  All {total} collectibles processed successfully!")