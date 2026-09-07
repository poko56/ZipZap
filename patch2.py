import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update save_settings_action and remove default folder UI
old_settings_ui = """        ctk.CTkLabel(card, text="โฟลเดอร์เป้าหมายเริ่มต้น (Default Target Folder):", text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14, weight="bold")).pack(anchor="w", padx=40, pady=(20,5))
        self.entry_folder = ctk.CTkEntry(card, width=500, fg_color=BG_MAIN, border_color="#D1D5DB", text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14))
        self.entry_folder.pack(anchor="w", padx=40, pady=5)
        self.entry_folder.insert(0, self.config_data.get("watch_folder", ""))
        
        btn_save = ctk.CTkButton(card, text="บันทึกการตั้งค่า (Save Settings)", fg_color=ACCENT_ORANGE, hover_color=ACCENT_HOVER, font=ctk.CTkFont(family="Helvetica", size=16, weight="bold"), command=self.save_settings_action)
        btn_save.pack(anchor="w", padx=40, pady=30)"""

new_settings_ui = """        btn_save = ctk.CTkButton(card, text="บันทึกการตั้งค่า (Save Settings)", fg_color=ACCENT_ORANGE, hover_color=ACCENT_HOVER, font=ctk.CTkFont(family="Helvetica", size=16, weight="bold"), command=self.save_settings_action)
        btn_save.pack(anchor="w", padx=40, pady=30)"""
content = content.replace(old_settings_ui, new_settings_ui)

old_save_action = """    def save_settings_action(self):
        folder = self.entry_folder.get()
        if os.path.exists(folder) or folder == "":
            self.save_config("watch_folder", folder)
            self.current_folder = folder
            self.lbl_folder.configure(text=f"📂 โฟลเดอร์ปัจจุบัน: {self.current_folder if self.current_folder else 'ยังไม่ได้เลือก'}")
            messagebox.showinfo("บันทึกสำเร็จ", "บันทึกการตั้งค่าเรียบร้อยแล้วครับ")
        else:
            messagebox.showerror("เกิดข้อผิดพลาด", "ไม่พบโฟลเดอร์ตามที่อยู่ที่ระบุ")"""

new_save_action = """    def save_settings_action(self):
        messagebox.showinfo("บันทึกสำเร็จ", "บันทึกการตั้งค่าเรียบร้อยแล้วครับ")"""
content = content.replace(old_save_action, new_save_action)

# 2. Update create_tool_btn
old_create_tool_btn = """        def create_tool_btn(parent, text, command_func, is_danger=False, require_folder=False):
            color = ACCENT_RED if is_danger else BG_CARD
            hover = ACCENT_RED_HOVER if is_danger else "#E5E7EB"
            txt_color = "#FFF" if is_danger else TEXT_MAIN
            btn = ctk.CTkButton(parent, text=text, command=None,
                                fg_color=color, text_color=txt_color, hover_color=hover,
                                font=ctk.CTkFont(family="Helvetica", size=15), height=45, anchor="w" if not is_danger else "center")
            btn.configure(command=lambda b=btn: command_func(b))
            btn.pack(pady=10, padx=20, fill="x")
            if require_folder:
                btn.configure(state="disabled", fg_color="#F3F4F6", text_color="#9CA3AF")
                self.folder_btns.append({"btn": btn, "color": color, "txt_color": txt_color})
            return btn"""

new_create_tool_btn = """        def create_tool_btn(parent, text, command_func, is_danger=False, require_folder=False, options=None, default_opt=None):
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
                btn.configure(command=lambda b=btn, ov=opt_var, vm=val_map: command_func(b, vm[ov.get()]))
                btn.pack(side="left", fill="x", expand=True)
            else:
                btn = ctk.CTkButton(frame, text=text, command=None,
                                    fg_color=color, text_color=txt_color, hover_color=hover,
                                    font=ctk.CTkFont(family="Helvetica", size=15), height=45, anchor="w" if not is_danger else "center")
                btn.configure(command=lambda b=btn: command_func(b))
                btn.pack(side="left", fill="x", expand=True)
                
            if require_folder:
                btn.configure(state="disabled", fg_color="#F3F4F6", text_color="#9CA3AF")
                self.folder_btns.append({"btn": btn, "color": color, "txt_color": txt_color})
            return btn"""
content = content.replace(old_create_tool_btn, new_create_tool_btn)


# 3. Update buttons
content = content.replace(
    'create_tool_btn(tab_conv, "🗜  บีบอัดขนาดรูปภาพ (ที่ใหญ่กว่า 5MB)", self.run_compress_image)',
    'create_tool_btn(tab_conv, "🗜  บีบอัดขนาดรูปภาพ", self.run_compress_image, options=[("ถ้าเกิน 1MB", 1), ("ถ้าเกิน 5MB", 5), ("ถ้าเกิน 10MB", 10)], default_opt=("ถ้าเกิน 5MB", 5))'
)
content = content.replace(
    'create_tool_btn(tab_clean, "📦  บีบอัดไฟล์ที่ไม่ได้ใช้งานเกิน 6 เดือนเป็น .ZIP", self.run_auto_zip, require_folder=True)',
    'create_tool_btn(tab_clean, "📦  บีบอัดไฟล์ที่ไม่ได้ใช้งานเป็น .ZIP", self.run_auto_zip, require_folder=True, options=[("เกิน 3 เดือน", 3), ("เกิน 6 เดือน", 6), ("เกิน 12 เดือน", 12)], default_opt=("เกิน 6 เดือน", 6))'
)
content = content.replace(
    'create_tool_btn(tab_clean, "🗑  ลบไฟล์เก่าที่ไม่ได้ใช้งานเกิน 7 วัน", self.run_empty_junk, is_danger=True, require_folder=True)',
    'create_tool_btn(tab_clean, "🗑  ลบไฟล์ขยะที่ไม่ได้ใช้งาน", self.run_empty_junk, is_danger=True, require_folder=True, options=[("เกิน 3 วัน", 3), ("เกิน 7 วัน", 7), ("เกิน 14 วัน", 14), ("เกิน 30 วัน", 30)], default_opt=("เกิน 7 วัน", 7))'
)


# 4. Update function signatures
content = content.replace("def run_auto_zip(self, btn=None):\n        if self.check_folder(): self.run_async(btn, self.cleaner.auto_zip_old_files, self.current_folder, 6)", "def run_auto_zip(self, btn=None, months=6):\n        if self.check_folder(): self.run_async(btn, self.cleaner.auto_zip_old_files, self.current_folder, months)")
content = content.replace("def run_empty_junk(self, btn=None):\n        if self.check_folder(): self.run_async(btn, self.cleaner.empty_junk_folder, self.current_folder, 7)", "def run_empty_junk(self, btn=None, days=7):\n        if self.check_folder(): self.run_async(btn, self.cleaner.empty_junk_folder, self.current_folder, days)")
content = content.replace("def run_compress_image(self, btn=None):\n        file = filedialog.askopenfilename(filetypes=[(\"Image files\", \"*.jpg *.png *.jpeg\")])\n        if file: self.run_async(btn, self.converter.compress_image, file, 5)", "def run_compress_image(self, btn=None, mb_limit=5):\n        file = filedialog.askopenfilename(filetypes=[(\"Image files\", \"*.jpg *.png *.jpeg\")])\n        if file: self.run_async(btn, self.converter.compress_image, file, mb_limit)")


with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)
print("Applied inline options to main.py")
