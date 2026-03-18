import tkinter as tk
from tkinter import messagebox, Menu, filedialog
import keyboard
import threading
import sys
import os
import time
from PIL import Image, ImageTk
import ctypes


class GeezIME:
    def __init__(self, root):
        self.root = root
        self.root.title("Geez IME Status")
        self.ime_enabled = True
        self.key_buffer = ""
        self.input_mode = "translit"  # translit | amharic | tigrinya
        self.lock = threading.Lock()
        self.toggle_hotkey = 'f12'
        self.is_processing = False
        self.writer_windows = []

        # Custom icon support
        self.setup_icon()

        self.status_label = tk.Label(root, text="ግ", font=("Nyala", 14), fg="white", bg="blue", cursor="fleur")
        self.status_label.pack(pady=2, padx=5)

        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.geometry("+300+300")

        self.status_label.bind("<ButtonPress-1>", self.start_move)
        self.status_label.bind("<ButtonRelease-1>", self.stop_move)
        self.status_label.bind("<B1-Motion>", self.on_move)
        self.status_label.bind("<Double-Button-1>", lambda e: self.toggle_ime())

        self.setup_transliteration_map()
        self.setup_layout_maps()
        self.setup_context_menu()

        # Global key hook
        keyboard.hook(self.handle_key_event, suppress=True)

        # Initial status + Caps/Num Lock polling (real-time indicator)
        self.update_status_label()
        self.lock_poll_thread = threading.Thread(target=self.poll_lock_states, daemon=True)
        self.lock_poll_thread.start()

    def setup_icon(self):
        """Try to set custom application icon"""
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            icon_path = os.path.join(base_path, "geezime.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception:
            pass

    def update_status_label(self):
        """Update the floating status window with IME state + Caps/Num Lock indicators"""
        if not self.ime_enabled:
            self.status_label.config(text="EN", bg="red", fg="white")
        else:
            caps_indicator = " ↑" if self.is_caps_lock_on() else ""
            num_indicator = " #" if self.is_num_lock_on() else ""
            self.status_label.config(text=f"ግ{caps_indicator}{num_indicator}", bg="blue", fg="white")

    def poll_lock_states(self):
        """Background thread that detects ANY Caps/Num Lock change"""
        prev_caps = self.is_caps_lock_on()
        prev_num = self.is_num_lock_on()
        while True:
            current_caps = self.is_caps_lock_on()
            current_num = self.is_num_lock_on()
            if current_caps != prev_caps or current_num != prev_num:
                self.root.after(0, self.update_status_label)
                prev_caps = current_caps
                prev_num = current_num
            time.sleep(0.2)  # 200ms for responsiveness
            
    def setup_context_menu(self):
        self.context_menu = Menu(self.root, tearoff=0)
        self.help_menu = Menu(self.context_menu, tearoff=0)
        self.help_menu.add_command(label="GeezIME Help", command=self.open_help)
        self.help_menu.add_command(label="About GeezIME", command=self.show_about_window)
        self.context_menu.add_cascade(label="Help", menu=self.help_menu)
        self.context_menu.add_separator()

        self.start_with_windows_var = tk.BooleanVar()
        self.start_with_windows_var.set(self.is_startup_enabled())
        self.context_menu.add_checkbutton(
            label="Start with Windows", variable=self.start_with_windows_var, command=self.toggle_startup
        )

        # Input mode submenu
        self.input_mode_var = tk.StringVar(value=self.input_mode)
        mode_menu = Menu(self.context_menu, tearoff=0)
        mode_menu.add_radiobutton(
            label="Transliteration (default)",
            variable=self.input_mode_var,
            value="translit",
            command=lambda: self.set_input_mode("translit"),
        )
        mode_menu.add_radiobutton(
            label="Amharic Layout",
            variable=self.input_mode_var,
            value="amharic",
            command=lambda: self.set_input_mode("amharic"),
        )
        mode_menu.add_radiobutton(
            label="Tigrinya Layout",
            variable=self.input_mode_var,
            value="tigrinya",
            command=lambda: self.set_input_mode("tigrinya"),
        )
        self.context_menu.add_cascade(label="Input Mode", menu=mode_menu)

        self.context_menu.add_command(label="Open Writer", command=self.open_writer_window)
        self.context_menu.add_command(label="On-screen Keyboard", command=self.open_onscreen_keyboard)
        self.context_menu.add_command(label="Tigrinya Keyboard", command=self.show_keyboard_layout_window)
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label=f"Geez On/Off ({self.toggle_hotkey.upper()})", command=self.toggle_ime
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Close GeezIME", command=self.on_close)

        self.status_label.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def toggle_ime(self):
        self.ime_enabled = not self.ime_enabled
        self.key_buffer = ""
        self.update_status_label()

    def is_caps_lock_on(self):
        """Reliable Windows Caps Lock check (VK_CAPITAL = 0x14)"""
        return bool(ctypes.windll.user32.GetKeyState(0x14) & 0x0001)

    def is_num_lock_on(self):
        """Reliable Windows Num Lock check (VK_NUMLOCK = 0x90)"""
        return bool(ctypes.windll.user32.GetKeyState(0x90) & 0x0001)

    def handle_key_event(self, event):
        # Always allow events generated by our own keyboard.write/send
        if self.is_processing:
            return True

        with self.lock:
            self.is_processing = True
            try:
                is_down = event.event_type == keyboard.KEY_DOWN
                key_name = event.name
                
                # Normalize Numpad keys immediately (e.g., 'numpad 1' -> '1')
                if key_name.startswith('numpad '):
                    key_name = key_name.replace('numpad ', '')

                # --- Hotkey Logic ---
                if is_down and key_name == self.toggle_hotkey:
                    self.toggle_ime()
                    return False

                # Instant indicator updates
                if is_down and key_name in ('caps lock', 'num lock'):
                    self.root.after(0, self.update_status_label)

                # If IME is disabled, let everything pass through
                if not self.ime_enabled:
                    return True

                # --- Passthrough Logic (Modifiers and Shortcuts) ---
                is_modifier = key_name in ('ctrl', 'alt', 'windows', 'cmd', 'left windows', 
                                             'right windows', 'alt gr', 'shift', 'caps lock', 'num lock')
                is_shortcut = keyboard.is_pressed('ctrl') or keyboard.is_pressed('alt') or keyboard.is_pressed('cmd')
                
                # Special keys like Enter, Tab, etc. (names longer than 1 char)
                # We exclude space, backspace, and normalized numpad digits
                is_digit = key_name.isdigit() and key_name != '0'
                is_special_key = len(key_name) > 1 and key_name not in ('space', 'backspace') and not is_digit

                if is_modifier or is_shortcut or is_special_key:
                    if is_down and not is_modifier:
                        self.key_buffer = ""
                    return True

                # Do not suppress key-up events; only suppress key-down we actually handle.
                if not is_down:
                    return True

                # Early check for Numpad operators to let them pass through
                numpad_operators = {'+', '-', '*', '/', '.', 'enter'}
                if event.name.startswith('numpad ') and key_name in numpad_operators:
                    self.key_buffer = ""
                    return True

                # Direct layout modes: map single keystrokes to Ethiopic characters
                if self.input_mode in ("amharic", "tigrinya"):
                    layout = self.layout_maps.get(self.input_mode, {})
                    mapped = layout.get(key_name)
                    if mapped:
                        keyboard.write(mapped)
                        return False
                    # Not a mapped key in layout mode; let it fall back to normal typing
                    return True

                is_shifted = keyboard.is_pressed('shift')
                is_caps = self.is_caps_lock_on()

                # --- NEW: Shift Logic for Numbers & Symbols ---
                if is_shifted:
                    key_name = self.get_shifted_key(key_name)

                # --- Character Logic with Shift and Caps Lock interaction (Letters Only) ---
                if key_name.isalpha() and len(key_name) == 1:
                    if is_shifted != is_caps:
                        key_name = key_name.upper()
                    else:
                        key_name = key_name.lower()
                
                if key_name == 'space':
                    self.key_buffer = ""
                    return True

                # Check if it's a Geez-related key (including numbers 1-9)
                is_geez_key = key_name in self.prefixes or key_name in self.transliteration_map

                if not is_geez_key:
                    self.key_buffer = ""
                    return True

                if key_name == 'backspace':
                    if self.key_buffer:
                        old_buffer = self.key_buffer
                        self.key_buffer = self.key_buffer[:-1]
                        if old_buffer in self.transliteration_map:
                            keyboard.write('\b')
                            if self.key_buffer in self.transliteration_map:
                                keyboard.write(
                                    self.transliteration_map[self.key_buffer])
                        return False
                    else:
                        return True

                # --- Transliteration Logic ---
                new_buffer = self.key_buffer + key_name
                is_prefix = new_buffer in self.prefixes
                is_match = new_buffer in self.transliteration_map

                # If the current sequence is invalid
                if not is_prefix and not is_match:
                    # Check if the key itself is a valid start of a sequence
                    if is_geez_key:
                        # Commit the current buffer as a new starting point
                        self.key_buffer = key_name
                        match = self.transliteration_map.get(key_name)
                        if match:
                            keyboard.write(match)
                        return False  # Suppress original key
                    else:
                        # Not a Geez-related key (e.g. Enter, Escape, Arrow keys), let it through
                        self.key_buffer = ""
                        return True

                # Valid sequence or prefix
                self.key_buffer = new_buffer
                if is_match:
                    # Replace previous character if it was a match
                    prev_buffer = new_buffer[:-1]
                    num_backspaces = 1 if prev_buffer in self.transliteration_map else 0
                    keyboard.write('\b' * num_backspaces +
                                   self.transliteration_map[new_buffer])

                    if not is_prefix:
                        self.key_buffer = ""

                return False  # Suppress original key as we've handled it
            finally:
                self.is_processing = False

    def get_shifted_key(self, key):
        shift_map = {
            '1': '!', '2': '@', '3': '#', '4': '$', '5': '%', '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
            '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|', ';': ':', "'": '"', ',': '<', '.': '>', '/': '?',
            '`': '~'
        }
        return shift_map.get(key, key.upper())

    def setup_transliteration_map(self):
        # Transliteration model:
        # - Consonant families are generated from their base "e" (1st order) character.
        # - Suffixes: e,u,i,a,ie,(none),o map to orders 1..7 respectively.
        def add_family(m, token, base_char):
            base = ord(base_char)
            m[token + 'e'] = chr(base + 0)
            m[token + 'u'] = chr(base + 1)
            m[token + 'i'] = chr(base + 2)
            m[token + 'a'] = chr(base + 3)
            m[token + 'ie'] = chr(base + 4)
            m[token] = chr(base + 5)
            m[token + 'o'] = chr(base + 6)

        self.transliteration_map = {}

        families = {
            # Basic families
            'h': 'ሀ',
            'l': 'ለ',
            'H': 'ሐ',
            'm': 'መ',
            's2': 'ሠ',
            'r': 'ረ',
            's': 'ሰ',
            'S': 'ሸ',
            'q': 'ቀ',
            'Q': 'ቐ',
            'b': 'በ',
            'v': 'ቨ',
            't': 'ተ',
            'c': 'ቸ',
            'h2': 'ኀ',
            'n': 'ነ',
            'N': 'ኘ',
            'k': 'ከ',
            'K': 'ኸ',
            'w': 'ወ',
            'O': 'ዐ',
            'z': 'ዘ',
            'Z': 'ዠ',
            'y': 'የ',
            'd': 'ደ',
            'j': 'ጀ',
            'g': 'ገ',
            'T': 'ጠ',
            'C': 'ጨ',
            'P': 'ጰ',
            'x': 'ፀ',
            'x2': 'ጸ',
            'f': 'ፈ',
            'p': 'ፐ',
        }

        for token, base_char in families.items():
            add_family(self.transliteration_map, token, base_char)

        # Labialized / "W" forms (kept explicit; not all are contiguous blocks)
        self.transliteration_map.update({
            # qW / QW / kW / KW / gW / hW families as used in the original mapping
            'que': 'ቈ', 'qui': 'ቊ', 'qua': 'ቋ', 'quie': 'ቌ', 'qW': 'ቍ',
            'Que': 'ቘ', 'Qui': 'ቚ', 'Qua': 'ቛ', 'Quie': 'ቜ', 'QW': 'ቝ',
            'kue': 'ኰ', 'kui': 'ኲ', 'kua': 'ኳ', 'kuie': 'ኴ', 'kW': 'ኵ',
            'Kue': 'ዀ', 'Kui': 'ዂ', 'Kua': 'ዃ', 'Kuie': 'ዄ', 'KW': 'ዅ',
            'gue': 'ጐ', 'gui': 'ጒ', 'gua': 'ጓ', 'guie': 'ጔ', 'gW': 'ጕ',
            'hue': 'ኈ', 'hui': 'ኊ', 'hua': 'ኋ', 'huie': 'ኌ', 'hW': 'ኍ',
        })

        # Standalone vowels (both አ-family and ዐ-family)
        self.transliteration_map.update({
            # አ series
            'e': 'አ', 'u': 'ኡ', 'i': 'ኢ', 'a': 'ኣ', 'ie': 'ኤ', 'E': 'እ', 'o': 'ኦ',
            # ዐ series (upper-case O prefix)
            'Oe': 'ዐ', 'Ou': 'ዑ', 'Oi': 'ዒ', 'Oa': 'ዓ', 'Oie': 'ዔ', 'O': 'ዕ', 'Oo': 'ዖ',
        })

        # Ethiopic punctuation (and a couple of useful digraphs)
        self.transliteration_map.update({
            '.': '።',
            ',': '፣',
            ';': '፤',
            ':': '፡',
            ';-': '፥',
            '::': '።',
        })

        # Ethiopic numerals in transliteration mode (single digits)
        self.transliteration_map.update({
            '1': '፩',
            '2': '፪',
            '3': '፫',
            '4': '፬',
            '5': '፭',
            '6': '፮',
            '7': '፯',
            '8': '፰',
            '9': '፱',
            '0': '፲',
        })

        # Pre-calculate prefixes for performance and reliable sequence detection
        self.prefixes = set()
        for key in self.transliteration_map.keys():
            for i in range(1, len(key)):
                self.prefixes.add(key[:i])

    def setup_layout_maps(self):
        """Build simple single-keystroke Ethiopic layouts for Amharic/Tigrinya."""
        self.layout_maps = {"amharic": {}, "tigrinya": {}}

        # Use existing transliteration families to derive a practical single-key layout:
        # for each base family token, map its Latin key to the "a" form (4th order) glyph.
        base_tokens = [
            'h', 'l', 'H', 'm', 's2', 'r', 's', 'S', 'q', 'Q',
            'b', 'v', 't', 'c', 'h2', 'n', 'N', 'k', 'K', 'w',
            'O', 'z', 'Z', 'y', 'd', 'j', 'g', 'T', 'C', 'P',
            'x', 'x2', 'f', 'p',
        ]

        amharic = self.layout_maps["amharic"]
        tigrinya = self.layout_maps["tigrinya"]

        for token in base_tokens:
            a_key = token + "a"
            glyph = self.transliteration_map.get(a_key)
            if not glyph:
                continue
            # Map both lower/upper-case Latin letters that correspond to this token
            base_char = token[0]
            for k in {base_char.lower(), base_char.upper()}:
                amharic[k] = glyph
                tigrinya[k] = glyph

        # Standalone vowels (mapped directly on their Latin keys)
        vowel_map = {
            'e': self.transliteration_map.get('e'),
            'u': self.transliteration_map.get('u'),
            'i': self.transliteration_map.get('i'),
            'a': self.transliteration_map.get('a'),
            'o': self.transliteration_map.get('o'),
        }
        for k, v in vowel_map.items():
            if not v:
                continue
            for layout in (amharic, tigrinya):
                layout[k] = v
                layout[k.upper()] = v

        # Ethiopic punctuation on standard punctuation keys
        punct_pairs = {
            '.': self.transliteration_map.get('.'),
            ',': self.transliteration_map.get(','),
            ';': self.transliteration_map.get(';'),
            ':': self.transliteration_map.get(':'),
        }
        for k, v in punct_pairs.items():
            if not v:
                continue
            for layout in (amharic, tigrinya):
                layout[k] = v

        # Ethiopic numerals on the number row in layout modes
        numerals = {
            '1': '፩',
            '2': '፪',
            '3': '፫',
            '4': '፬',
            '5': '፭',
            '6': '፮',
            '7': '፯',
            '8': '፰',
            '9': '፱',
            '0': '፲',
        }
        for k, v in numerals.items():
            for layout in (amharic, tigrinya):
                layout[k] = v

    def set_input_mode(self, mode: str):
        if mode not in ("translit", "amharic", "tigrinya"):
            return
        self.input_mode = mode
        if hasattr(self, "input_mode_var"):
            self.input_mode_var.set(mode)

    def open_writer_window(self):
        win = tk.Toplevel(self.root)
        win.title("Geez Writer")
        win.geometry("900x600")
        win.minsize(600, 400)

        text = tk.Text(win, wrap="word", font=("Nyala", 16), undo=True)
        text.pack(fill="both", expand=True)

        def do_open():
            path = filedialog.askopenfilename(
                title="Open",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not path:
                return
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = f.read()
                text.delete("1.0", "end")
                text.insert("1.0", data)
            except Exception as e:
                messagebox.showerror("Open failed", str(e))

        def do_save_as():
            path = filedialog.asksaveasfilename(
                title="Save As",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            )
            if not path:
                return
            try:
                data = text.get("1.0", "end-1c")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(data)
            except Exception as e:
                messagebox.showerror("Save failed", str(e))

        menubar = Menu(win)
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open…", command=do_open)
        file_menu.add_command(label="Save As…", command=do_save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=win.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        win.config(menu=menubar)

        self.writer_windows.append(win)
        win.bind("<Destroy>", lambda e: self.writer_windows.remove(win) if win in self.writer_windows else None)

    def open_onscreen_keyboard(self):
        """Simple on-screen Geez keyboard that types into the active window."""
        kb = tk.Toplevel(self.root)
        kb.title("Geez On-screen Keyboard")
        kb.attributes("-topmost", True)

        # Common Geez characters grouped roughly by families / usage
        rows = [
            "ሀሁሂሃሄህሆ ለሉሊላሌልሎ መሙሚማሜምሞ",
            "ረሩሪራሬርሮ ሰሱሲሳሴስሶ ሸሹሺሻሼሽሾ",
            "ቀቁቂቃቄቅቆ በቡቢባቤብቦ ተቱቲታቴትቶ",
            "ነኑኒናኔንኖ ከኩኪካኬክኮ ወዉዊዋዌውዎ",
            "ዘዙዚዛዜዝዞ ዠዡዢዣዤዥዦ የዩዪያዬይዮ",
            "ደዱዲዳዴድዶ ጀጁጂጃጄጅጆ ገጉጊጋጌግጎ",
            "ጠጡጢጣጤጥጦ ጨጩጪጫጬጭጮ ጰጱጲጳጴጵጶ",
            "ፀፁፂፃፄፅፆ ጸጹጺጻጼጽጾ ፈፉፊፋፌፍፎ",
            "ፐፑፒፓፔፕፖ ፩፪፫፬፭፮፯፰፱፲",
            "።፣፤፡፥",
        ]

        def insert_char(ch: str):
            # Type directly into the currently focused control
            keyboard.write(ch)

        for r, line in enumerate(rows):
            col = 0
            for ch in line:
                if ch == " ":
                    col += 1
                    continue
                btn = tk.Button(
                    kb,
                    text=ch,
                    width=2,
                    font=("Nyala", 14),
                    command=lambda c=ch: insert_char(c),
                )
                btn.grid(row=r, column=col, padx=1, pady=1, sticky="nsew")
                col += 1

        # Make the keyboard nicely resizable
        for i in range(20):
            kb.grid_columnconfigure(i, weight=1)

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def on_close(self):
        if messagebox.askokcancel("Quit", "Do you want to quit GeezIME?"):
            keyboard.unhook_all()
            self.root.destroy()
            sys.exit()

    def show_about_window(self):
        about_win = tk.Toplevel(self.root)
        about_win.title("About GeezIME")
        about_win.geometry("350x180")
        about_win.resizable(False, False)
        about_win.transient(self.root)
        about_win.grab_set()
        tk.Label(about_win, text="GeezIME III", font=("Nyala", 24, "bold")).pack(pady=(10, 0))
        tk.Label(
            about_win,
            text="Developer: Samrawi Berhe, Senior Fullstack Developer (Python), 12+ years experience.",
            font=("Segoe UI", 9),
            wraplength=320,
            justify="center",
        ).pack(pady=(8, 4))
        tk.Label(
            about_win,
            text="© 2026 SAMI Blue Software Solutions PLC.\nSAMI Born To Sail",
            font=("Segoe UI", 9, "italic"),
            justify="center",
        ).pack(pady=(10, 10))
        tk.Button(about_win, text="OK", command=about_win.destroy, width=10).pack()
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - about_win.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - about_win.winfo_height()) // 2
        about_win.geometry(f"+{x}+{y}")

    def show_keyboard_layout_window(self):
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            image_path = os.path.join(base_path, "keyboard_layout.png")
            layout_win = tk.Toplevel(self.root)
            layout_win.title("Tigrinya Keyboard Layout")
            img = Image.open(image_path)
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(layout_win, image=photo)
            label.image = photo
            label.pack()
        except Exception as e:
            messagebox.showerror("Error", f"Could not open keyboard layout: {e}")

    def open_help(self):
        help_file = "GeezIME_help.html"
        try:
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
            file_path = os.path.join(base_path, help_file)
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open help file: {e}")

    def get_startup_folder(self):
        return os.path.join(os.getenv('APPDATA'), 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')

    def is_startup_enabled(self):
        return os.path.exists(os.path.join(self.get_startup_folder(), "GeezIME.bat"))

    def toggle_startup(self):
        if self.start_with_windows_var.get():
            self.enable_startup()
        else:
            self.disable_startup()

    def enable_startup(self):
        shortcut_path = os.path.join(self.get_startup_folder(), "GeezIME.bat")
        batch_content = f'start "" "{sys.executable}" "{os.path.abspath(sys.argv[0])}"'
        try:
            with open(shortcut_path, "w") as f:
                f.write(batch_content)
            return True
        except Exception:
            return False

    def disable_startup(self):
        shortcut_path = os.path.join(self.get_startup_folder(), "GeezIME.bat")
        try:
            if os.path.exists(shortcut_path):
                os.remove(shortcut_path)
            return True
        except Exception:
            return False


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def main():
    # Single instance check: ensure only one copy is running
    # Using a global mutex via Win32 API
    mutex_name = "GeezIME_SingleInstance_Mutex"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()
    
    # ERROR_ALREADY_EXISTS = 183
    if last_error == 183:
        # Program is already running
        # We can find the existing window and bring it to foreground if we want, 
        # but for an IME, simply exiting is standard.
        ctypes.windll.user32.MessageBoxW(0, "GeezIME is already running.", "GeezIME", 0x40 | 0x0)
        sys.exit(0)

    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit()

    root = tk.Tk()
    app = GeezIME(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
