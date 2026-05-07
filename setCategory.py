import pyautogui
import pyperclip
import time
import math
import os
from PIL import ImageGrab, Image

# ── OCR import (pytesseract) ──────────────────────────────────
try:
    import pytesseract
    # If tesseract is not on PATH, set it here:
    # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠  pytesseract not installed — falling back to fixed-offset Edit click")
    print("   Install with:  pip install pytesseract")
    print("   Also install Tesseract OCR:  https://github.com/UB-Mannheim/tesseract/wiki\n")

# ─────────────────────────────────────────────
# Reference dimensions — matched to your 1456 x 816 screenshot
# ─────────────────────────────────────────────
REF_W = 1456
REF_H = 816

screen_w, screen_h = pyautogui.size()

# ─────────────────────────────────────────────
# ROW Y POSITIONS — measured from screenshot (collectibles list)
# IntimoArt #327(299), #326(339), #325(379), #324(419),
# #323(459), #322(500), #321(540), #320(580), #319(620), #318(660)
# ─────────────────────────────────────────────
ROW_Y_POSITIONS = [299, 339, 379, 419, 459, 500, 540, 580, 620, 660]
ROWS_PER_PAGE   = len(ROW_Y_POSITIONS)

# 3-dot (⋯) button — far right column
THREE_DOT_X = 1108

# Next page ">" button
NEXT_PAGE_X = 899
NEXT_PAGE_Y = 721

# ─────────────────────────────────────────────
# DROPDOWN SCAN REGION — where the popup menu appears
# From screenshot: dropdown box spans roughly:
#   x: 975 → 1130,  y: 315 → 435
# We scan a slightly wider area to be safe.
# ─────────────────────────────────────────────
DROPDOWN_SCAN_X1 = 970     # ref left edge of dropdown
DROPDOWN_SCAN_X2 = 1135    # ref right edge of dropdown
DROPDOWN_SCAN_Y1 = 310     # ref top of dropdown
DROPDOWN_SCAN_Y2 = 440     # ref bottom of dropdown

# Fallback fixed offset when OCR fails
# "Edit" is the 3rd item — ~70px below the row_y in ref coords
EDIT_FALLBACK_X      = 1001
EDIT_FALLBACK_Y_OFF  = 71   # offset from row_y

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
    """Click directly at screen pixel coords (no scaling)."""
    print(f"    → [{label}] click at screen({sx},{sy})")
    pyautogui.moveTo(sx, sy, duration=0.4)
    pyautogui.click()
    time.sleep(delay)

# ─────────────────────────────────────────────
# OCR — find and click "Edit" in the dropdown
# ─────────────────────────────────────────────
def ocr_click_edit(row_y):
    """
    After the 3-dot dropdown is open:
      1. Grab a screenshot of the dropdown region.
      2. Use pytesseract to extract word-level bounding boxes.
      3. Find the word "Edit" (case-insensitive).
      4. Click the centre of that bounding box.
      5. Fall back to a fixed-offset click if OCR fails.

    row_y  : ref-coord Y of the row whose dropdown is open
              (used only for the fallback click).
    """
    # Convert ref dropdown region → screen pixels
    sx1, sy1 = sc(DROPDOWN_SCAN_X1, DROPDOWN_SCAN_Y1)
    sx2, sy2 = sc(DROPDOWN_SCAN_X2, DROPDOWN_SCAN_Y2)

    # Grab the dropdown screenshot strip
    ss = ImageGrab.grab(bbox=(sx1, sy1, sx2, sy2))

    # ── Scale up 3× for better OCR accuracy on small text ──
    scale = 3
    ss_big = ss.resize((ss.width * scale, ss.height * scale), Image.LANCZOS)

    # Optional: save for debug
    # ss_big.save("dropdown_debug.png")

    if not OCR_AVAILABLE:
        _fallback_edit_click(row_y)
        return

    # Run pytesseract with word-level data
    try:
        data = pytesseract.image_to_data(
            ss_big,
            output_type=pytesseract.Output.DICT,
            config="--psm 6"   # assume a uniform block of text
        )
    except Exception as e:
        print(f"    ⚠  OCR error: {e} → using fallback")
        _fallback_edit_click(row_y)
        return

    # Search for "Edit" in the OCR results
    found = False
    n = len(data["text"])
    for i in range(n):
        word = data["text"][i].strip()
        if word.lower() == "edit" and int(data["conf"][i]) > 30:
            # Bounding box in the scaled image
            bx = data["left"][i]
            by = data["top"][i]
            bw = data["width"][i]
            bh = data["height"][i]

            # Centre of the word in scaled image coords
            cx_scaled = bx + bw // 2
            cy_scaled = by + bh // 2

            # Map back to screen coords
            cx_screen = sx1 + cx_scaled // scale
            cy_screen = sy1 + cy_scaled // scale

            print(f"    ✅ OCR found 'Edit' at scaled({cx_scaled},{cy_scaled})"
                  f" → screen({cx_screen},{cy_screen})  conf={data['conf'][i]}")
            click_screen(cx_screen, cy_screen, "Edit [OCR]", delay=2.0)
            found = True
            break

    if not found:
        print("    ⚠  OCR could not locate 'Edit' → using fallback")
        _fallback_edit_click(row_y)


