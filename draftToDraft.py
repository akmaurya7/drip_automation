import pyautogui
import pyperclip
import time
from PIL import ImageGrab, Image
import tkinter as tk
from tkinter import simpledialog, scrolledtext, messagebox

# ─────────────────────────────────────────────
# Reference dimensions (1456 x 816)
# ─────────────────────────────────────────────
REF_W = 1456
REF_H = 816

screen_w, screen_h = pyautogui.size()

# ─────────────────────────────────────────────
# COLLECTIBLES LIST — measured from Image 1
#
# Rows visible: TX(299), TX(339), On(379), DJ(419), Tm(459),
#               TV(500), TV(540), In(580), Ish(620), Did(660)
# Name column X ≈ 565
# ─────────────────────────────────────────────
LIST_NAME_X        = 565
LIST_ROW_Y = [299, 339, 379, 419, 459, 500, 540, 580, 620, 660]
LIST_ROWS_PER_PAGE = 10

# Pagination ">" next page — measured from Image 1
NEXT_PAGE_X = 893
NEXT_PAGE_Y = 721

# ─────────────────────────────────────────────
# EDIT PANEL — RIGHT SIDE PANEL
# Panel spans ref x ≈ 1119 → 1445
#
# Measured from Image 2 (BEFORE category is selected):
#   Name field       : x=1283, y=195
#   Description field: x=1283, y=258
#   Categories label : x=1283, y=312
#   Category input   : x=1283, y=350   ← type here
#   Dropdown result  : x=1187, y=377   ← "Art" row in dropdown (Image 3)
#
# ── BEFORE CATEGORY SELECTED (Image 2) ──────
#   Rarity label     : y=391
#   No Rarity btn    : x=1146, y=411
#   Rare btn         : x=1196, y=411
#   Legendary btn    : x=1262, y=411
#   Ultimate btn     : x=1340, y=411
#   Eternal btn      : x=1146, y=438
#   Image (media)    : x=1163, y=528
#   Browse btn       : x=1384, y=628
#   Save as Draft    : x=1292, y=738
#   Cancel           : x=1221, y=738
#
# ── AFTER CATEGORY SELECTED (Image 4) ───────
# The "ART ×" tag pill is inserted → panel content shifts DOWN ~21px:
#   Rarity label     : y=412
#   No Rarity btn    : x=1146, y=432
#   Rare btn         : x=1196, y=432
#   Legendary btn    : x=1262, y=432
#   Ultimate btn     : x=1340, y=432
#   Eternal btn      : x=1146, y=458
#   Image (media)    : x=1163, y=549
#   Browse btn       : x=1384, y=648
#   Save as Draft    : x=1292, y=738   ← same (fixed at bottom)
#   Cancel           : x=1221, y=738
# ─────────────────────────────────────────────

PANEL_NAME_X  = 1283
PANEL_NAME_Y  = 195

PANEL_DESC_X  = 1283
PANEL_DESC_Y  = 258

# Category input (the text box inside Categories section)
PANEL_CAT_INPUT_X   = 1200
PANEL_CAT_INPUT_Y   = 350

# Dropdown first result — "Art" row appears at y≈377 (Image 3)
PANEL_CAT_DROP_Y    = 377

# ── Rarity buttons — TWO sets of coords ──────────────────────
# Set A: BEFORE category selected (Image 2)
RARITY_BEFORE = {
    "No Rarity": (1146, 411),
    "Rare":      (1196, 411),
    "Legendary": (1262, 411),
    "Ultimate":  (1340, 411),
    "Eternal":   (1146, 438),
}

# Set B: AFTER category selected (Image 4) — everything shifted ~21px down
RARITY_AFTER = {
    "No Rarity": (1146, 432),
    "Rare":      (1196, 432),
    "Legendary": (1262, 432),
    "Ultimate":  (1340, 432),
    "Eternal":   (1146, 458),
}

# ── Image / Browse / Save — TWO sets ─────────────────────────
# BEFORE category (Image 2)
PANEL_IMAGE_BTN_BEFORE_X = 1163
PANEL_IMAGE_BTN_BEFORE_Y = 528
PANEL_BROWSE_BEFORE_X    = 1384
PANEL_BROWSE_BEFORE_Y    = 628

