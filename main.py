import os
import json
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import math
import uuid
from datetime import datetime

# Import Core Modules (OOP)
from core.logger import ActionLogger
from core.converter import FileConverter
from core.organizer import FileOrganizer
from core.cleaner import StorageCleaner
from core.watcher import WatcherManager
from core.ai_assistant import AIAssistant

# Theme Colors (Modern Light/Purple)
BG_MAIN = "#F3F5F9"
BG_CARD = "#FFFFFF"
TEXT_MAIN = "#1F2937"
TEXT_MUTED = "#6B7280"
ACCENT_PRIMARY = "#7C3AED" # Purple
ACCENT_HOVER = "#6D28D9"
ACCENT_SUCCESS = "#10B981"
ACCENT_WARNING = "#F59E0B"
ACCENT_DANGER = "#EF4444"
SIDEBAR_BG = "#FFFFFF"

ctk.set_appearance_mode("Light")

class SmartFileManagerApp(ctk.CTk):
    def get_embedded_api_key(self):
        import sys
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.abspath(os.path.dirname(__file__))
        key_path = os.path.join(base_path, "api_key.txt")
        if os.path.exists(key_path):
            with open(key_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""

    def __init__(self):
        super().__init__()

        self.title("ZipZap - Smart File Manager")
        self.geometry("1200x800")
        self.minsize(1000, 700)
        self.configure(fg_color=BG_MAIN)
        
        self.config_file = "config.json"
        self.config_data = self.load_config()
        self.current_folder = ""
        self.folder_btns = []
        
        embedded_key = self.get_embedded_api_key()
        final_key = embedded_key if embedded_key else self.config_data.get("gemini_api_key", "")
        
        # Set Window Icon
        try:
            import sys
            import tkinter as tk
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.abspath(os.path.dirname(__file__))
            
            if os.name == 'nt':
                self.iconbitmap(os.path.join(base_path, "icon.ico"))
            else:
                icon_img = tk.PhotoImage(file=os.path.join(base_path, "icon.png"))
                self.iconphoto(False, icon_img)
        except Exception as e:
            print("Failed to set icon:", e)
        
        # Instantiate OOP Core Managers
        self.logger = ActionLogger()
        self.converter = FileConverter(self.logger)
        self.organizer = FileOrganizer(self.logger, final_key)
        self.cleaner = StorageCleaner(self.logger)
        self.watcher_manager = WatcherManager(self.logger)
        self.ai_assistant = AIAssistant(final_key)
        self.sync_excluded_folders()

        self.setup_ui()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except: pass
        return {"watch_folder": "", "gemini_api_key": "", "theme": "Light"}

    def save_config(self, key, value):
        self.config_data[key] = value
        with open(self.config_file, "w") as f:
            json.dump(self.config_data, f, indent=4)
        
        if key == "theme":
            ctk.set_appearance_mode(value)

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=SIDEBAR_BG)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(30, 30), sticky="w")
        ctk.CTkLabel(logo_frame, text="⚡", font=ctk.CTkFont(size=28), text_color=ACCENT_PRIMARY).pack(side="left")
        ctk.CTkLabel(logo_frame, text=" ZipZap", font=ctk.CTkFont(family="Helvetica", size=22, weight="bold"), text_color=ACCENT_PRIMARY).pack(side="left", padx=(5,0))

        # Nav Buttons
        self.nav_btns = []
        def create_nav_btn(text, row, command):
            btn = ctk.CTkButton(self.sidebar_frame, text=text, command=lambda c=command, r=row: self.handle_nav(c, r), 
                                fg_color="transparent", text_color=TEXT_MUTED, hover_color=BG_MAIN, 
                                font=ctk.CTkFont(family="Helvetica", size=15, weight="bold"), anchor="w", height=45)
            btn.grid(row=row, column=0, padx=15, pady=5, sticky="ew")
            self.nav_btns.append(btn)
            return btn

        self.btn_dashboard = create_nav_btn("  Dashboard", 1, self.show_dashboard)
        self.btn_cleaner = create_nav_btn("  Smart Cleaner", 2, self.show_cleaner)
        self.btn_converter = create_nav_btn("  Converter", 3, self.show_converter)
        self.btn_ai = create_nav_btn("  AI Help Chat", 4, self.show_ai_chat)
        self.btn_monitor = create_nav_btn("  Auto Monitor", 5, self.show_monitor)
        self.btn_settings = create_nav_btn("  Settings", 6, self.show_settings)

        # Theme Toggle
        theme_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        theme_frame.grid(row=8, column=0, padx=20, pady=20, sticky="w")
        self.switch_theme = ctk.CTkSwitch(theme_frame, text="Dark Mode", command=self.toggle_theme, progress_color=ACCENT_PRIMARY)
        self.switch_theme.pack()
        if self.config_data.get("theme") == "Dark":
            self.switch_theme.select()

        # --- Main Content Area ---
        self.main_frame = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        self.main_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")

        # Top Bar (Header)
        self.topbar = ctk.CTkFrame(self.main_frame, height=60, fg_color=BG_CARD, corner_radius=0)
        self.topbar.pack(fill="x")
        self.lbl_page_title = ctk.CTkLabel(self.topbar, text="Dashboard", font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"), text_color=TEXT_MAIN)
        self.lbl_page_title.pack(side="left", padx=30, pady=15)

        # Container for pages
        self.content_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True)

        self.frames = {}
        self.create_dashboard()
        self.create_cleaner()
        self.create_converter()
        self.create_ai_chat()
        self.create_monitor()
        self.create_settings()
        
        # Select first nav
        self.handle_nav(self.show_dashboard, 1)

    def handle_nav(self, command, row):
        for idx, btn in enumerate(self.nav_btns):
            if idx + 1 == row:
                btn.configure(fg_color=f"{ACCENT_PRIMARY}1A", text_color=ACCENT_PRIMARY) # 1A is ~10% opacity in hex, but CTK uses fg_color
                # Workaround for tint: just use a light purple or solid
                btn.configure(fg_color="#EDE9FE", text_color=ACCENT_PRIMARY)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)
        command()

    def hide_all_frames(self):
        for frame in self.frames.values():
            frame.pack_forget()

    def show_dashboard(self):
        self.hide_all_frames()
        self.lbl_page_title.configure(text="Dashboard")
        self.frames["dashboard"].pack(fill="both", expand=True, padx=30, pady=20)
        self.update_dashboard_stats()

    def show_cleaner(self):
        self.hide_all_frames()
        self.lbl_page_title.configure(text="Smart Cleaner")
        self.frames["cleaner"].pack(fill="both", expand=True, padx=30, pady=20)

    def show_converter(self):
        self.hide_all_frames()
        self.lbl_page_title.configure(text="Universal Converter")
        self.frames["converter"].pack(fill="both", expand=True, padx=30, pady=20)

    def show_ai_chat(self):
        self.hide_all_frames()
        self.lbl_page_title.configure(text="AI Help Chat")
        self.frames["ai"].pack(fill="both", expand=True, padx=30, pady=20)

    def show_monitor(self):
        self.hide_all_frames()
        self.lbl_page_title.configure(text="Auto Monitor")
        self.frames["monitor"].pack(fill="both", expand=True, padx=30, pady=20)

    def show_settings(self):
        self.hide_all_frames()
        self.lbl_page_title.configure(text="Settings")
        self.frames["settings"].pack(fill="both", expand=True, padx=30, pady=20)

    def toggle_theme(self):
        theme = "Dark" if self.switch_theme.get() == 1 else "Light"
        self.save_config("theme", theme)

    # ================= UI CREATION METHODS =================
    
    def create_dashboard(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.frames["dashboard"] = frame
        
        # Top Row
        top_row = ctk.CTkFrame(frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(0, 20))
        
        # Storage Overview Card
        storage_card = ctk.CTkFrame(top_row, fg_color=BG_CARD, corner_radius=15)
        storage_card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(storage_card, text="Storage Overview", font=ctk.CTkFont(weight="bold", size=16), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(15, 0))
        
        self.canvas = tk.Canvas(storage_card, width=150, height=150, bg=BG_CARD, highlightthickness=0)
        self.canvas.pack(side="left", padx=20, pady=15)
        
        stats_frame = ctk.CTkFrame(storage_card, fg_color="transparent")
        stats_frame.pack(side="left", padx=20, pady=20, fill="y")
        self.lbl_total_files = ctk.CTkLabel(stats_frame, text="● Total Files: 0", text_color=TEXT_MUTED)
        self.lbl_total_files.pack(anchor="w", pady=5)
        self.lbl_folder_size = ctk.CTkLabel(stats_frame, text="● Total Size: 0 MB", text_color=TEXT_MUTED)
        self.lbl_folder_size.pack(anchor="w", pady=5)
        
        # Target Folder Selection Card
        folder_card = ctk.CTkFrame(top_row, fg_color=BG_CARD, corner_radius=15)
        folder_card.pack(side="right", fill="both", expand=True, padx=(10, 0))
        ctk.CTkLabel(folder_card, text="Target Folder", font=ctk.CTkFont(weight="bold", size=16), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(15, 10))
        self.lbl_dash_folder = ctk.CTkLabel(folder_card, text="No folder selected", text_color=TEXT_MUTED, wraplength=300)
        self.lbl_dash_folder.pack(anchor="w", padx=20, pady=5)
        btn_sel = ctk.CTkButton(folder_card, text="Select Folder", command=self.select_folder, fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER)
        btn_sel.pack(anchor="w", padx=20, pady=15)
        
        # Middle Row (Quick Actions)
        mid_row = ctk.CTkFrame(frame, fg_color="transparent")
        mid_row.pack(fill="x", pady=20)
        ctk.CTkLabel(mid_row, text="Quick Actions", font=ctk.CTkFont(weight="bold", size=16), text_color=TEXT_MAIN).pack(anchor="w", pady=(0, 10))
        
        qa_container = ctk.CTkFrame(mid_row, fg_color="transparent")
        qa_container.pack(fill="x")
        
        def qa_btn(parent, text, command):
            b = ctk.CTkButton(parent, text=text, command=command, fg_color=BG_CARD, text_color=TEXT_MAIN, hover_color="#F9FAFB", height=80, corner_radius=15, font=ctk.CTkFont(size=14, weight="bold"))
            b.pack(side="left", fill="x", expand=True, padx=5)
            return b
            
        qa_btn(qa_container, "🧹 Smart Clean", lambda: self.handle_nav(self.show_cleaner, 2))
        qa_btn(qa_container, "🔄 Convert File", lambda: self.handle_nav(self.show_converter, 3))
        qa_btn(qa_container, "✨ AI Rename", lambda: self.handle_nav(self.show_converter, 3))
        qa_btn(qa_container, "👁️ Watchdog", lambda: self.handle_nav(self.show_monitor, 5))

        # Bottom Row (Recent Activities)
        bot_row = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        bot_row.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(bot_row, text="Recent Activities", font=ctk.CTkFont(weight="bold", size=16), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(15, 10))
        self.dash_log = ctk.CTkTextbox(bot_row, fg_color="transparent", text_color=TEXT_MUTED)
        self.dash_log.pack(fill="both", expand=True, padx=20, pady=(0,20))

    def create_cleaner(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.frames["cleaner"] = frame
        
        card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        card.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(card, text="Smart Cleaner", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_MAIN).pack(pady=30)
        ctk.CTkLabel(card, text="Free up space by finding and deleting junk files, duplicates, and large items.", text_color=TEXT_MUTED).pack()
        
        self.btn_run_clean = ctk.CTkButton(card, text="Scan Target Folder", height=45, fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, command=self.run_cleaner_scan)
        self.btn_run_clean.pack(pady=30)
        self.folder_btns.append({"btn": self.btn_run_clean, "color": ACCENT_PRIMARY, "txt_color": "#FFF"})
        self.btn_run_clean.configure(state="disabled")

    def create_converter(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.frames["converter"] = frame
        
        card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        card.pack(fill="both", expand=True, pady=10)
        
        tabview = ctk.CTkTabview(card, fg_color="transparent", text_color=TEXT_MAIN, segmented_button_selected_color=ACCENT_PRIMARY, segmented_button_selected_hover_color=ACCENT_HOVER)
        tabview.pack(fill="both", expand=True, padx=20, pady=10)
        
        tab_doc = tabview.add("📄 Document")
        tab_img = tabview.add("🖼 Image")
        tab_media = tabview.add("🎬 Media")
        tab_org = tabview.add("🗂 Organize")
        
        def add_tool(parent, title, desc, command, requires_folder=False, is_danger=False):
            f = ctk.CTkFrame(parent, fg_color="#F9FAFB", corner_radius=10)
            f.pack(fill="x", pady=10, padx=20)
            ctk.CTkLabel(f, text=title, font=ctk.CTkFont(weight="bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=15, pady=(15, 0))
            ctk.CTkLabel(f, text=desc, text_color=TEXT_MUTED).pack(anchor="w", padx=15, pady=(0, 15))
            b = ctk.CTkButton(f, text="Start", command=command, fg_color=ACCENT_PRIMARY if not is_danger else ACCENT_DANGER, hover_color=ACCENT_HOVER)
            b.pack(side="right", padx=15, pady=15)
            
            # Reposition button to top right instead of packing at bottom
            b.place(relx=1.0, rely=0.5, anchor="e", x=-15)
            
            if requires_folder:
                self.folder_btns.append({"btn": b, "color": ACCENT_PRIMARY, "txt_color": "#FFF"})
                b.configure(state="disabled")

        add_tool(tab_doc, "Word to PDF", "Convert .docx files to PDF formats quickly.", self.run_convert_pdf)
        add_tool(tab_img, "Convert to JPG", "Convert HEIC, WEBP, PNG to standard JPG.", self.run_convert_image)
        add_tool(tab_img, "Compress Image", "Reduce image size (files > 5MB).", lambda: self.run_async(None, self.converter.compress_image, filedialog.askopenfilename(), 5))
        add_tool(tab_media, "Extract Audio (MP3)", "Extract audio from MP4, MOV, MKV files.", self.run_extract_audio)
        add_tool(tab_org, "Smart Rename (AI)", "Let Gemini AI rename files based on image/PDF content.", self.run_smart_rename)
        add_tool(tab_org, "Sort by Extension", "Group files into folders by their type.", self.run_sort_extension, requires_folder=True)
        add_tool(tab_org, "Sort by Date", "Group files into Year/Month folders.", self.run_sort_date, requires_folder=True)

    def create_ai_chat(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.frames["ai"] = frame
        
        card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        card.pack(fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(card, text="AI Help Chat", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(20,10))
        
        self.chat_history = ctk.CTkTextbox(card, fg_color="#F9FAFB", text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14))
        self.chat_history.pack(fill="both", expand=True, padx=20, pady=10)
        
        bottom_frame = ctk.CTkFrame(card, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=20)
        
        self.chat_input = ctk.CTkEntry(bottom_frame, placeholder_text="Ask AI to find files, summarize docs, etc...", fg_color="#F9FAFB", text_color=TEXT_MAIN, height=45)
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.chat_input.bind("<Return>", lambda event: self.send_message())
        
        btn_send = ctk.CTkButton(bottom_frame, text="Send", command=self.send_message, fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, height=45, width=80)
        btn_send.pack(side="left")
        
        btn_clear = ctk.CTkButton(bottom_frame, text="Clear", command=self.clear_chat, fg_color="transparent", text_color=TEXT_MUTED, border_width=1, height=45, width=60)
        btn_clear.pack(side="left", padx=(10, 0))
        
        self.clear_chat()

    def create_monitor(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.frames["monitor"] = frame
        
        card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        card.pack(fill="x", pady=10)
        
        ctk.CTkLabel(card, text="Auto Monitor (Watchdog)", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(20,5))
        ctk.CTkLabel(card, text="Automatically organize files as they arrive in the target folder.", text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(0,20))
        
        self.switch_watch = ctk.CTkSwitch(card, text="Enable Auto Monitor for Target Folder", progress_color=ACCENT_PRIMARY, command=self.toggle_watch)
        self.switch_watch.pack(anchor="w", padx=20, pady=(0,20))
        
        log_card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        log_card.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(log_card, text="Activity Log", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(20,10))
        self.log_textbox = ctk.CTkTextbox(log_card, fg_color="#F9FAFB", text_color=TEXT_MAIN)
        self.log_textbox.pack(fill="both", expand=True, padx=20, pady=(0,20))

    def create_settings(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.frames["settings"] = frame
        
        card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        card.pack(fill="x", pady=10)
        
        ctk.CTkLabel(card, text="Settings", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(20, 20))
        
        ctk.CTkLabel(card, text="API Configuration", font=ctk.CTkFont(weight="bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20)
        if self.organizer.api_key:
            ctk.CTkLabel(card, text="✅ Gemini API Connected (Embedded)", text_color=ACCENT_SUCCESS).pack(anchor="w", padx=20, pady=5)
        else:
            ctk.CTkLabel(card, text="❌ Gemini API Key Not Found. Some AI features will not work.", text_color=ACCENT_DANGER).pack(anchor="w", padx=20, pady=5)
        
        ctk.CTkLabel(card, text="About ZipZap", font=ctk.CTkFont(weight="bold"), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(20,5))
        ctk.CTkLabel(card, text="Version: 1.0.0\nDeveloped with Python & CustomTkinter\nAI Engine: Google Gemini 1.5 Flash", text_color=TEXT_MUTED, justify="left").pack(anchor="w", padx=20, pady=(0,20))

    # ================= LOGIC METHODS =================

    def sync_excluded_folders(self):
        self.organizer.set_excluded_folders(self.config_data.get("excluded_folders", []))
        self.cleaner.set_excluded_folders(self.config_data.get("excluded_folders", []))

    def toggle_watch(self):
        if self.switch_watch.get() == 1:
            if not self.current_folder:
                messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกโฟลเดอร์เป้าหมายก่อนเปิดระบบอัตโนมัติ")
                self.switch_watch.deselect()
                return
            self.watcher_manager.start_watching(self.current_folder)
            self.log_action(f"✅ เริ่มเฝ้าระวังโฟลเดอร์: {self.current_folder}")
        else:
            self.watcher_manager.stop_watching()
            self.log_action("🛑 หยุดเฝ้าระวังโฟลเดอร์")

    def update_dashboard_stats(self):
        if not self.current_folder:
            return
            
        def count_files():
            try:
                num_files = sum(len(files) for _, _, files in os.walk(self.current_folder))
                size_bytes = sum(os.path.getsize(os.path.join(r, f)) for r, _, files in os.walk(self.current_folder) for f in files)
                size_mb = size_bytes / (1024 * 1024)
                
                self.after(0, lambda: self.lbl_total_files.configure(text=f"● Total Files: {num_files}"))
                self.after(0, lambda: self.lbl_folder_size.configure(text=f"● Total Size: {size_mb:.2f} MB"))
                self.after(0, self.draw_donut)
            except Exception as e:
                print("Error calculating stats", e)
        
        threading.Thread(target=count_files, daemon=True).start()
        
    def draw_donut(self):
        self.canvas.delete("all")
        # Draw a simple donut chart
        self.canvas.create_arc(10, 10, 140, 140, start=0, extent=240, fill=ACCENT_PRIMARY, outline="")
        self.canvas.create_arc(10, 10, 140, 140, start=240, extent=120, fill="#E5E7EB", outline="")
        # Inner circle
        self.canvas.create_oval(35, 35, 115, 115, fill=BG_CARD, outline="")
        self.canvas.create_text(75, 75, text="Storage", font=("Helvetica", 12, "bold"), fill=TEXT_MAIN)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = folder
            self.lbl_dash_folder.configure(text=folder)
            
            # Enable folder dependent buttons
            for b in self.folder_btns:
                b["btn"].configure(state="normal")
                
            self.update_dashboard_stats()

    def run_cleaner_scan(self):
        if not self.current_folder: return
        self.dash_log.insert("end", f"Scanning {self.current_folder} for junk...\n")
        messagebox.showinfo("Smart Cleaner", "Scan feature is currently a placeholder for future implementation.")

    def log_action(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {msg}\n"
        if hasattr(self, 'dash_log'):
            self.dash_log.insert("end", log_msg)
            self.dash_log.see("end")
        if hasattr(self, 'log_textbox'):
            self.log_textbox.insert("end", log_msg)
            self.log_textbox.see("end")

    def run_async(self, btn, func, *args):
        if btn:
            btn.configure(state="disabled")
        
        def task():
            try:
                func(*args)
                self.log_action(f"✅ Success: Action completed.")
            except Exception as e:
                self.log_action(f"❌ Error: {str(e)}")
            finally:
                if btn:
                    self.after(0, lambda: btn.configure(state="normal"))
        
        threading.Thread(target=task, daemon=True).start()

    def run_sort_extension(self):
        if self.current_folder: self.run_async(None, self.organizer.sort_by_extension, self.current_folder)

    def run_sort_date(self):
        if self.current_folder: self.run_async(None, self.organizer.sort_by_date, self.current_folder)

    def run_convert_image(self):
        file = filedialog.askopenfilename(filetypes=[("Image files", "*.heic *.webp *.png *.bmp")])
        if file: self.run_async(None, self.converter.convert_to_jpg, file)

    def run_convert_pdf(self):
        file = filedialog.askopenfilename(filetypes=[("Word Document", "*.docx")])
        if file: self.run_async(None, self.converter.convert_docx_to_pdf, file)

    def run_extract_audio(self):
        file = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv")])
        if file: self.run_async(None, self.converter.extract_audio, file)

    def run_smart_rename(self):
        files = filedialog.askopenfilenames(filetypes=[("Supported files", "*.jpg *.png *.jpeg *.webp *.heic *.pdf *.txt"), ("All files", "*.*")])
        if files:
            if not self.organizer.api_key:
                messagebox.showwarning("แจ้งเตือน", "ไม่พบ API Key ของ Gemini กรุณาแพ็คแอปใหม่พร้อมกับ API Key ครับ")
                return
                
            def batch_rename():
                success_count = 0
                for f in files:
                    try:
                        self.log_action(f"⏳ กำลังให้ AI วิเคราะห์ไฟล์: {os.path.basename(f)}...")
                        new_name = self.organizer.smart_rename_with_ai(f)
                        if new_name:
                            self.log_action(f"✅ เปลี่ยนชื่อสำเร็จ: {new_name}")
                            success_count += 1
                        else:
                            self.log_action(f"⚠️ ข้ามไฟล์ (AI คิดไม่ออก): {os.path.basename(f)}")
                    except Exception as e:
                        err_msg = str(e)
                        if "INVALID_ARGUMENT" in err_msg or "Cannot extract" in err_msg:
                            self.log_action(f"❌ ไฟล์เสียหรือไม่รองรับ: {os.path.basename(f)}")
                        else:
                            self.log_action(f"❌ เกิดข้อผิดพลาดกับไฟล์ {os.path.basename(f)}: {err_msg}")
                self.log_action(f"🎉 Smart Rename เสร็จสิ้น! เปลี่ยนไปได้ {success_count}/{len(files)} ไฟล์")

            threading.Thread(target=batch_rename, daemon=True).start()

    def clear_chat(self):
        if hasattr(self, 'chat_history'):
            self.chat_history.configure(state="normal")
            self.chat_history.delete("1.0", "end")
            self.chat_history.insert("end", "✧ AI: Hello! I am your smart assistant. Ask me anything about your files.\n\n")
            self.chat_history.configure(state="disabled")

    def send_message(self):
        user_msg = self.chat_input.get().strip()
        if not user_msg:
            return
            
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"👤 คุณ: {user_msg}\n\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")
        self.chat_input.delete(0, "end")
        
        def fetch_reply():
            try:
                reply = self.ai_assistant.ask_about_files(self.current_folder, user_msg)
            except Exception as e:
                reply = f"เกิดข้อผิดพลาด: {e}"
            self.after(0, lambda: self.append_ai_reply(reply))
            
        threading.Thread(target=fetch_reply, daemon=True).start()
        
    def append_ai_reply(self, reply):
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"✧ AI: {reply}\n\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")

if __name__ == "__main__":
    app = SmartFileManagerApp()
    app.mainloop()
