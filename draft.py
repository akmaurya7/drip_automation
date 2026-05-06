"""
DRIP Collectibles — Upload Automation (Fixed)
==============================================
Fixes:
 1. Category field clicks at exact correct position
 2. File dialog — types full image path into filename box
    → selects images in order: 1st, 2nd, 3rd ...
 3. Terminal asks: count, rarity, image folder path
 4. Titles entered via popup
"""

import pyautogui
import time
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox

# ─────────────────────────────────────────────
# Reference dimensions (1456 x 816)
# ─────────────────────────────────────────────
REF_W = 1456
REF_H = 816

screen_w, screen_h = pyautogui.size()
print(f"Screen: {screen_w} x {screen_h}")

def sc(x, y):
    return int(x * screen_w / REF_W), int(y * screen_h / REF_H)

def click(x, y, label="", delay=0.8):
    cx, cy = sc(x, y)
    print(f"  → [{label}] ({cx},{cy})")
    pyautogui.moveTo(cx, cy, duration=0.35)
    pyautogui.click()
    time.sleep(delay)

def type_text(text):
    """Paste text via clipboard — handles special chars & spaces."""
    import pyperclip
    pyperclip.copy(str(text))
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.3)

def clear_field_and_type(x, y, text, label=""):
    """Click field, select all, paste text."""
    cx, cy = sc(x, y)
    pyautogui.moveTo(cx, cy, duration=0.3)
    pyautogui.click()
    time.sleep(0.4)
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)
    pyautogui.press("delete")
    time.sleep(0.1)
    type_text(text)
    print(f"  → [{label}]: {text[:50]}")

# ─────────────────────────────────────────────
# Panel field coordinates (ref 1456x816)
# Measured from Image 1 precisely
# ─────────────────────────────────────────────
# Panel is on right side X: 1143 → 1430
# Name field input:         Y ≈ 172
# Description textarea:     Y ≈ 231
# Categories input box:     Y ≈ 310  (the actual input, below label)
# Category dropdown item:   Y ≈ 335  (first suggestion appears here)
# Rarity row 1:             Y ≈ 372
# Rarity row 2 (Eternal):   Y ≈ 397
# Image media button:       Y ≈ 481
# Browse (image upload):    Y ≈ 573
# Save as Draft:            Y ≈ 732
# Create button (list):     Y ≈ 165, X ≈ 1089

PANEL_X = 1283   # center X of the right panel input fields

FIELD = {
    "name":         (PANEL_X, 172),
    "description":  (PANEL_X, 231),
    "category_box": (PANEL_X, 310),   # ← FIXED: exact input box
    "cat_dropdown": (PANEL_X, 335),   # first dropdown suggestion
    "rarity_row1":  1372,             # Y for No Rarity / Rare / Legendary / Ultimate
    "rarity_row2":  1397,             # Y for Eternal (second row)  — wait these are ref Y
}

# Rarity button X positions (ref) on the panel
RARITY_MAP = {
    "No Rarity": (1169, 372),
    "Rare":      (1222, 372),
    "Legendary": (1281, 372),
    "Ultimate":  (1349, 372),
    "Eternal":   (1173, 397),
}

# ─────────────────────────────────────────────
# Categories
# ─────────────────────────────────────────────
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
# File dialog — type path into filename field
# This is the most reliable method.
# After Browse is clicked:
#  1. Dialog opens (Downloads folder shown)
#  2. We click the File name input at bottom
#  3. Type/paste the full image path
#  4. Press Enter (= Open)
# ─────────────────────────────────────────────
def select_image_via_dialog(image_path):
    """
    After Browse opens the Windows file dialog,
    type the full image path into the filename field and press Enter.
    """
    time.sleep(2.0)   # wait for dialog to fully open

    # The File name field is at the bottom of the dialog.
    # From Image 2: dialog is ~730x550, positioned near center-left of screen.
    # File name field absolute position ≈ (340, 469) relative to dialog top-left.
    # Dialog top-left from Image 2 ≈ (10, 10) on screen.
    # So absolute: X≈220, Y≈479
    # But this varies — SAFER: click the filename field using Tab key
    # from the dialog, or use the address bar approach.
    #
    # MOST RELIABLE: Just type the path — Windows dialog intercepts
    # any typing as a path filter when the grid has focus.

    print(f"  → Typing path into dialog: {image_path}")

    # Click the File name input box directly
    # From Image 2, the filename field is at abs approx:
    # Dialog left edge ≈ 10px, field Y ≈ 469px from top of screen
    # Field center X ≈ 10 + 340 = 350, Y ≈ 469
    fn_x = 340
    fn_y = 469
    pyautogui.moveTo(fn_x, fn_y, duration=0.3)
    pyautogui.click()
    time.sleep(0.3)

    # Select all existing text in field and replace
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)

    import pyperclip
    pyperclip.copy(image_path)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.5)

    # Click Open button
    # From Image 2: Open button at abs ≈ (536, 503)
    open_x = 536
    open_y = 503
    pyautogui.moveTo(open_x, open_y, duration=0.3)
    pyautogui.click()
    time.sleep(2.0)
    print(f"  → Opened: {os.path.basename(image_path)}")