# AFTER category selected (Image 4)
PANEL_IMAGE_BTN_AFTER_X  = 1163
PANEL_IMAGE_BTN_AFTER_Y  = 549
PANEL_BROWSE_AFTER_X     = 1384
PANEL_BROWSE_AFTER_Y     = 648

# Save as Draft & Cancel — fixed at bottom, same in both states
PANEL_SAVE_DRAFT_X = 1292
PANEL_SAVE_DRAFT_Y = 738
PANEL_CANCEL_X     = 1221
PANEL_CANCEL_Y     = 738

# Back arrow (top-left of page) — for returning to collectibles list after save
BACK_ARROW_X = 25
BACK_ARROW_Y = 71

# ─────────────────────────────────────────────
# File manager dialog coords (unchanged)
# ─────────────────────────────────────────────
FM_FILETYPE_DROP_X = 1316
FM_FILETYPE_DROP_Y = 698
FM_ALL_FILES_X     = 1316
FM_ALL_FILES_Y     = 743
FM_GRID_START_X    = 262
FM_GRID_START_Y    = 207
FM_THUMB_W         = 122
FM_THUMB_H         = 186
FM_GRID_COLS       = 10
FM_OPEN_X          = 1264
FM_OPEN_Y          = 721

# ─────────────────────────────────────────────
# 10 Categories
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
# Core helpers
# ─────────────────────────────────────────────
def sc(x, y):
    return int(x * screen_w / REF_W), int(y * screen_h / REF_H)

def click(x, y, label="", delay=1.0):
    cx, cy = sc(x, y)
    print(f"    → [{label}] ref({x},{y}) → screen({cx},{cy})")
    pyautogui.moveTo(cx, cy, duration=0.4)
    pyautogui.click()
    time.sleep(delay)

def clear_and_paste(x, y, text, label=""):
    cx, cy = sc(x, y)
    pyautogui.moveTo(cx, cy, duration=0.3)
    pyautogui.tripleClick()
    time.sleep(0.2)
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('delete')
    time.sleep(0.2)
    pyperclip.copy(text)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.4)
    print(f"    → [{label}] = '{text[:45]}{'...' if len(text)>45 else ''}'")


# ─────────────────────────────────────────────
# Click a list row (0-based index on current page)
# ─────────────────────────────────────────────
def click_list_row(row_on_page):
    row_y = LIST_ROW_Y[row_on_page]
    print(f"    → Clicking list row #{row_on_page + 1} at ref({LIST_NAME_X}, {row_y})")
    click(LIST_NAME_X, row_y, f"List row {row_on_page + 1}", delay=2.0)


# ─────────────────────────────────────────────
# Go to next page
# ─────────────────────────────────────────────
def go_to_next_page():
    print(f"    → Clicking NEXT PAGE button")
    click(NEXT_PAGE_X, NEXT_PAGE_Y, "Next Page", delay=2.5)


# ─────────────────────────────────────────────
# Enter category → select from dropdown
# Uses PANEL_CAT_INPUT_Y (before-state coords)
# After clicking dropdown result, panel shifts down.
# All subsequent actions use AFTER coords.
# ─────────────────────────────────────────────
def enter_panel_category(category_text):
    print(f"    → Category: '{category_text}'")
    # Click the category input field
    cx, cy = sc(PANEL_CAT_INPUT_X, PANEL_CAT_INPUT_Y)
    pyautogui.moveTo(cx, cy, duration=0.3)
    pyautogui.click()
    time.sleep(0.4)

    # Clear any existing text
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('delete')
    time.sleep(0.2)

    # Paste category text via clipboard
    pyperclip.copy(category_text)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.3)   # wait for dropdown to render (Image 3 state)

    # Click first dropdown result (Image 3: "Art" highlighted at y≈377)
    click(PANEL_CAT_INPUT_X, PANEL_CAT_DROP_Y, f"Cat dropdown → {category_text}", delay=1.0)
    # ⚠️  After this click the panel shifts down (Image 4 state)
    # All clicks below MUST use AFTER coords


