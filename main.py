import os
import json
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import math
import uuid
from datetime import datetime
from PIL import Image, ImageDraw, ImageTk, ImageFont
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_icon_image(icon_char, color, size=24):
    scale = 3
    img_size = size * scale
    img = Image.new("RGBA", (img_size, img_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    try:
        font_path = os.path.join(BASE_DIR, "assets", "MaterialIcons.ttf")
        font = ImageFont.truetype(font_path, int(size * scale * 0.9))
        bbox = draw.textbbox((0, 0), icon_char, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((img_size-w)/2 - bbox[0], (img_size-h)/2 - bbox[1]), icon_char, fill=color, font=font)
    except: pass
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    return ctk.CTkImage(light_image=img, size=(size, size))

def create_app_logo_image(size=40):
    scale = 4
    img_size = size * scale
    img = Image.new("RGBA", (img_size, img_size), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    radius = 10 * scale
    bg_color = ("#EDE9FE", "#4C1D95") # Light purple background
    icon_color = "#7C3AED" # Primary accent color
    draw.rounded_rectangle([0, 0, img_size, img_size], radius=radius, fill=bg_color)
    
    try:
        font_path = os.path.join(BASE_DIR, "assets", "MaterialIcons.ttf")
        font = ImageFont.truetype(font_path, int(size * scale * 0.6))
        icon_char = "\ue2c7" # folder
        bbox = draw.textbbox((0, 0), icon_char, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((img_size-w)/2 - bbox[0], (img_size-h)/2 - bbox[1]), icon_char, fill=icon_color, font=font)
    except: pass
    
    img = img.resize((size, size), Image.Resampling.LANCZOS)
    return ctk.CTkImage(light_image=img, size=(size, size))

# Import Core Modules (OOP)
from core.logger import ActionLogger
from core.converter import FileConverter
from core.organizer import FileOrganizer
from core.cleaner import StorageCleaner
from core.watcher import WatcherManager
from core.ai_assistant import AIAssistant

# Theme Colors (Modern Light/Purple)
BG_MAIN = ("#F3F5F9", "#0F172A")
BG_CARD = ("#FFFFFF", "#1E293B")
TEXT_MAIN = ("#1F2937", "#F8FAFC")
TEXT_MUTED = ("#6B7280", "#94A3B8")
ACCENT_PRIMARY = ("#7C3AED", "#8B5CF6") # Purple
ACCENT_HOVER = ("#6D28D9", "#7C3AED")
ACCENT_SUCCESS = ("#10B981", "#34D399")
ACCENT_WARNING = ("#F59E0B", "#FBBF24")
ACCENT_DANGER = ("#EF4444", "#F87171")
SIDEBAR_BG = ("#FFFFFF", "#1E293B")

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
        self.resizable(False, False)
        self.minsize(1000, 700)
        self.configure(fg_color=BG_MAIN)
        
        self.config_file = "config.json"
        self.config_data = self.load_config()
        self.current_folder = ""
        self.folder_btns = []
        
        # Converter State
        self.converter_files = []
        self.converter_mode = "Document"
        self.converter_target_format = ctk.StringVar(value=".pdf")
        self.converter_output_dir = ctk.StringVar(value="โฟลเดอร์เดียวกับต้นฉบับ")
        
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
        self.minsize(900, 600)
        
        try:
            from PIL import ImageTk
            icon_path = os.path.join(BASE_DIR, "assets", "icon.png")
            icon_img = ImageTk.PhotoImage(file=icon_path)
            self.iconphoto(False, icon_img)
        except Exception as e:
            print("Could not load app icon:", e)
            
        self.grid_columnconfigure(1, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=SIDEBAR_BG)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=20, pady=(20, 20), sticky="w")
        
        try:
            logo_path = os.path.join(BASE_DIR, "assets", "logo_transparent.png")
            logo_img = Image.open(logo_path).convert("RGBA")
            # Calculate height to keep aspect ratio for a width of ~180px
            w, h = logo_img.size
            new_w = 180
            new_h = int(h * (new_w / w))
            
            # Pre-scale for Retina (2x) using high-quality Lanczos to eliminate blurriness
            retina_w, retina_h = new_w * 2, new_h * 2
            logo_img = logo_img.resize((retina_w, retina_h), Image.Resampling.LANCZOS)
            
            self.logo_ctk = ctk.CTkImage(light_image=logo_img, size=(new_w, new_h))
            ctk.CTkLabel(logo_frame, image=self.logo_ctk, text="").pack(side="left")
        except Exception as e:
            ctk.CTkLabel(logo_frame, text="⚡ ZipZap", font=ctk.CTkFont(size=24, weight="bold"), text_color=ACCENT_PRIMARY).pack(side="left")

        # Nav Buttons
        self.nav_btns = []
        def create_nav_btn(text, row, command, icon_char):
            img_active = create_icon_image(icon_char, ACCENT_PRIMARY)
            img_inactive = create_icon_image(icon_char, TEXT_MUTED)
            btn = ctk.CTkButton(self.sidebar_frame, text=f"  {text}", image=img_inactive, command=lambda c=command, r=row: self.handle_nav(c, r), 
                                fg_color="transparent", text_color=TEXT_MUTED, hover_color=BG_MAIN, 
                                font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"), anchor="w", height=45)
            btn.grid(row=row, column=0, padx=15, pady=5, sticky="ew")
            btn._icon_active = img_active
            btn._icon_inactive = img_inactive
            self.nav_btns.append(btn)
            return btn

        self.btn_dashboard = create_nav_btn("Dashboard", 1, self.show_dashboard, "\ue871")
        self.btn_cleaner = create_nav_btn("Smart Cleaner", 2, self.show_cleaner, "\ue65f")
        self.btn_converter = create_nav_btn("Converter", 3, self.show_converter, "\uea18")
        self.btn_ai = create_nav_btn("AI Help Chat", 4, self.show_ai_chat, "\ue8f4")
        self.btn_monitor = create_nav_btn("Auto Monitor", 5, self.show_monitor, "\ue8b5")
        self.btn_settings = create_nav_btn("Settings", 6, self.show_settings, "\ue8b8")

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
        self.main_frame.pack_propagate(False)
        self.grid_propagate(False)

        # Top Bar (Header)
        self.topbar = ctk.CTkFrame(self.main_frame, height=60, fg_color=BG_CARD, corner_radius=0)
        self.topbar.pack(fill="x")
        self.lbl_page_title = ctk.CTkLabel(self.topbar, text="Dashboard", font=ctk.CTkFont(family="Helvetica", size=20, weight="bold"), text_color=TEXT_MAIN)
        self.lbl_page_title.pack(side="left", padx=30, pady=15)

        # Container for pages
        self.content_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_container.pack(fill="both", expand=True)
        self.content_container.pack_propagate(False)

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
                btn.configure(fg_color=("#EDE9FE", "#4C1D95"), text_color=ACCENT_PRIMARY, image=btn._icon_active)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED, image=btn._icon_inactive)
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
        
        self.lbl_donut = ctk.CTkLabel(storage_card, text="")
        self.lbl_donut.pack(side="left", padx=20, pady=15)
        
        stats_frame = ctk.CTkFrame(storage_card, fg_color="transparent")
        stats_frame.pack(side="left", padx=20, pady=20, fill="y", expand=True)
        
        # Legend
        def create_legend(parent, color, text):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.pack(anchor="w", pady=4)
            # Use a tiny colored frame as a dot
            dot = ctk.CTkFrame(f, width=12, height=12, fg_color=color, corner_radius=6)
            dot.pack(side="left", padx=(0, 10))
            lbl = ctk.CTkLabel(f, text=text, text_color=TEXT_MUTED, font=ctk.CTkFont(family="Helvetica", size=13))
            lbl.pack(side="left")
            return lbl
            
        self.lbl_leg_docs = create_legend(stats_frame, "#7C3AED", "เอกสาร (0 MB)")
        self.lbl_leg_media = create_legend(stats_frame, "#10B981", "มัลติมีเดีย (0 MB)")
        self.lbl_leg_others = create_legend(stats_frame, "#F472B6", "อื่นๆ (0 MB)")
        self.lbl_leg_free = create_legend(stats_frame, ("#E5E7EB", "#475569"), "พื้นที่ว่างบนดิสก์")
        
        # Target Folder Selection Card
        folder_card = ctk.CTkFrame(top_row, fg_color=BG_CARD, corner_radius=15)
        folder_card.pack(side="right", fill="both", expand=True, padx=(10, 0))
        ctk.CTkLabel(folder_card, text="Target Folder", font=ctk.CTkFont(weight="bold", size=16), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(15, 10))
        self.lbl_dash_folder = ctk.CTkLabel(folder_card, text="No folder selected", text_color=TEXT_MUTED, wraplength=300)
        self.lbl_dash_folder.pack(anchor="w", padx=20, pady=5)
        btn_sel = ctk.CTkButton(folder_card, text="Select Folder", command=self.select_folder, fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER)
        btn_sel.pack(anchor="w", padx=20, pady=15)
        
        self.draw_donut() # Draw initial empty donut
        
        # Middle Row (Quick Actions)
        mid_row = ctk.CTkFrame(frame, fg_color="transparent")
        mid_row.pack(fill="x", pady=20)
        ctk.CTkLabel(mid_row, text="Quick Actions", font=ctk.CTkFont(weight="bold", size=16), text_color=TEXT_MAIN).pack(anchor="w", pady=(0, 10))
        
        qa_container = ctk.CTkFrame(mid_row, fg_color="transparent")
        qa_container.pack(fill="x")
        
        def qa_btn(parent, text, command, icon_char, color):
            img = create_icon_image(icon_char, color, size=28)
            b = ctk.CTkButton(parent, text=f"  {text}", image=img, command=command, fg_color=BG_CARD, text_color=TEXT_MAIN, hover_color=("#F9FAFB", "#334155"), height=80, corner_radius=15, font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"))
            b.pack(side="left", fill="x", expand=True, padx=5)
            return b
            
        qa_btn(qa_container, "ทำความสะอาด", lambda: self.handle_nav(self.show_cleaner, 2), "\ue872", "#10B981")
        qa_btn(qa_container, "แปลงไฟล์", lambda: self.handle_nav(self.show_converter, 3), "\uea18", "#7C3AED")
        qa_btn(qa_container, "AI วิเคราะห์", lambda: self.handle_nav(self.show_ai_chat, 4), "\ue8f4", "#F472B6")
        qa_btn(qa_container, "เฝ้าระวัง", lambda: self.handle_nav(self.show_monitor, 5), "\ue8b5", "#F59E0B")

        # Bottom Row (Recent Activities)
        bot_row = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        bot_row.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(bot_row, text="Recent Activities", font=ctk.CTkFont(weight="bold", size=16), text_color=TEXT_MAIN).pack(anchor="w", padx=20, pady=(15, 10))
        self.dash_log = ctk.CTkTextbox(bot_row, fg_color="transparent", text_color=TEXT_MUTED)
        self.dash_log.pack(fill="both", expand=True, padx=20, pady=(0,20))

    def create_cleaner(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.frames["cleaner"] = frame
        
        # State variables
        self.clean_chk_temp = ctk.BooleanVar(value=True)
        self.clean_chk_dup = ctk.BooleanVar(value=True)
        self.clean_chk_large = ctk.BooleanVar(value=False)
        self.clean_scan_results = [] # Store file paths to delete
        
        # --- Options Card ---
        opt_card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        opt_card.pack(fill="x", pady=(0, 15))
        
        header_f = ctk.CTkFrame(opt_card, fg_color="transparent")
        header_f.pack(fill="x", padx=20, pady=(15, 10))
        ctk.CTkLabel(header_f, text=" / Smart Cleaner", font=ctk.CTkFont(size=16, weight="bold"), text_color=TEXT_MAIN).pack(side="left")
        ctk.CTkLabel(opt_card, text="สแกนหาไฟล์ขยะ ไฟล์ซ้ำซ้อน และไฟล์ขนาดใหญ่ที่ไม่ได้ใช้งาน เพื่อเคลียร์พื้นที่ว่างอย่างปลอดภัย", text_color=TEXT_MUTED).pack(anchor="w", padx=20, pady=(0, 15))
        
        def add_option(parent, var, title, desc, icon):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=20, pady=5)
            chk = ctk.CTkCheckBox(row, text="", variable=var, width=24, fg_color=ACCENT_PRIMARY)
            chk.pack(side="left")
            img = create_icon_image(icon, TEXT_MUTED, size=20)
            ctk.CTkLabel(row, image=img, text="").pack(side="left", padx=10)
            text_f = ctk.CTkFrame(row, fg_color="transparent")
            text_f.pack(side="left")
            ctk.CTkLabel(text_f, text=title, font=ctk.CTkFont(weight="bold"), text_color=TEXT_MAIN).pack(anchor="w")
            ctk.CTkLabel(text_f, text=desc, font=ctk.CTkFont(size=11), text_color=TEXT_MUTED).pack(anchor="w")
            # divider
            ctk.CTkFrame(parent, height=1, fg_color=("#F3F4F6", "#475569")).pack(fill="x", padx=20, pady=5)
            
        add_option(opt_card, self.clean_chk_temp, "Temporary Files", "ไฟล์ขยะของระบบ, Cache, Log Files", "\ue872")
        add_option(opt_card, self.clean_chk_dup, "Duplicate Files", "ไฟล์ที่ซ้ำซ้อนกันในหลายตำแหน่ง", "\ue14d")
        add_option(opt_card, self.clean_chk_large, "Large & Unused Files", "ไฟล์ขนาดใหญ่ที่ไม่ได้เปิดนานกว่า 30 วัน", "\ue2c7")
        
        # --- Target Folder ---
        folder_f = ctk.CTkFrame(opt_card, fg_color="transparent")
        folder_f.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(folder_f, text="โฟลเดอร์เป้าหมาย", font=ctk.CTkFont(weight="bold"), text_color=TEXT_MAIN).pack(anchor="w")
        
        input_f = ctk.CTkFrame(folder_f, fg_color="transparent")
        input_f.pack(fill="x", pady=(5, 10))
        self.clean_folder_entry = ctk.CTkEntry(input_f, text_color=TEXT_MAIN, fg_color=("#F9FAFB", "#334155"))
        self.clean_folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(input_f, text="เลือกโฟลเดอร์", fg_color=("#F3F4F6", "#475569"), text_color=TEXT_MAIN, hover_color=("#E5E7EB", "#475569"), command=self.select_folder).pack(side="right")
        
        self.btn_run_clean = ctk.CTkButton(opt_card, text="🔍 Scan Now", height=45, fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, command=self.run_cleaner_scan)
        self.btn_run_clean.pack(fill="x", padx=20, pady=(0, 20))
        
        # --- Results Card ---
        res_card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        res_card.pack(fill="both", expand=True)
        
        res_header = ctk.CTkFrame(res_card, fg_color="transparent")
        res_header.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(res_header, text="ผลการสแกน", font=ctk.CTkFont(weight="bold", size=16), text_color=TEXT_MAIN).pack(side="left")
        self.lbl_clean_summary = ctk.CTkLabel(res_header, text="พบ 0 ไฟล์ ขนาดรวม 0 MB", text_color=TEXT_MUTED)
        self.lbl_clean_summary.pack(side="right")
        
        self.clean_results_frame = ctk.CTkScrollableFrame(res_card, fg_color="transparent")
        self.clean_results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        bot_f = ctk.CTkFrame(res_card, fg_color="transparent")
        bot_f.pack(fill="x", padx=20, pady=15)
        self.lbl_clean_selected = ctk.CTkLabel(bot_f, text="เลือกแล้ว: 0 ไฟล์ (0 MB)", text_color=TEXT_MAIN, font=ctk.CTkFont(weight="bold"))
        self.lbl_clean_selected.pack(side="left")
        self.btn_cleanup = ctk.CTkButton(bot_f, text="🗑 Clean Up", fg_color="#EF4444", hover_color="#DC2626", command=self.run_cleaner_cleanup, state="disabled")
        self.btn_cleanup.pack(side="right")

    def create_converter(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.frames["converter"] = frame
        
        card = ctk.CTkFrame(frame, fg_color=BG_CARD, corner_radius=15)
        card.pack(fill="both", expand=True, pady=10)
        
        # Header & Badge
        header_frame = ctk.CTkFrame(card, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(header_frame, text="Universal Converter", font=ctk.CTkFont(size=18, weight="bold"), text_color=TEXT_MAIN).pack(side="left")
        badge = ctk.CTkFrame(header_frame, fg_color=("#EDE9FE", "#4C1D95"), corner_radius=10)
        badge.pack(side="right")
        ctk.CTkLabel(badge, text="ALL-IN-ONE", text_color=ACCENT_PRIMARY, font=ctk.CTkFont(size=11, weight="bold")).pack(padx=10, pady=2)
        
        # Tabs (Mode selector)
        self.converter_tab_var = ctk.StringVar(value="Document")
        tabs_frame = ctk.CTkFrame(card, fg_color="transparent")
        tabs_frame.pack(fill="x", padx=20, pady=10)
        
        seg_btn = ctk.CTkSegmentedButton(tabs_frame, values=["Document", "Image", "Media"], variable=self.converter_tab_var, command=self.on_converter_tab_change)
        seg_btn.pack(fill="x")
        
        # Drop Zone / Add Files Area
        self.drop_zone = ctk.CTkFrame(card, fg_color=("#F9FAFB", "#334155"), corner_radius=10, border_width=2, border_color=("#E5E7EB", "#475569"))
        self.drop_zone.pack(fill="x", padx=20, pady=10)
        
        dz_content = ctk.CTkFrame(self.drop_zone, fg_color="transparent")
        dz_content.pack(pady=30)
        
        img_doc = create_icon_image("\ue873", ("#D1D5DB", "#64748B"), size=40) # description icon
        ctk.CTkLabel(dz_content, image=img_doc, text="").pack()
        ctk.CTkLabel(dz_content, text="คลิก + Add Files เพื่อเพิ่มไฟล์ที่ต้องการแปลง", font=ctk.CTkFont(weight="bold"), text_color=TEXT_MAIN).pack(pady=(10, 0))
        ctk.CTkLabel(dz_content, text="รองรับ .docx, .jpg, .png, .mp4, etc.", text_color=TEXT_MUTED, font=ctk.CTkFont(size=12)).pack(pady=(0, 10))
        
        ctk.CTkButton(dz_content, text="+ Add Files", fg_color="transparent", border_width=1, border_color=TEXT_MUTED, text_color=TEXT_MAIN, hover_color=("#F3F4F6", "#475569"), command=self.add_converter_files).pack()
        
        # File List Area
        self.conv_list_frame = ctk.CTkScrollableFrame(card, fg_color="transparent")
        self.conv_list_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        # Bottom Controls
        bot_controls = ctk.CTkFrame(card, fg_color="transparent")
        bot_controls.pack(fill="x", padx=20, pady=(10, 20))
        
        # Format selection
        format_frame = ctk.CTkFrame(bot_controls, fg_color="transparent")
        format_frame.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(format_frame, text="รูปแบบไฟล์ปลายทาง", text_color=TEXT_MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w")
        self.conv_format_menu = ctk.CTkOptionMenu(format_frame, variable=self.converter_target_format, values=[".pdf"], fg_color=("#F9FAFB", "#334155"), text_color=TEXT_MAIN, button_color=("#F3F4F6", "#475569"), button_hover_color=("#E5E7EB", "#475569"))
        self.conv_format_menu.pack(fill="x", pady=(5, 0))
        
        # Output directory selection
        dir_frame = ctk.CTkFrame(bot_controls, fg_color="transparent")
        dir_frame.pack(side="left", fill="x", expand=True, padx=(10, 0))
        ctk.CTkLabel(dir_frame, text="บันทึกที่", text_color=TEXT_MUTED, font=ctk.CTkFont(size=12)).pack(anchor="w")
        
        dir_input_frame = ctk.CTkFrame(dir_frame, fg_color="transparent")
        dir_input_frame.pack(fill="x", pady=(5, 0))
        
        self.conv_dir_entry = ctk.CTkEntry(dir_input_frame, textvariable=self.converter_output_dir, fg_color=("#F9FAFB", "#334155"), text_color=TEXT_MAIN, state="disabled")
        self.conv_dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkButton(dir_input_frame, text="เลือก", width=60, fg_color="transparent", border_width=1, border_color=TEXT_MUTED, text_color=TEXT_MAIN, hover_color=("#F3F4F6", "#475569"), command=self.select_converter_output_dir).pack(side="right")
        
        # Start button
        self.btn_start_conversion = ctk.CTkButton(card, text="🔄 เริ่มแปลงไฟล์", fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, height=45, font=ctk.CTkFont(weight="bold", size=14), command=self.run_batch_conversion)
        self.btn_start_conversion.pack(fill="x", padx=20, pady=(0, 20))
        
        self.refresh_converter_list()

    def on_converter_tab_change(self, selected_tab):
        self.converter_mode = selected_tab
        self.converter_files = [] 
        if selected_tab == "Document":
            self.conv_format_menu.configure(values=[".pdf"])
            self.converter_target_format.set(".pdf")
        elif selected_tab == "Image":
            self.conv_format_menu.configure(values=[".jpg", ".png", "Compress (Keep format)"])
            self.converter_target_format.set(".jpg")
        elif selected_tab == "Media":
            self.conv_format_menu.configure(values=[".mp3"])
            self.converter_target_format.set(".mp3")
        self.refresh_converter_list()

    def select_converter_output_dir(self):
        folder = filedialog.askdirectory(title="เลือกโฟลเดอร์สำหรับบันทึกไฟล์")
        if folder:
            self.converter_output_dir.set(folder)

    def add_converter_files(self):
        filetypes = []
        if self.converter_mode == "Document":
            filetypes = [("Word Documents", "*.docx"), ("All Files", "*.*")]
        elif self.converter_mode == "Image":
            filetypes = [
                ("Image Files", "*.jpg *.jpeg *.png *.heic *.webp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("All Files", "*.*")
            ]
        elif self.converter_mode == "Media":
            filetypes = [
                ("Video Files", "*.mp4 *.mov *.mkv *.avi"),
                ("All Files", "*.*")
            ]
            
        try:
            files = filedialog.askopenfilenames(title="เลือกไฟล์ที่ต้องการแปลง", filetypes=filetypes)
            if files:
                for f in files:
                    if f not in self.converter_files:
                        self.converter_files.append(f)
                self.refresh_converter_list()
        except Exception as e:
            self.logger.log_action("ERROR", f"Failed to open file dialog: {e}")

    def remove_converter_file(self, file_path):
        if file_path in self.converter_files:
            self.converter_files.remove(file_path)
            self.refresh_converter_list()

    def refresh_converter_list(self):
        for widget in self.conv_list_frame.winfo_children():
            widget.destroy()
            
        if not self.converter_files:
            self.btn_start_conversion.configure(state="disabled")
            return
            
        self.btn_start_conversion.configure(state="normal")
        target_fmt = self.converter_target_format.get()
        if target_fmt == "Compress (Keep format)":
            target_fmt = "⬇️ Compress"
            
        for f in self.converter_files:
            row = ctk.CTkFrame(self.conv_list_frame, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=("#E5E7EB", "#475569"))
            row.pack(fill="x", pady=5)
            
            # Pack X button FIRST so it is on the far right
            btn_rm = ctk.CTkButton(row, text="✕", width=30, height=30, fg_color="transparent", hover_color=("#FEE2E2", "#7F1D1D"), text_color="#EF4444", command=lambda path=f: self.remove_converter_file(path))
            btn_rm.pack(side="right", padx=(0, 10))
            
            # Then pack target format pill
            target_frame = ctk.CTkFrame(row, fg_color=BG_CARD)
            target_frame.pack(side="right", padx=15)
            
            ctk.CTkLabel(target_frame, text="➔", text_color=("#9CA3AF", "#64748B")).pack(side="left", padx=10)
            
            pill = ctk.CTkFrame(target_frame, fg_color=("#DBEAFE", "#1E3A8A"), corner_radius=10)
            pill.pack(side="left")
            ctk.CTkLabel(pill, text=target_fmt, text_color=("#1D4ED8", "#93C5FD"), font=ctk.CTkFont(size=12, weight="bold")).pack(padx=10, pady=2)
            
            # Icon
            icon_char = "\ue873" if self.converter_mode == "Document" else "\ue3f4" if self.converter_mode == "Image" else "\ue04a"
            img = create_icon_image(icon_char, ("#D1D5DB", "#64748B"), size=24)
            ctk.CTkLabel(row, image=img, text="").pack(side="left", padx=15, pady=10)
            
            # File info
            info_frame = ctk.CTkFrame(row, fg_color=BG_CARD)
            info_frame.pack(side="left", fill="x", expand=True)
            
            fname = os.path.basename(f)
            size_mb = os.path.getsize(f) / (1024 * 1024)
            ctk.CTkLabel(info_frame, text=fname, font=ctk.CTkFont(weight="bold", size=13), text_color=TEXT_MAIN).pack(anchor="w", pady=(5, 0))
            ctk.CTkLabel(info_frame, text=f"{size_mb:.1f} MB", text_color=TEXT_MUTED, font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(0, 5))

    def run_batch_conversion(self):
        if not self.converter_files:
            return
            
        out_dir = self.converter_output_dir.get()
        if out_dir == "โฟลเดอร์เดียวกับต้นฉบับ":
            out_dir = None
            
        mode = self.converter_mode
        target_fmt = self.converter_target_format.get()
        files = list(self.converter_files)
        
        def process_conversion():
            success_count = 0
            for file_path in files:
                self.log_action(f"⏳ กำลังแปลงไฟล์: {os.path.basename(file_path)}")
                try:
                    if mode == "Document":
                        success, res = self.converter.convert_docx_to_pdf(file_path, output_dir=out_dir)
                    elif mode == "Image":
                        if target_fmt == "Compress (Keep format)":
                            success, res = self.converter.compress_image(file_path, max_size_mb=5, output_dir=out_dir)
                        else:
                            fmt_map = {".jpg": "JPEG", ".png": "PNG"}
                            success, res = self.converter.convert_image(file_path, output_format=fmt_map.get(target_fmt, "JPEG"), output_dir=out_dir)
                    elif mode == "Media":
                        success, res = self.converter.extract_audio(file_path, output_dir=out_dir)
                    
                    if success:
                        self.log_action(f"✅ สำเร็จ: {res}")
                        success_count += 1
                    else:
                        self.log_action(f"❌ ผิดพลาด: {res}")
                except Exception as e:
                    self.log_action(f"❌ เกิดข้อผิดพลาดกับไฟล์ {os.path.basename(file_path)}: {str(e)}")
            
            self.log_action(f"🎉 แปลงไฟล์เสร็จสิ้น! ทำสำเร็จ {success_count}/{len(files)} ไฟล์")
            self.after(0, self.converter_files.clear)
            self.after(0, self.refresh_converter_list)
            
        self.btn_start_conversion.configure(state="disabled")
        threading.Thread(target=process_conversion, daemon=True).start()

    def create_ai_chat(self):
        frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        self.frames["ai"] = frame
        
        # Full width scrolling area for chat
        self.chat_history_frame = ctk.CTkScrollableFrame(frame, fg_color="transparent")
        self.chat_history_frame.pack(fill="both", expand=True)
        
        # Bottom input area (like ChatGPT)
        bottom_area = ctk.CTkFrame(frame, fg_color="transparent")
        bottom_area.pack(fill="x", side="bottom")
        
        input_container = ctk.CTkFrame(bottom_area, fg_color="transparent")
        input_container.pack(fill="x", padx=40, pady=20)
        
        self.chat_input = ctk.CTkEntry(input_container, placeholder_text="Ask ZipZap AI about your files...", fg_color=BG_CARD, text_color=TEXT_MAIN, height=50, corner_radius=25)
        self.chat_input.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.chat_input.bind("<Return>", lambda event: self.send_message())
        
        # Send button (circular with icon)
        send_icon = create_icon_image("\ue163", "#FFFFFF", size=20)
        btn_send = ctk.CTkButton(input_container, text="", image=send_icon, command=self.send_message, fg_color=ACCENT_PRIMARY, hover_color=ACCENT_HOVER, width=50, height=50, corner_radius=25)
        btn_send.pack(side="left")
        
        btn_clear = ctk.CTkButton(input_container, text="Clear", command=self.clear_chat, fg_color="transparent", text_color=TEXT_MUTED, hover_color=("#E5E7EB", "#475569"), width=60, height=50, corner_radius=25)
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
        self.log_textbox = ctk.CTkTextbox(log_card, fg_color=("#F9FAFB", "#334155"), text_color=TEXT_MAIN)
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
        ex = self.config_data.get("excluded_folders", [])
        self.organizer.excluded_folders = ex
        self.cleaner.excluded_folders = ex
        self.watcher_manager.excluded_folders = ex

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
                import shutil
                num_files = 0
                size_docs = 0
                size_media = 0
                size_others = 0
                
                for r, _, files in os.walk(self.current_folder):
                    for f in files:
                        num_files += 1
                        try:
                            f_size = os.path.getsize(os.path.join(r, f))
                        except: f_size = 0
                        
                        ext = f.lower().split('.')[-1] if '.' in f else ''
                        if ext in ['pdf', 'doc', 'docx', 'txt', 'xlsx', 'csv', 'pptx']:
                            size_docs += f_size
                        elif ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'heic', 'bmp', 'mp4', 'mov', 'avi', 'mkv', 'mp3', 'wav']:
                            size_media += f_size
                        else:
                            size_others += f_size

                total_folder_size = size_docs + size_media + size_others
                
                # Get Disk Usage for Free Space
                try:
                    total, used, free = shutil.disk_usage(self.current_folder)
                    free_gb = free / (1024**3)
                    self.after(0, lambda: self.lbl_leg_free.configure(text=f"พื้นที่ว่างดิสก์ ({free_gb:.1f} GB)"))
                except:
                    pass

                self.after(0, lambda: self.lbl_leg_docs.configure(text=f"เอกสาร ({size_docs/(1024*1024):.1f} MB)"))
                self.after(0, lambda: self.lbl_leg_media.configure(text=f"มัลติมีเดีย ({size_media/(1024*1024):.1f} MB)"))
                self.after(0, lambda: self.lbl_leg_others.configure(text=f"อื่นๆ ({size_others/(1024*1024):.1f} MB)"))
                
                if total_folder_size > 0:
                    data = [
                        (size_docs/total_folder_size*100, "#7C3AED"),   # Purple
                        (size_media/total_folder_size*100, "#10B981"), # Teal
                        (size_others/total_folder_size*100, "#F472B6"),  # Pink
                    ]
                else:
                    data = None
                    
                total_mb = total_folder_size / (1024 * 1024)
                
                self.after(0, lambda: self.draw_donut(data, total_mb))
            except Exception as e:
                print("Error calculating stats", e)
        
        threading.Thread(target=count_files, daemon=True).start()
        
    def draw_donut(self, data=None, total_mb=0):
        size = 150
        scale = 4
        img_size = size * scale
        img = Image.new("RGBA", (img_size, img_size), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        thickness = 18 * scale
        bbox = [thickness/2, thickness/2, img_size - thickness/2, img_size - thickness/2]
        
        if not data:
            data = [(100, ("#E5E7EB", "#475569"))]
            
        start_angle = -90
        mode = ctk.get_appearance_mode()
        for percentage, color in data:
            if percentage <= 0: continue
            extent = (percentage / 100) * 360
            end_angle = start_angle + extent
            
            # Resolve color for PIL (which doesn't understand light/dark tuples)
            if isinstance(color, tuple):
                resolved_color = color[1] if mode == "Dark" else color[0]
            else:
                resolved_color = color
                
            draw.arc(bbox, start=start_angle, end=end_angle, fill=resolved_color, width=int(thickness))
            start_angle = end_angle

        # Resize and create CTkImage
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        ctk_img = ctk.CTkImage(light_image=img, size=(size, size))
        
        # Format the center text like the mockup
        if total_mb >= 1024:
            val_text = f"{total_mb/1024:.1f} GB"
        else:
            val_text = f"{total_mb:.1f} MB" if total_mb > 0 else "0%"
            
        # We can't do two different fonts in one CTkLabel easily, so we'll just put it in two lines
        center_text = f"{val_text}\nUSED"
        
        self.lbl_donut.configure(image=ctk_img, text=center_text, text_color=ACCENT_PRIMARY, compound="center", font=ctk.CTkFont(family="Helvetica", size=18, weight="bold"))
        self.lbl_donut.image = ctk_img

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = folder
            self.lbl_dash_folder.configure(text=folder)
            
            if hasattr(self, 'clean_folder_entry'):
                self.clean_folder_entry.delete(0, 'end')
                self.clean_folder_entry.insert(0, folder)
                
            # Enable folder dependent buttons
            for b in self.folder_btns:
                b["btn"].configure(state="normal")
                
            self.update_dashboard_stats()

    def run_cleaner_scan(self):
        folder = self.clean_folder_entry.get() if hasattr(self, 'clean_folder_entry') else self.current_folder
        if not folder or not os.path.exists(folder):
            messagebox.showerror("Error", "โปรดเลือกโฟลเดอร์ที่ถูกต้องก่อนสแกน")
            return
            
        self.btn_run_clean.configure(state="disabled", text="Scanning...")
        
        # Clear old results
        for widget in self.clean_results_frame.winfo_children():
            widget.destroy()
            
        def _scan_task():
            results = []
            if self.clean_chk_dup.get():
                results.extend(self.cleaner.scan_duplicates(folder))
            if self.clean_chk_temp.get():
                results.extend(self.cleaner.scan_junk(folder))
            if self.clean_chk_large.get():
                results.extend(self.cleaner.scan_large_files(folder))
                
            self.after(0, lambda: self.show_clean_results(results))
            self.after(0, lambda: self.btn_run_clean.configure(state="normal", text="🔍 Scan Now"))

        threading.Thread(target=_scan_task, daemon=True).start()
        
    def show_clean_results(self, results):
        self.clean_scan_results = results
        total_size = sum(f["size"] for f in results)
        mb = total_size / (1024 * 1024)
        gb = mb / 1024
        size_str = f"{gb:.2f} GB" if gb >= 1 else f"{mb:.2f} MB"
        self.lbl_clean_summary.configure(text=f"พบ {len(results)} ไฟล์ ขนาดรวม {size_str}")
        self.lbl_clean_selected.configure(text=f"เลือกแล้ว: {len(results)} ไฟล์ ({size_str})")
        
        if results:
            self.btn_cleanup.configure(state="normal", text=f"🗑 Clean Up — ได้พื้นที่คืน {size_str}")
        else:
            self.btn_cleanup.configure(state="disabled", text="🗑 Clean Up")
            ctk.CTkLabel(self.clean_results_frame, text="ไม่พบไฟล์ขยะหรือไฟล์ซ้ำในโฟลเดอร์นี้", text_color=TEXT_MUTED).pack(pady=30)
            
        grouped = {"junk": [], "duplicate": [], "large": []}
        for r in results: grouped[r["type"]].append(r)
        
        def render_group(title, key, icon):
            items = grouped[key]
            if not items: return
            group_f = ctk.CTkFrame(self.clean_results_frame, fg_color=("#F9FAFB", "#334155"), corner_radius=8)
            group_f.pack(fill="x", pady=(0, 10))
            
            header = ctk.CTkFrame(group_f, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=8)
            img = create_icon_image(icon, TEXT_MUTED, size=16)
            ctk.CTkLabel(header, image=img, text="").pack(side="left")
            ctk.CTkLabel(header, text=f" {title} ({len(items)})", font=ctk.CTkFont(weight="bold"), text_color=TEXT_MAIN).pack(side="left")
            
            group_size = sum(i["size"] for i in items) / (1024*1024)
            ctk.CTkLabel(header, text=f"{group_size:.1f} MB", font=ctk.CTkFont(weight="bold"), text_color=ACCENT_PRIMARY).pack(side="right")
            
            for item in items[:30]:  # Limit UI rendering
                row = ctk.CTkFrame(group_f, fg_color="transparent")
                row.pack(fill="x", padx=30, pady=2)
                chk = ctk.CTkCheckBox(row, text="", width=20, fg_color=ACCENT_PRIMARY)
                chk.select()
                chk.pack(side="left")
                filename = os.path.basename(item["path"])
                ctk.CTkLabel(row, text=filename, text_color=TEXT_MAIN).pack(side="left")
                sz = item["size"] / (1024*1024)
                ctk.CTkLabel(row, text=f"{sz:.1f} MB", text_color=TEXT_MUTED).pack(side="right")
            if len(items) > 30:
                ctk.CTkLabel(group_f, text=f"... และอีก {len(items)-30} ไฟล์", text_color=TEXT_MUTED).pack(pady=2)

        render_group("Temporary Files", "junk", "\ue872")
        render_group("Duplicate Files", "duplicate", "\ue14d")
        render_group("Large & Unused", "large", "\ue2c7")

    def run_cleaner_cleanup(self):
        if not self.clean_scan_results: return
        paths = [f["path"] for f in self.clean_scan_results]
        
        self.btn_cleanup.configure(state="disabled", text="Cleaning...")
        
        def _task():
            count, saved_mb = self.cleaner.clean_files(paths)
            self.after(0, lambda: messagebox.showinfo("Smart Cleaner", f"ทำความสะอาดเรียบร้อย!\nลบไฟล์ {count} ไฟล์\nได้พื้นที่คืนมา {saved_mb:.2f} MB"))
            self.after(0, self.update_dashboard_stats)
            self.after(0, self.run_cleaner_scan) # Rescan to refresh UI

        threading.Thread(target=_task, daemon=True).start()

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

    def add_chat_bubble(self, text, is_user=False):
        # Use transparent backgrounds for a modern, clean look (like Gemini)
        row = ctk.CTkFrame(self.chat_history_frame, fg_color="transparent")
        row.pack(fill="x", pady=15)
        
        content = ctk.CTkFrame(row, fg_color="transparent")
        content.pack(fill="x", padx=40)
        
        # Avatar (Left aligned for both)
        if is_user:
            avatar_frame = ctk.CTkFrame(content, width=36, height=36, corner_radius=18, fg_color=ACCENT_PRIMARY)
            avatar_frame.pack(side="left", anchor="n", padx=(0, 20))
            avatar_frame.pack_propagate(False)
            icon_code = "\ue7fd" # Person icon
            img = create_icon_image(icon_code, "#FFFFFF", size=20)
            ctk.CTkLabel(avatar_frame, image=img, text="").pack(expand=True)
        else:
            avatar_frame = ctk.CTkFrame(content, width=36, height=36, corner_radius=18, fg_color="#10B981")
            avatar_frame.pack(side="left", anchor="n", padx=(0, 20))
            avatar_frame.pack_propagate(False)
            
            icon_code = "\ue6dd" # Crisp sparkle icon
            img = create_icon_image(icon_code, "#FFFFFF", size=20)
            ctk.CTkLabel(avatar_frame, image=img, text="").pack(expand=True)
        
        # Text Content area
        text_frame = ctk.CTkFrame(content, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)
        
        name = "คุณ" if is_user else "ZipZap AI"
        ctk.CTkLabel(text_frame, text=name, font=ctk.CTkFont(weight="bold", size=15), text_color=TEXT_MAIN).pack(anchor="w", pady=(0, 5))
        
        lbl = ctk.CTkLabel(text_frame, text=text, text_color=TEXT_MAIN, font=ctk.CTkFont(size=14), wraplength=700, justify="left")
        lbl.pack(anchor="w")
        
        self.after(50, lambda: self.chat_history_frame._parent_canvas.yview_moveto(1.0))

    def clear_chat(self):
        if hasattr(self, 'chat_history_frame'):
            for widget in self.chat_history_frame.winfo_children():
                widget.destroy()
            
            # Show a clean, text-only welcome banner
            banner_frame = ctk.CTkFrame(self.chat_history_frame, fg_color="transparent")
            banner_frame.pack(fill="x", pady=(80, 10))
            
            # Icon in the center (crisp font icon)
            icon_frame = ctk.CTkFrame(banner_frame, fg_color="transparent")
            icon_frame.pack()
            img = create_icon_image("\ue6dd", TEXT_MAIN, size=48)
            ctk.CTkLabel(icon_frame, image=img, text="").pack(pady=(0, 10))
            
            ctk.CTkLabel(banner_frame, text="How can I help you today?", font=ctk.CTkFont(size=28, weight="bold"), text_color=TEXT_MAIN).pack(pady=(10, 5))
            ctk.CTkLabel(banner_frame, text="Ask me to find files, explain documents, or organize your storage.", font=ctk.CTkFont(size=16), text_color=TEXT_MUTED).pack()

    def send_message(self):
        user_msg = self.chat_input.get().strip()
        if not user_msg:
            return
            
        self.add_chat_bubble(user_msg, is_user=True)
        self.chat_input.delete(0, "end")
        
        def fetch_reply():
            try:
                reply = self.ai_assistant.ask_ai(self.current_folder, user_msg)
            except Exception as e:
                reply = f"เกิดข้อผิดพลาด: {e}"
            self.after(0, lambda: self.add_chat_bubble(reply, is_user=False))
            
        threading.Thread(target=fetch_reply, daemon=True).start()

if __name__ == "__main__":
    app = SmartFileManagerApp()
    app.mainloop()