# ─────────────────────────────────────────────
# Type category and click dropdown
# ─────────────────────────────────────────────
def enter_category(category):
    """
    Click the Categories input box precisely,
    type the category, wait for dropdown, click first result.
    """
    # Click the input field
    cx, cy = sc(PANEL_X, 310)
    print(f"  → Clicking category field at ({cx},{cy})")
    pyautogui.moveTo(cx, cy, duration=0.3)
    pyautogui.click()
    time.sleep(0.5)

    # Clear any existing text
    pyautogui.hotkey("ctrl", "a")
    time.sleep(0.2)

    # Type the category
    import pyperclip
    pyperclip.copy(category)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(1.5)   # wait for dropdown to appear

    # Click the first dropdown suggestion (appears ~25px below input)
    dx, dy = sc(PANEL_X, 335)
    print(f"  → Clicking dropdown suggestion at ({dx},{dy})")
    pyautogui.moveTo(dx, dy, duration=0.3)
    pyautogui.click()
    time.sleep(0.5)

    # Press comma to confirm as tag
    pyautogui.press("comma")
    time.sleep(0.3)

    # Escape to close any leftover dropdown
    pyautogui.press("escape")
    time.sleep(0.3)
    print(f"  → Category set: {category}")

# ─────────────────────────────────────────────
# Process one collectible
# ─────────────────────────────────────────────
def process_one(index, title, image_path, category, rarity):
    print(f"\n{'═'*60}")
    print(f"  #{index+1:03d}  {title}")
    print(f"         Image    : {os.path.basename(image_path)}")
    print(f"         Category : {category}  |  Rarity: {rarity}")
    print(f"{'═'*60}")

    # 1. Click Create button (top right of collectibles list)
    click(1089, 165, "Create", delay=2.5)

    # 2. Name field — click and type
    clear_field_and_type(PANEL_X, 172, title, "Name")

    # 3. Description — same as title
    clear_field_and_type(PANEL_X, 231, title, "Description")

    # 4. Category input (FIXED coords)
    enter_category(category)

    # 5. Rarity button
    rx, ry = RARITY_MAP[rarity]
    click(rx, ry, f"Rarity: {rarity}", delay=0.6)

    # 6. Image media type button
    click(1185, 481, "Media type: Image", delay=1.0)

    # 7. Scroll panel to reveal Browse button
    cx, cy = sc(PANEL_X, 540)
    pyautogui.moveTo(cx, cy, duration=0.3)
    pyautogui.scroll(-3)
    time.sleep(0.6)

    # 8. Click Browse button
    click(1389, 573, "Browse", delay=1.8)

    # 9. Type image path into dialog → Open
    select_image_via_dialog(image_path)

    # 10. Scroll panel down to Save as Draft
    cx, cy = sc(PANEL_X, 600)
    pyautogui.moveTo(cx, cy, duration=0.3)
    pyautogui.scroll(-4)
    time.sleep(0.6)

    # 11. Save as Draft
    click(1304, 732, "Save as Draft", delay=3.5)

    print(f"  ✅ #{index+1} done!")


# ════════════════════════════════════════════════════════
#  TITLE INPUT POPUP
# ════════════════════════════════════════════════════════

def get_titles_popup(count):
    """Small popup — paste titles one per line."""
    result = {"titles": None}

    win = tk.Tk()
    win.title(f"Paste {count} Titles — One Per Line")
    win.geometry("520x400")
    win.configure(bg="#1a1a2e")
    win.lift()
    win.attributes("-topmost", True)

    tk.Label(
        win,
        text=f"Paste {count} titles below  (one title per line):",
        bg="#1a1a2e", fg="#e0e0e0",
        font=("Segoe UI", 11, "bold")
    ).pack(pady=(14, 6), padx=16, anchor="w")

    box = scrolledtext.ScrolledText(
        win, height=13, width=60,
        bg="#16213e", fg="#e0e0e0",
        insertbackground="white",
        font=("Consolas", 10),
        relief="flat", bd=2
    )
    box.pack(padx=16, pady=6)

    status = tk.Label(win, text="", bg="#1a1a2e", fg="#ff8a80",
                      font=("Segoe UI", 9))
    status.pack()

    def confirm():
        raw    = box.get("1.0", "end").strip()
        titles = [t.strip() for t in raw.splitlines() if t.strip()]
        if len(titles) != count:
            status.config(
                text=f"❌  Need {count} titles. You entered {len(titles)}."
            )
            return
        result["titles"] = titles
        win.destroy()

    tk.Button(
        win, text="✅  Confirm",
        command=confirm,
        bg="#4caf50", fg="white",
        font=("Segoe UI", 11, "bold"),
        relief="flat", padx=20, pady=8
    ).pack(pady=10)

    win.mainloop()
    return result["titles"]