def _fallback_edit_click(row_y):
    """Fixed-offset fallback when OCR fails."""
    edit_ref_y = row_y + EDIT_FALLBACK_Y_OFF
    print(f"    → Fallback Edit click at ref({EDIT_FALLBACK_X}, {edit_ref_y})")
    click(EDIT_FALLBACK_X, edit_ref_y, "Edit [FALLBACK]", delay=2.0)


# ─────────────────────────────────────────────
# Tag × delete — pixel-scan (unchanged logic)
# ─────────────────────────────────────────────
TAG_ROW_REF_Y   = 380
TAG_SCAN_X1     = 587
TAG_SCAN_X2     = 875
TAG_SCAN_HALF_H = 8

def find_and_click_category_delete():
    sx1, sy1 = sc(TAG_SCAN_X1, TAG_ROW_REF_Y - TAG_SCAN_HALF_H)
    sx2, sy2 = sc(TAG_SCAN_X2, TAG_ROW_REF_Y + TAG_SCAN_HALF_H)

    ss = ImageGrab.grab(bbox=(sx1, sy1, sx2, sy2))
    pixels = ss.load()
    w, h = ss.size

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


# ─────────────────────────────────────────────
# Category input + dropdown
# ─────────────────────────────────────────────
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


# ─────────────────────────────────────────────
# Save / Back
# ─────────────────────────────────────────────
SAVE_BUTTON_X = 665
SAVE_BUTTON_Y = 580
BACK_ARROW_X  = 25
BACK_ARROW_Y  = 71


# ─────────────────────────────────────────────
# Full flow for one collectible row
# ─────────────────────────────────────────────
def process_one(global_index, row_y, category):
    print(f"\n{'═'*60}")
    print(f"  COLLECTIBLE #{global_index+1}  →  Category: '{category}'")
    print(f"{'═'*60}")

    # 1. Click the 3-dot menu
    click(THREE_DOT_X, row_y, f"3-dot row #{global_index+1}", delay=1.5)

    # 2. OCR-detect and click "Edit" in the dropdown
    ocr_click_edit(row_y)

    # 3. Modal open — find and click × on existing category tag
    find_and_click_category_delete()
    time.sleep(0.5)

    # 4. Type new category and select from dropdown
    enter_category(category)
    time.sleep(0.5)

    # 5. Click Save
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
print("  DRIP Collectibles — Category Automation (OCR Edition)")
print("★"*60)

if OCR_AVAILABLE:
    print("  ✅  pytesseract OCR is available — Edit will be located automatically")
else:
    print("  ⚠   pytesseract not found — using fixed-offset fallback for Edit")
print()

total = ask_int("How many total collectibles to process", 1, 550)
mode  = ask_category_mode()

chosen_category = None
if mode == "1":
    print("\n  Available categories:")
    for i, c in enumerate(CATEGORIES, 1):
        print(f"    {i:2d}. {c}")
    idx = ask_int("Choose category number", 1, len(CATEGORIES))
    chosen_category = CATEGORIES[idx - 1]

# Build assignment list
assignments = []
for i in range(total):
    if mode == "1":
        assignments.append([chosen_category])
    elif mode == "2":
        assignments.append([CATEGORIES[i % len(CATEGORIES)]])
    else:
        assignments.append(CATEGORIES[:])

pages_needed = math.ceil(total / ROWS_PER_PAGE)

# Summary
print("\n" + "─"*60)
print("  SCHEDULE SUMMARY")
print("─"*60)
print(f"  Total collectibles : {total}")
print(f"  Mode               : {'SAME ('+chosen_category+')' if mode=='1' else 'CYCLE' if mode=='2' else 'ALL CATEGORIES EACH'}")
print(f"  Pages to process   : {pages_needed}")
print("─"*60)

preview_count = min(total, 20)
for i in range(preview_count):
    print(f"  #{i+1:03d}  →  {', '.join(assignments[i])}")
if total > 20:
    print(f"  ... ({total - 20} more not shown)")
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

# Run — page by page
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
            for cat_pass, cat in enumerate(cats):
                print(f"\n  ── Category pass {cat_pass+1}/{len(cats)}: '{cat}'")
                process_one(global_index, row_y, cat)

    processed += rows_this_page

    if processed < total:
        go_next_page()
        current_page += 1

print(f"\n\n🎉  All {total} collectibles processed successfully!")