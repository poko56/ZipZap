import re

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update create_settings
old_settings = """        ctk.CTkLabel(card, text="Gemini API Key (สำหรับ AI):", text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14, weight="bold")).pack(anchor="w", padx=40, pady=(20,5))
        self.entry_api = ctk.CTkEntry(card, width=500, show="*", fg_color=BG_MAIN, border_color="#D1D5DB", text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14))
        self.entry_api.pack(anchor="w", padx=40, pady=5)
        self.entry_api.insert(0, self.config_data.get("gemini_api_key", ""))"""

new_settings = """        # Excluded Folders UI
        ctk.CTkLabel(card, text="โฟลเดอร์ยกเว้น (AI และระบบจะไม่ยุ่งกับไฟล์ในนี้):", text_color=TEXT_MAIN, font=ctk.CTkFont(family="Helvetica", size=14, weight="bold")).pack(anchor="w", padx=40, pady=(20,5))
        
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
        btn_clear_ex.pack(pady=5)"""

content = content.replace(old_settings, new_settings)

# 2. Update save_settings_action
old_save = """    def save_settings_action(self):
        self.save_config("gemini_api_key", self.entry_api.get())
        folder = self.entry_folder.get()"""

new_save = """    def save_settings_action(self):
        folder = self.entry_folder.get()"""
content = content.replace(old_save, new_save)


# 3. Add new methods
new_methods = """
    def update_excluded_listbox(self):
        self.listbox_excluded.configure(state="normal")
        self.listbox_excluded.delete("1.0", "end")
        for f in self.config_data.get("excluded_folders", []):
            self.listbox_excluded.insert("end", f + "\\n")
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

    def clear_chat(self):"""
content = content.replace("\n    def clear_chat(self):", new_methods)

# 4. Sync in __init__
old_init_end = """        self.ai_assistant = AIAssistant(self.config_data.get("gemini_api_key", ""))

        self.setup_ui()"""
new_init_end = """        self.ai_assistant = AIAssistant(self.config_data.get("gemini_api_key", ""))
        self.sync_excluded_folders()

        self.setup_ui()"""
content = content.replace(old_init_end, new_init_end)


with open("main.py", "w", encoding="utf-8") as f:
    f.write(content)
print("main.py patched")