# ════════════════════════════════════════════════════════
#  TERMINAL INPUT HELPERS
# ════════════════════════════════════════════════════════

def ask_int(prompt, lo=1, hi=9999):
    while True:
        try:
            v = int(input(f"  {prompt}: ").strip())
            if lo <= v <= hi:
                return v
            print(f"  ❌  Enter between {lo} and {hi}")
        except ValueError:
            print("  ❌  Numbers only")

def ask_rarity():
    opts = list(RARITY_MAP.keys())
    print("\n  Rarity (same for all images):")
    for i, r in enumerate(opts, 1):
        print(f"    {i}. {r}")
    while True:
        try:
            v = int(input("  Choose [1-5]: ").strip())
            if 1 <= v <= len(opts):
                return opts[v - 1]
            print(f"  ❌  Enter 1-{len(opts)}")
        except ValueError:
            print("  ❌  Numbers only")

def ask_folder():
    print("\n  Full path to image folder")
    print("  Example: C:\\Users\\YourName\\Pictures\\NFT_Images")
    while True:
        folder = input("  >> ").strip().strip('"').strip("'")
        if os.path.isdir(folder):
            return folder
        print(f"  ❌  Folder not found: {folder}")
        print("     Check the path and try again.")

def get_sorted_images(folder):
    """Return sorted list of image files in folder."""
    exts = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
    files = sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(exts)
    ])
    return files


# ════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        import pyperclip
    except ImportError:
        os.system("pip install pyperclip")
        import pyperclip

    print("\n" + "★"*55)
    print("  DRIP Collectibles — Upload Automation")
    print("★"*55)

    # Q1: How many photos
    total = ask_int("How many photos to upload", 1, 9999)

    # Q2: Rarity
    rarity = ask_rarity()

    # Q3: Image folder
    folder = ask_folder()
    images = get_sorted_images(folder)

    print(f"\n  Found {len(images)} images in folder (sorted alphabetically)")
    if len(images) < total:
        print(f"  ❌  Only {len(images)} images found but {total} requested!")
        exit()

    # Use images in order: 1st, 2nd, 3rd ... (no skipping)
    selected_images = images[:total]

    # Q4: Titles via popup
    print(f"\n  Opening title popup — paste {total} titles (one per line)...")
    titles = get_titles_popup(total)
    if not titles:
        print("  ❌  No titles. Exiting.")
        exit()

    # Build category list — cycle through all categories evenly
    per_cat   = max(1, total // len(CATEGORIES))
    remainder = total % len(CATEGORIES)
    categories = []
    for ci, cat in enumerate(CATEGORIES):
        n = per_cat + (1 if ci < remainder else 0)
        categories.extend([cat] * n)
    categories = categories[:total]

    # ── Summary ──────────────────────────────────────────
    print("\n" + "─"*55)
    print("  UPLOAD SUMMARY")
    print("─"*55)
    print(f"  Total    : {total}")
    print(f"  Rarity   : {rarity}")
    print(f"  Folder   : {folder}")
    print("─"*55)
    for i in range(min(total, 12)):
        img_name = os.path.basename(selected_images[i])
        print(f"  #{i+1:03d}  {titles[i][:30]:<30}  {img_name:<25}  [{categories[i]}]")
    if total > 12:
        print(f"  ... ({total-12} more)")
    print("─"*55)

    go = input("\n  Start? (y/n): ").strip().lower()
    if go != "y":
        print("  Cancelled.")
        exit()

    # ── Countdown ─────────────────────────────────────────
    print("\n" + "★"*55)
    print("  Starting in 5 seconds!")
    print("  Switch to browser → collectibles list page NOW!")
    print("★"*55)
    for i in range(5, 0, -1):
        print(f"  {i}...")
        time.sleep(1)
    print("  GO!\n")

    # ── Run ───────────────────────────────────────────────
    for i in range(total):
        process_one(
            index      = i,
            title      = titles[i],
            image_path = selected_images[i],
            category   = categories[i],
            rarity     = rarity,
        )

    print(f"\n\n🎉  All {total} collectibles uploaded as drafts!")