# ─────────────────────────────────────────────
# Select rarity — uses AFTER-category coords (Image 4)
# because rarity is always clicked AFTER category is set
# ─────────────────────────────────────────────
def select_rarity(rarity_name):
    if rarity_name not in RARITY_AFTER:
        print(f"    ⚠  Unknown rarity '{rarity_name}' — skipping")
        return
    rx, ry = RARITY_AFTER[rarity_name]
    click(rx, ry, f"Rarity: {rarity_name} [AFTER coords]", delay=0.8)


# ─────────────────────────────────────────────
# File manager: All Files → click nth file → Open
# ─────────────────────────────────────────────
def select_file_in_manager(file_index):
    print(f"    → File manager open — selecting file #{file_index + 1}")
    time.sleep(1.5)

    click(FM_FILETYPE_DROP_X, FM_FILETYPE_DROP_Y, "FileType dropdown", delay=0.8)
    click(FM_ALL_FILES_X,     FM_ALL_FILES_Y,     "All Files",         delay=0.8)

    col    = file_index % FM_GRID_COLS
    row    = file_index // FM_GRID_COLS
    file_x = FM_GRID_START_X + col * FM_THUMB_W
    file_y = FM_GRID_START_Y + row * FM_THUMB_H
    print(f"    → Grid pos: row={row}, col={col} → ref({file_x}, {file_y})")
    click(file_x, file_y, f"File #{file_index + 1}", delay=0.6)

    click(FM_OPEN_X, FM_OPEN_Y, "Open", delay=2.5)
    print(f"    → File #{file_index + 1} selected ✓")


# ─────────────────────────────────────────────
# Full flow for ONE collectible edit
#
# Coord timeline:
#   1. click_list_row         → opens panel (Image 2 state)
#   2. clear_and_paste Name   → Image 2 state
#   3. clear_and_paste Desc   → Image 2 state
#   4. enter_panel_category   → types + clicks dropdown
#                               PANEL SHIFTS DOWN (Image 4 state)
#   5. select_rarity          → AFTER coords ✓
#   6. click Image media btn  → AFTER coords ✓
#   7. click Browse           → AFTER coords ✓
#   8. select_file_in_manager → file dialog (separate window)
#   9. scroll + Save as Draft → fixed bottom coord ✓
# ─────────────────────────────────────────────
def process_one_edit(index, row_on_page, title, category, rarity):
    print(f"\n{'═'*60}")
    print(f"  EDIT #{index+1}  |  {title[:40]}")
    print(f"  Row: {row_on_page+1}   Category: {category}   Rarity: {rarity}")
    print(f"{'═'*60}")

    # 1. Click the row to open the edit panel
    click_list_row(row_on_page)

    # 2. Fill Name field (Image 2 coords)
    clear_and_paste(PANEL_NAME_X, PANEL_NAME_Y, title, "Name")
    time.sleep(0.3)

    # 3. Fill Description field (Image 2 coords)
    clear_and_paste(PANEL_DESC_X, PANEL_DESC_Y, title, "Description")
    time.sleep(0.3)

    # 4. Enter category + click dropdown
    #    ⚠️ After this step the panel shifts down to Image 4 layout
    enter_panel_category(category)
    time.sleep(0.5)

    # ── Everything below uses AFTER-category coords (Image 4) ──

    # 5. Select rarity (AFTER coords)
    select_rarity(rarity)

    # 6. Click "Image" media type button (AFTER coords: y=549)
    click(PANEL_IMAGE_BTN_AFTER_X, PANEL_IMAGE_BTN_AFTER_Y,
          "Image type [AFTER]", delay=1.5)

    # 7. Click Browse (AFTER coords: y=648)
    click(PANEL_BROWSE_AFTER_X, PANEL_BROWSE_AFTER_Y,
          "Browse [AFTER]", delay=2.5)

    # 8. File manager: select nth file
    select_file_in_manager(index)

    # 9. Wait for upload to complete
    time.sleep(3.5)

    # 10. Scroll down to reveal Save as Draft (fixed bottom)
    cx, cy = sc(PANEL_SAVE_DRAFT_X, 600)
    pyautogui.moveTo(cx, cy, duration=0.3)
    pyautogui.scroll(-6)
    time.sleep(0.8)

    # 11. Click Save as Draft (fixed bottom coord)
    click(PANEL_SAVE_DRAFT_X, PANEL_SAVE_DRAFT_Y, "Save as Draft", delay=3.5)

    # 12. Click back arrow TWICE to return to collectibles list
    click(BACK_ARROW_X, BACK_ARROW_Y, "Back ← (1st)", delay=1.5)
    click(BACK_ARROW_X, BACK_ARROW_Y, "Back ← (2nd)", delay=2.0)

    print(f"  ✅  #{index+1} saved as draft and back to list!")


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


