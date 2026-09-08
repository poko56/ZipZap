import os
import sys
import json
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import re
import subprocess
import uuid

# Import Core Modules (OOP)
from core.logger import ActionLogger
from core.converter import FileConverter
from core.organizer import FileOrganizer
from core.cleaner import StorageCleaner
from core.watcher import WatcherManager
from core.ai_assistant import AIAssistant

# Theme Colors (Minimalist Grayscale)
BG_MAIN = "#FAFAFA"
BG_CARD = "#FFFFFF"
TEXT_MAIN = "#111827"
ACCENT_ORANGE = "#374151" # Reusing variable name to avoid global rename
ACCENT_HOVER = "#1F2937"
ACCENT_RED = "#E53E3E"
ACCENT_RED_HOVER = "#C53030"

ctk.set_appearance_mode("Light")



class SmartFileManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ระบบจัดการไฟล์อัจฉริยะ (Smart File Manager)")
        self.geometry("960x680")
        self.minsize(900, 650)
        self.configure(fg_color=BG_MAIN)
        
        self.config_file = "config.json"
        self.config_data = self.load_config()
        self.current_folder = ""
        self.folder_btns = []
        
        # Instantiate OOP Core Managers
        self.logger = ActionLogger()
        self.converter = FileConverter(self.logger)
        self.organizer = FileOrganizer(self.logger, self.config_data.get("gemini_api_key", ""))
        self.cleaner = StorageCleaner(self.logger)
        self.watcher_manager = WatcherManager(self.logger)
        self.ai_assistant = AIAssistant(self.config_data.get("gemini_api_key", ""))
        self.sync_excluded_folders()

        self.setup_ui()

    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f)
            except: pass
        return {"watch_folder": "", "gemini_api_key": ""}

    def save_config(self, key, value):
        self.config_data[key] = value
        with open(self.config_file, "w") as f:
            json.dump(self.config_data, f, indent=4)
        
        # Update API Keys
        if key == "gemini_api_key":
            self.organizer.api_key = value
            self.ai_assistant.api_key = value

    def setup_ui(self):
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=BG_CARD)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="✦ SmartMF", font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"), text_color=ACCENT_ORANGE)
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 20))

        def create_nav_btn(text, row, command):
            btn = ctk.CTkButton(self.sidebar_frame, text=text, command=command, fg_color="transparent", text_color=TEXT_MAIN, hover_color=BG_MAIN, font=ctk.CTkFont(family="Helvetica", size=16, weight="bold"), anchor="w", height=40)
            btn.grid(row=row, column=0, padx=20, pady=5, sticky="ew")
            return btn

        self.btn_dashboard = create_nav_btn("⌨  แผงควบคุมหลัก", 1, self.show_dashboard)
        self.btn_ai = create_nav_btn("✧  ผู้ช่วย AI", 2, self.show_ai_chat)
        self.btn_logs = create_nav_btn("📄  ประวัติการใช้งาน", 3, self.show_logs)
        self.btn_settings = create_nav_btn("⚙  ตั้งค่าระบบ", 4, self.show_settings)

        self.btn_dashboard.configure(fg_color=BG_MAIN, text_color=ACCENT_ORANGE)

        # Main View Frame
        self.main_frame = ctk.CTkFrame(self, fg_color=BG_MAIN, corner_radius=0)
        self.main_frame.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")

        self.create_dashboard()
        self.create_ai_chat()
        self.create_logs()
        self.create_settings()
        
        self.show_dashboard()

    def hide_all_frames(self):
        self.frame_dashboard.pack_forget()
        self.frame_ai.pack_forget()
        self.frame_logs.pack_forget()
        self.frame_settings.pack_forget()
        for btn in [self.btn_dashboard, self.btn_ai, self.btn_logs, self.btn_settings]:
            btn.configure(fg_color="transparent", text_color=TEXT_MAIN)

    def show_dashboard(self):
        self.hide_all_frames()
        self.btn_dashboard.configure(fg_color=BG_MAIN, text_color=ACCENT_ORANGE)
        self.frame_dashboard.pack(fill="both", expand=True, padx=30, pady=30)

    def show_ai_chat(self):
        self.hide_all_frames()
        self.btn_ai.configure(fg_color=BG_MAIN, text_color=ACCENT_ORANGE)
        self.frame_ai.pack(fill="both", expand=True, padx=30, pady=30)

    def show_logs(self):
        self.hide_all_frames()
        self.btn_logs.configure(fg_color=BG_MAIN, text_color=ACCENT_ORANGE)
        self.frame_logs.pack(fill="both", expand=True, padx=30, pady=30)
        self.refresh_logs()

    def show_settings(self):
        self.hide_all_frames()
        self.btn_settings.configure(fg_color=BG_MAIN, text_color=ACCENT_ORANGE)
        self.frame_settings.pack(fill="both", expand=True, padx=30, pady=30)

    def create_dashboard(self):
        self.frame_dashboard = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        # Header (Target Folder & Watcher)
        header = ctk.CTkFrame(self.frame_dashboard, fg_color=BG_CARD, corner_radius=15)
        header.pack(fill="x", pady=(0, 20), ipady=10)
        
        folder_disp = self.current_folder if self.current_folder else "ยังไม่ได้เลือก"
        self.lbl_folder = ctk.CTkLabel(header, text=f"📂 โฟลเดอร์ปัจจุบัน: {folder_disp}", font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"), text_color=TEXT_MAIN)
        self.lbl_folder.pack(side="left", padx=20, pady=10)
        self.lbl_stats = ctk.CTkLabel(header, text="", font=ctk.CTkFont(family="Helvetica", size=13), text_color="#6B7280")
        self.lbl_stats.pack(side="left", padx=10, pady=10)
        
        btn_select_folder = ctk.CTkButton(header, text="เลือกโฟลเดอร์...", width=100, fg_color=ACCENT_ORANGE, hover_color=ACCENT_HOVER, font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"), command=self.select_folder)
        btn_select_folder.pack(side="left", padx=10, pady=10)
        
        self.switch_watch = ctk.CTkSwitch(header, text="เปิดระบบอัตโนมัติ (Auto Monitor)", progress_color=ACCENT_ORANGE, text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"), command=self.toggle_watch)
        self.switch_watch.pack(side="right", padx=20, pady=10)

        # TabView for Tools
        self.tabview = ctk.CTkTabview(self.frame_dashboard, 
                                      fg_color="transparent",
                                      segmented_button_fg_color="#E5E7EB",
                                      segmented_button_selected_color="#FFFFFF",
                                      segmented_button_unselected_color="#E5E7EB",
                                      segmented_button_unselected_hover_color="#D1D5DB",
                                      text_color="#111827")
        self.tabview.pack(fill="both", expand=True)
        
        tab_conv = self.tabview.add("🔄 แปลงไฟล์")
        tab_org = self.tabview.add("🗂 จัดระเบียบ")
        tab_clean = self.tabview.add("🧹 ทำความสะอาด")

        def create_tool_btn(parent, text, tooltip_text, command, is_danger=False, require_folder=False, options=None, default_opt=None):
            frame = ctk.CTkFrame(parent, fg_color="transparent")
            frame.pack(pady=10, padx=20, fill="x")
            
            color = ACCENT_RED if is_danger else BG_CARD
            hover = ACCENT_RED_HOVER if is_danger else "#E5E7EB"
            txt_color = "#FFF" if is_danger else TEXT_MAIN
            
            if options:
                opt_var = ctk.StringVar(value=default_opt[0] if default_opt else options[0][0])
                opt_menu = ctk.CTkOptionMenu(frame, values=[o[0] for o in options], variable=opt_var, width=130, height=45, fg_color=BG_MAIN, text_color=TEXT_MAIN, button_color=ACCENT_ORANGE, button_hover_color=ACCENT_HOVER, font=ctk.CTkFont(family="Helvetica", size=13))
                opt_menu.pack(side="right", padx=(10, 0))
                
                val_map = {o[0]: o[1] for o in options}
                btn = ctk.CTkButton(frame, text=text, command=None,
                                    fg_color=color, text_color=txt_color, hover_color=hover,
                                    font=ctk.CTkFont(family="Helvetica", size=15), height=45, anchor="w" if not is_danger else "center")
                btn.configure(command=lambda b=btn, ov=opt_var, vm=val_map: command(b, vm[ov.get()]))
                btn.pack(side="left", fill="x", expand=True)
            else:
                btn = ctk.CTkButton(frame, text=text, command=None,
                                    fg_color=color, text_color=txt_color, hover_color=hover,
                                    font=ctk.CTkFont(family="Helvetica", size=15), height=45, anchor="w" if not is_danger else "center")
                # Handle old command signature
                if command.__code__.co_argcount > 1:
                    btn.configure(command=lambda b=btn: command(b))
                else:
                    btn.configure(command=command)
                btn.pack(side="left", fill="x", expand=True)
                
            if require_folder:
                btn.configure(state="disabled", fg_color="#F3F4F6", text_color="#9CA3AF")
                self.folder_btns.append({"btn": btn, "color": color, "txt_color": txt_color})
            return btn

        # 1. Conversion Tab
        create_tool_btn(tab_conv, "🖼  แปลงรูปภาพให้เป็น JPG", "แปลงไฟล์รูปภาพนามสกุลแปลกๆ ให้เป็น .jpg เพื่อให้เอาไปใช้ต่อได้ง่าย", self.run_convert_image)
        create_tool_btn(tab_conv, "📄  แปลงไฟล์ Word เป็น PDF", "คลิกเพื่อเลือกไฟล์ .docx และโปรแกรมจะเซฟเป็น .pdf ให้อัตโนมัติ", self.run_convert_pdf)
        create_tool_btn(tab_conv, "🎵  ดึงเสียงออกจากวิดีโอ (บันทึกเป็น MP3)", "สกัดเอาแต่เสียงพูดจากวิดีโอ และเซฟเป็นไฟล์ .mp3", self.run_extract_audio)
        create_tool_btn(tab_conv, "🗜  บีบอัดขนาดรูปภาพ", "ลดขนาดภาพที่ใหญ่เกิน 5MB ให้เล็กลง เพื่อประหยัดพื้นที่เก็บข้อมูล", self.run_compress_image, options=[("ถ้าเกิน 1MB", 1), ("ถ้าเกิน 5MB", 5), ("ถ้าเกิน 10MB", 10)], default_opt=("ถ้าเกิน 5MB", 5))

        # 2. Organizer Tab
        create_tool_btn(tab_org, "📋  จัดกลุ่มไฟล์ตามประเภท (รูป, วิดีโอ, เอกสาร)", "ระบบจะย้ายไฟล์ในโฟลเดอร์เป้าหมายไปจัดกลุ่มให้เป็นหมวดหมู่ (เช่นโฟลเดอร์ Images, Videos)", self.run_sort_extension, require_folder=True)
        create_tool_btn(tab_org, "📅  จัดกลุ่มไฟล์ตามเดือนและปีที่สร้าง", "ย้ายไฟล์ทั้งหมดเข้าโฟลเดอร์ที่แบ่งตาม ปีและเดือนที่สร้างไฟล์ เหมาะสำหรับรูปถ่าย", self.run_sort_date, require_folder=True)
        
        btn_smart = ctk.CTkButton(tab_org, text="✧  ให้ AI ช่วยตั้งชื่อไฟล์ให้ใหม่ (Smart Rename)", command=None,
                                  fg_color=ACCENT_ORANGE, text_color="#FFF", hover_color=ACCENT_HOVER,
                                  font=ctk.CTkFont(family="Helvetica", size=15, weight="bold"), height=45, anchor="w")
        btn_smart.configure(command=lambda b=btn_smart: self.run_smart_rename(b))
        btn_smart.pack(pady=15, padx=20, fill="x")

        # 3. Cleanup Tab
        create_tool_btn(tab_clean, "📑  ค้นหาและลบไฟล์ที่ซ้ำกัน", "สแกนหาไฟล์ที่มีเนื้อหาเหมือนกันเป๊ะในโฟลเดอร์เป้าหมาย และลบทิ้งให้เหลือแค่อันเดียว", self.run_remove_duplicates, require_folder=True)
        create_tool_btn(tab_clean, "📦  บีบอัดไฟล์ที่ไม่ได้ใช้งานเป็น .ZIP", "ตรวจสอบว่าไฟล์ไหนไม่ค่อยถูกเปิดนานเกิน 6 เดือน จะจับมัดรวมเป็น ZIP ให้ประหยัดที่", self.run_auto_zip, require_folder=True, options=[("เกิน 3 เดือน", 3), ("เกิน 6 เดือน", 6), ("เกิน 12 เดือน", 12)], default_opt=("เกิน 6 เดือน", 6))
        create_tool_btn(tab_clean, "🗑  ลบไฟล์ขยะที่ไม่ได้ใช้งาน", "ลบไฟล์ทั้งหมดในโฟลเดอร์เป้าหมายที่อายุเก่าเกิน 7 วัน (โปรดระวังการลบข้อมูลสำคัญ)", self.run_empty_junk, is_danger=True, require_folder=True, options=[("เกิน 3 วัน", 3), ("เกิน 7 วัน", 7), ("เกิน 14 วัน", 14), ("เกิน 30 วัน", 30)], default_opt=("เกิน 7 วัน", 7))

    def create_ai_chat(self):
        self.frame_ai = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        
        header = ctk.CTkFrame(self.frame_ai, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="ผู้ช่วยค้นหาไฟล์ AI (AI Assistant)", font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"), text_color=TEXT_MAIN).pack(side="left")
        btn_clear_chat = ctk.CTkButton(header, text="🧹 ล้างแชท", width=80, fg_color="#E5E7EB", hover_color="#D1D5DB", text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"), command=self.clear_chat)
        btn_clear_chat.pack(side="right")
        
        self.chat_history = ctk.CTkTextbox(self.frame_ai, wrap="word", fg_color=BG_CARD, text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14), corner_radius=15)
        self.chat_history.pack(fill="both", expand=True, pady=10)
        self.chat_history.insert("end", "✧ AI: สวัสดีครับ! ผมคือผู้ช่วยค้นหาไฟล์ คุณสามารถพิมพ์ถามผมได้เลย เช่น 'มีไฟล์รูปภาพเก่าๆ ของปีที่แล้วไหม?' หรือ 'ในเครื่องมีไฟล์ PDF กี่ไฟล์?'\n\n")
        self.chat_history.configure(state="disabled")
        
        input_frame = ctk.CTkFrame(self.frame_ai, fg_color="transparent")
        input_frame.pack(fill="x", pady=5)
        
        self.entry_chat = ctk.CTkEntry(input_frame, placeholder_text="พิมพ์ข้อความที่นี่...", fg_color=BG_CARD, border_color="#D1D5DB", text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14))
        self.entry_chat.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=8)
        self.entry_chat.bind("<Return>", lambda event: self.send_ai_message())
        
        # Add Right-Click Paste Menu and Mac Command-V support
        def paste_text(event=None):
            try:
                text = self.clipboard_get()
                if self.entry_chat.select_present():
                    self.entry_chat.delete(tk.SEL_FIRST, tk.SEL_LAST)
                self.entry_chat.insert("insert", text)
            except Exception:
                pass
            return "break"
            
        self.entry_chat.bind("<Command-v>", paste_text)
        
        context_menu = tk.Menu(self.entry_chat, tearoff=0)
        context_menu.add_command(label="📋 วาง (Paste)", command=paste_text)
        
        def show_context_menu(event):
            context_menu.tk_popup(event.x_root, event.y_root)
            
        self.entry_chat.bind("<Button-2>", show_context_menu) # Mac Right-click
        self.entry_chat.bind("<Button-3>", show_context_menu) # PC Right-click
        
        btn_send = ctk.CTkButton(input_frame, text="ส่ง", width=80, fg_color=ACCENT_ORANGE, hover_color=ACCENT_HOVER, font=ctk.CTkFont(family="Helvetica", size=16, weight="bold"), command=self.send_ai_message)
        btn_send.pack(side="right", ipady=8)

    def send_ai_message(self):
        user_msg = self.entry_chat.get().strip()
        if not user_msg: return
        
        self.entry_chat.delete(0, 'end')
        self.chat_history.configure(state="normal")
        self.chat_history.insert("end", f"◇ คุณ: {user_msg}\n\n")
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")
        
        def show_loading():
            self.chat_history.configure(state="normal")
            self.chat_history.insert("end", "✧ AI: กำลังค้นหาข้อมูลไฟล์...\n\n")
            self.chat_history.see("end")
            self.chat_history.configure(state="disabled")
            
        self.after(0, show_loading)
        
        def fetch_ai():
            reply = self.ai_assistant.ask_ai(self.current_folder, user_msg)
            
            def update_reply():
                self.chat_history.configure(state="normal")
                self.chat_history.delete("end-3l", "end") # Remove loading text
                self.chat_history.insert("end", f"\n✧ AI: ")
                
                parts = re.split(r'(\[OPEN:.*?\])', reply)
                for part in parts:
                    if part.startswith("[OPEN:") and part.endswith("]"):
                        rel_path = part[6:-1].strip()
                        full_path = os.path.join(self.current_folder, rel_path)
                        
                        btn = ctk.CTkButton(self.chat_history, text="📂 เปิดไฟล์", width=90, height=24, corner_radius=6,
                                            fg_color="#F3F4F6", border_width=0,
                                            hover_color="#E5E7EB", text_color="#111827",
                                            font=ctk.CTkFont(family="Helvetica", size=12, weight="bold"),
                                            command=lambda p=full_path: self.open_file_location(p))
                                            
                        self.chat_history.insert("end", " ")
                        self.chat_history._textbox.window_create("end", window=btn, padx=5, pady=2)
                        self.chat_history.insert("end", " ")
                    else:
                        self.chat_history.insert("end", part)
                        
                self.chat_history.insert("end", "\n\n" + "-"*40 + "\n\n")
                self.chat_history.see("end")
                self.chat_history.configure(state="disabled")
                
            self.after(0, update_reply)
            
        threading.Thread(target=fetch_ai, daemon=True).start()

    def create_logs(self):
        self.frame_logs = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        header = ctk.CTkFrame(self.frame_logs, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(header, text="ประวัติการใช้งาน (Action Logs)", font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"), text_color=TEXT_MAIN).pack(side="left")
        
        self.btn_undo = ctk.CTkButton(header, text="⟲ ยกเลิกการจัดการไฟล์ล่าสุด (Undo)", fg_color=ACCENT_RED, hover_color=ACCENT_RED_HOVER, font=ctk.CTkFont(family="Helvetica", size=14, weight="bold"), command=self.run_undo)
        self.btn_undo.pack(side="right")
        
        self.log_textbox = ctk.CTkTextbox(self.frame_logs, wrap="word", fg_color=BG_CARD, text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14), corner_radius=15)
        self.log_textbox.pack(fill="both", expand=True, pady=10)

    def create_settings(self):
        self.frame_settings = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        card = ctk.CTkFrame(self.frame_settings, fg_color=BG_CARD, corner_radius=15)
        card.pack(fill="both", expand=True)
        ctk.CTkLabel(card, text="การตั้งค่าระบบ (Settings)", font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"), text_color=TEXT_MAIN).pack(pady=(30, 20), anchor="w", padx=40)
        
        # Excluded Folders UI
        ctk.CTkLabel(card, text="โฟลเดอร์ยกเว้น (AI และระบบจะไม่ยุ่งกับไฟล์ในนี้):", text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14, weight="bold")).pack(anchor="w", padx=40, pady=(10,5))
        
        ex_frame = ctk.CTkFrame(card, fg_color="transparent")
        ex_frame.pack(anchor="w", padx=40, fill="x")
        
        self.listbox_excluded = ctk.CTkTextbox(ex_frame, width=380, height=100, fg_color=BG_MAIN, border_color="#D1D5DB", text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=13))
        self.listbox_excluded.pack(side="left", pady=5)
        self.update_excluded_listbox()
        
        btn_frame = ctk.CTkFrame(ex_frame, fg_color="transparent")
        btn_frame.pack(side="left", padx=10)
        
        btn_add_ex = ctk.CTkButton(btn_frame, text="+ เพิ่มโฟลเดอร์", width=100, fg_color="#374151", hover_color="#1F2937", font=ctk.CTkFont(family="Helvetica", size=13), command=self.add_excluded_folder)
        btn_add_ex.pack(pady=5)
        
        btn_clear_ex = ctk.CTkButton(btn_frame, text="ล้างทั้งหมด", width=100, fg_color=ACCENT_RED, hover_color=ACCENT_RED_HOVER, font=ctk.CTkFont(family="Helvetica", size=13), command=self.clear_excluded_folders)
        btn_clear_ex.pack(pady=5)
        
        btn_save = ctk.CTkButton(card, text="บันทึกการตั้งค่า (Save Settings)", fg_color=ACCENT_ORANGE, hover_color=ACCENT_HOVER, font=ctk.CTkFont(family="Helvetica", size=16, weight="bold"), command=self.save_settings_action)
        btn_save.pack(anchor="w", padx=40, pady=30)

    # --- Actions ---

    def update_excluded_listbox(self):
        self.listbox_excluded.configure(state="normal")
        self.listbox_excluded.delete("1.0", "end")
        for f in self.config_data.get("excluded_folders", []):
            self.listbox_excluded.insert("end", f + "\n")
        self.listbox_excluded.configure(state="disabled")

    def add_excluded_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            ex_list = self.config_data.get("excluded_folders", [])
            if folder not in ex_list:
                ex_list.append(folder)
                self.config_data["excluded_folders"] = ex_list
                self.save_config("excluded_folders", ex_list)
                self.update_excluded_listbox()
                self.sync_excluded_folders()

    def clear_excluded_folders(self):
        self.config_data["excluded_folders"] = []
        self.save_config("excluded_folders", [])
        self.update_excluded_listbox()
        self.sync_excluded_folders()
        
    def sync_excluded_folders(self):
        ex = self.config_data.get("excluded_folders", [])
        self.organizer.excluded_folders = ex
        self.cleaner.excluded_folders = ex
        self.watcher_manager.excluded_folders = ex

    def clear_chat(self):
        self.chat_history.configure(state="normal")
        self.chat_history.delete("1.0", "end")
        self.chat_history.insert("end", "✧ AI: สวัสดีครับ! ผมคือผู้ช่วยค้นหาไฟล์ คุณสามารถพิมพ์ถามผมได้เลย เช่น 'มีไฟล์รูปภาพเก่าๆ ของปีที่แล้วไหม?' หรือ 'ในเครื่องมีไฟล์ PDF กี่ไฟล์?'\n\n")
        self.chat_history.configure(state="disabled")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.current_folder = folder
            self.lbl_folder.configure(text=f"📂 โฟลเดอร์ปัจจุบัน: {self.current_folder}")
            
            # Count files and update stats
            num_files = sum(len(files) for _, _, files in os.walk(self.current_folder))
            self.lbl_stats.configure(text=f"📊 จำนวนไฟล์ทั้งหมด: {num_files} ไฟล์")
            
            # Enable folder dependent buttons
            for b in self.folder_btns:
                b["btn"].configure(state="normal", fg_color=b["color"], text_color=b["txt_color"])

    def save_settings_action(self):
        messagebox.showinfo("บันทึกสำเร็จ", "บันทึกการตั้งค่าเรียบร้อยแล้วครับ")

    def run_async(self, btn, func, *args):
        orig_text = ""
        if btn:
            orig_text = btn.cget("text")
            btn.configure(text="⏳ กำลังทำงาน...", state="disabled")
        def wrapper():
            result, msg = func(*args)
            if btn:
                self.after(0, lambda: btn.configure(text=orig_text, state="normal"))
            if result: messagebox.showinfo("สำเร็จ", msg)
            else: messagebox.showerror("เกิดข้อผิดพลาด", msg)
        threading.Thread(target=wrapper, daemon=True).start()

    def check_folder(self):
        if not self.current_folder or not os.path.exists(self.current_folder):
            messagebox.showwarning("แจ้งเตือน", "กรุณาเลือกโฟลเดอร์เป้าหมายทางด้านบนก่อนใช้งานฟังก์ชันนี้ครับ")
            return False
        return True

    def open_file_location(self, path):
        """เปิด Explorer/Finder แล้วเลือกไฟล์ที่ระบุ รองรับทั้ง Windows, macOS, Linux"""
        if not os.path.exists(path):
            messagebox.showerror("ไม่พบไฟล์", f"ไม่พบไฟล์ที่ระบุ: {path}")
            return
        try:
            if sys.platform.startswith("win"):
                subprocess.run(["explorer", "/select,", os.path.normpath(path)])
            elif sys.platform == "darwin":
                subprocess.run(["open", "-R", path])
            else:
                subprocess.run(["xdg-open", os.path.dirname(path)])
        except Exception as e:
            messagebox.showerror("เกิดข้อผิดพลาด", f"ไม่สามารถเปิดไฟล์ได้: {str(e)}")

    def run_sort_extension(self, btn=None):
        if self.check_folder(): self.run_async(btn, self.organizer.sort_by_extension, self.current_folder)
    def run_sort_date(self, btn=None):
        if self.check_folder(): self.run_async(btn, self.organizer.sort_by_date, self.current_folder)
    def run_remove_duplicates(self, btn=None):
        if self.check_folder(): self.run_async(btn, self.cleaner.remove_duplicates, self.current_folder)
    def run_auto_zip(self, btn=None, months=6):
        if self.check_folder(): self.run_async(btn, self.cleaner.auto_zip_old_files, self.current_folder, months)
    def run_empty_junk(self, btn=None, days=7):
        if self.check_folder(): self.run_async(btn, self.cleaner.empty_junk_folder, self.current_folder, days)

    def run_convert_image(self, btn=None):
        file = filedialog.askopenfilename(filetypes=[("Image files", "*.heic *.webp *.png *.jpg")])
        if file: self.run_async(btn, self.converter.convert_image, file, "JPEG")
    def run_compress_image(self, btn=None, mb_limit=5):
        file = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg")])
        if file: self.run_async(btn, self.converter.compress_image, file, mb_limit)
    def run_convert_pdf(self, btn=None):
        file = filedialog.askopenfilename(filetypes=[("Word Document", "*.docx")])
        if file: self.run_async(btn, self.converter.convert_docx_to_pdf, file)
    def run_extract_audio(self, btn=None):
        file = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv")])
        if file: self.run_async(btn, self.converter.extract_audio, file)
    def run_smart_rename(self, btn=None):
        file = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png *.jpeg *.webp")])
        if file:
            if not self.organizer.api_key:
                messagebox.showwarning("แจ้งเตือน", "ยังไม่ได้ใส่ API Key ของ Gemini กรุณาตั้งค่าก่อนใช้งานในแท็บ Settings ครับ")
                return
            self.run_async(btn, self.organizer.smart_rename, file)

    def run_undo(self):
        result, msg = self.logger.undo_last_action()
        if result:
            messagebox.showinfo("ย้อนกลับสำเร็จ", msg)
            self.refresh_logs()
        else:
            messagebox.showerror("ไม่สามารถย้อนกลับได้", msg)

    def refresh_logs(self):
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        if os.path.exists(self.logger.log_txt):
            with open(self.logger.log_txt, "r", encoding="utf-8") as f:
                self.log_textbox.insert("end", f.read())
        self.log_textbox.configure(state="disabled")

    def toggle_watch(self):
        if self.switch_watch.get() == 1:
            if self.check_folder():
                callbacks = {'on_pdf_convert': self.converter.convert_docx_to_pdf, 'on_new_file': lambda path: self.organizer.sort_by_extension(self.current_folder)}
                res, msg = self.watcher_manager.start_watching(self.current_folder, callbacks)
                if not res:
                    messagebox.showerror("เกิดข้อผิดพลาดระบบจับตา", msg)
                    self.switch_watch.deselect()
            else:
                self.switch_watch.deselect()
        else:
            self.watcher_manager.stop_watching()

if __name__ == "__main__":
    app = SmartFileManagerApp()
    app.mainloop()