def ask_titles(count):
    """Show a popup dialog to type or paste multiple titles (one per line)"""
    
    class TitleDialog(tk.Tk):
        def __init__(self, count):
            super().__init__()
            self.count = count
            self.result = None
            
            self.title("Enter Titles")
            self.geometry("750x600")
            self.resizable(True, True)
            self.attributes('-topmost', True)
            
            # Use grid layout for better control
            self.grid_rowconfigure(1, weight=1)
            self.grid_columnconfigure(0, weight=1)
            
            # Instructions (row 0)
            instr = tk.Label(self, 
                           text=f"Enter {count} titles (one per line):\nType manually or paste from clipboard",
                           font=("Arial", 11), fg="#333")
            instr.grid(row=0, column=0, pady=15, padx=15, sticky="ew")
            
            # Text area frame (row 1, expandable)
            text_frame = tk.Frame(self)
            text_frame.grid(row=1, column=0, pady=10, padx=15, sticky="nsew")
            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)
            
            # Scrollbar
            scrollbar = tk.Scrollbar(text_frame)
            scrollbar.grid(row=0, column=1, sticky="ns")
            
            # Text widget
            self.text_area = tk.Text(text_frame, height=25, width=90, font=("Courier", 10),
                                    yscrollcommand=scrollbar.set, wrap=tk.WORD)
            self.text_area.grid(row=0, column=0, sticky="nsew")
            scrollbar.config(command=self.text_area.yview)
            self.text_area.focus()
            
            # Button frame (row 2, fixed at bottom)
            btn_frame = tk.Frame(self, height=80)
            btn_frame.grid(row=2, column=0, pady=20, padx=15, sticky="ew")
            btn_frame.grid_propagate(False)
            
            confirm_btn = tk.Button(btn_frame, text="✓ CONFIRM", command=self.confirm,
                                   bg="#4CAF50", fg="white", font=("Arial", 13, "bold"),
                                   width=18, padx=20, pady=15, cursor="hand2")
            confirm_btn.pack(side=tk.LEFT, padx=15)
            
            cancel_btn = tk.Button(btn_frame, text="✗ CANCEL", command=self.cancel,
                                  bg="#f44336", fg="white", font=("Arial", 13, "bold"),
                                  width=18, padx=20, pady=15, cursor="hand2")
            cancel_btn.pack(side=tk.LEFT, padx=15)
            
            # Keyboard shortcuts
            self.bind("<Control-Return>", lambda e: self.confirm())
            self.bind("<Escape>", lambda e: self.cancel())
            
        def confirm(self):
            text = self.text_area.get("1.0", tk.END).strip()
            if not text:
                messagebox.showerror("Error", "Please enter at least one title", parent=self)
                return
            
            titles = [t.strip() for t in text.split("\n") if t.strip()]
            
            if len(titles) != self.count:
                messagebox.showerror("Error", 
                                   f"Expected {self.count} titles, got {len(titles)}", 
                                   parent=self)
                return
            
            self.result = titles
            self.destroy()
            
        def cancel(self):
            self.result = None
            self.destroy()
    
    dialog = TitleDialog(count)
    dialog.mainloop()
    
    if dialog.result is None:
        print("  ❌  Title input cancelled.")
        exit()
    
    return dialog.result


def ask_rarity():
    print("""
  Select rarity (applies to ALL uploads):
    1. No Rarity
    2. Rare
    3. Legendary
    4. Ultimate
    5. Eternal
""")
    opts = ["No Rarity", "Rare", "Legendary", "Ultimate", "Eternal"]
    while True:
        try:
            v = int(input("  Enter 1-5: ").strip())
            if 1 <= v <= 5:
                return opts[v - 1]
            print("  ❌  Enter a number between 1 and 5")
        except ValueError:
            print("  ❌  Please enter a valid number")


def ask_category_mode(count):
    print("""
  Category assignment mode:
    1. SAME    → all uploads get the same category
    2. CYCLE   → cycles through all 10 in order
    3. MANUAL  → pick per upload
""")
    while True:
        m = input("  Enter 1 / 2 / 3: ").strip()
        if m in ("1", "2", "3"):
            break
        print("  ❌  Enter 1, 2, or 3")

    if m == "1":
        print("\n  Available categories:")
        for i, c in enumerate(CATEGORIES, 1):
            print(f"    {i:2d}. {c}")
        idx = ask_int("Choose category number", 1, len(CATEGORIES))
        return [CATEGORIES[idx - 1]] * count

    elif m == "2":
        return [CATEGORIES[i % len(CATEGORIES)] for i in range(count)]

    else:
        print("\n  Available categories:")
        for i, c in enumerate(CATEGORIES, 1):
            print(f"    {i:2d}. {c}")
        cats = []
        for i in range(count):
            idx = ask_int(f"Category for upload #{i+1}", 1, len(CATEGORIES))
            cats.append(CATEGORIES[idx - 1])
        return cats


def ask_starting_row():
    print("""
  Which row on the CURRENT PAGE to start from?
  (Starting fresh from page 1? Enter 1)
""")
    return ask_int("Starting row on current page", 1, LIST_ROWS_PER_PAGE) - 1


# ════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════

print("\n" + "★"*60)
print("  DRIP Collectibles — Edit & Save as Draft Automation")
print("★"*60)

print()
total      = ask_int("How many collectibles to edit", 1, 200)
titles     = ask_titles(total)
rarity     = ask_rarity()
categories = ask_category_mode(total)
start_row  = ask_starting_row()

# ── Summary ─────────────────────────────────────────────
print("\n" + "─"*60)
print("  EDIT SUMMARY")
print("─"*60)
print(f"  Total        : {total}")
print(f"  Rarity       : {rarity}")
print(f"  Starting row : {start_row + 1} (on current page)")
print("─"*60)
for i in range(total):
    print(f"  #{i+1:03d}  [{categories[i]:<22}]  {titles[i][:35]}")
print("─"*60)
print()
print("  ⚠  IMPORTANT:")
print("     - Script clicks list rows sequentially, auto-advances pages")
print("     - Make sure you are ON the correct starting page in browser!")
print("     - Images must be sorted correctly in your upload folder")
print()
print("  ℹ  Coord note:")
print("     Rarity / Image / Browse use POST-CATEGORY coords")
print("     (panel shifts down after category tag is added)")

confirm = input("\n  Start automation? (y/n): ").strip().lower()
if confirm != "y":
    print("\n  Cancelled.")
    exit()

# ── Countdown ───────────────────────────────────────────
print("\n" + "★"*60)
print("  Starting in 10 seconds!")
print("  Switch to browser → Collectibles list page NOW!")
print("★"*60)
for i in range(10, 0, -1):
    print(f"  {i}...")
    time.sleep(1)
print("  GO!\n")

# ── Run ─────────────────────────────────────────────────
current_row_on_page = start_row

for i in range(total):
    process_one_edit(
        index       = i,
        row_on_page = current_row_on_page,
        title       = titles[i],
        category    = categories[i],
        rarity      = rarity,
    )

    current_row_on_page += 1
    if current_row_on_page >= LIST_ROWS_PER_PAGE and i < total - 1:
        print(f"\n  📄  Page complete — going to next page...")
        go_to_next_page()
        current_row_on_page = 0
        time.sleep(1.0)

print(f"\n\n🎉  All {total} collectibles edited and saved as draft!")