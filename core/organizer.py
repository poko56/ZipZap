import os
import shutil
import datetime
from google import genai
from PIL import Image

class FileOrganizer:
    def __init__(self, logger, api_key=""):
        self.logger = logger
        self.api_key = api_key
        self.excluded_folders = []

    def _is_excluded(self, file_path):
        abs_path = os.path.abspath(file_path)
        for ex_folder in self.excluded_folders:
            ex_abs = os.path.abspath(ex_folder)
            try:
                if os.path.commonpath([abs_path, ex_abs]) == ex_abs: return True
            except ValueError: pass
        return False

    def sort_by_extension(self, folder_path):
        """ย้ายไฟล์เข้าโฟลเดอร์ตามนามสกุล"""
        if not os.path.exists(folder_path):
            return False, "ไม่พบโฟลเดอร์ที่ระบุ"
            
        extensions_map = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".heic"],
            "Videos": [".mp4", ".mov", ".avi", ".mkv"],
            "Documents": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".csv"],
            "Audio": [".mp3", ".wav", ".aac", ".flac"],
            "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"]
        }
        
        moved_count = 0
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                if self._is_excluded(file_path): continue
                _, ext = os.path.splitext(filename)
                ext = ext.lower()
                
                target_folder_name = "Others"
                for folder, exts in extensions_map.items():
                    if ext in exts:
                        target_folder_name = folder
                        break
                        
                target_folder = os.path.join(folder_path, target_folder_name)
                os.makedirs(target_folder, exist_ok=True)
                
                new_path = os.path.join(target_folder, filename)
                shutil.move(file_path, new_path)
                self.logger.log_move(file_path, new_path)
                moved_count += 1
                
        return True, f"คัดแยกสำเร็จจำนวน {moved_count} ไฟล์"

    def sort_by_date(self, folder_path):
        """สร้างโฟลเดอร์ย่อยตาม เดือน/ปี แล้วย้ายไฟล์เข้าไป"""
        if not os.path.exists(folder_path):
            return False, "ไม่พบโฟลเดอร์ที่ระบุ"
            
        moved_count = 0
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                if self._is_excluded(file_path): continue
                timestamp = os.path.getmtime(file_path)
                date = datetime.datetime.fromtimestamp(timestamp)
                folder_name = date.strftime("%Y_%m")
                
                target_folder = os.path.join(folder_path, folder_name)
                os.makedirs(target_folder, exist_ok=True)
                
                new_path = os.path.join(target_folder, filename)
                shutil.move(file_path, new_path)
                self.logger.log_move(file_path, new_path)
                moved_count += 1
                
        return True, f"จัดกลุ่มตามวันที่สำเร็จจำนวน {moved_count} ไฟล์"

    def smart_rename(self, file_path):
        """วิเคราะห์ภาพด้วย Gemini API แล้วเปลี่ยนชื่อไฟล์ให้สื่อความหมาย"""
        if not self.api_key:
            return False, "กรุณาตั้งค่า Gemini API Key ในเมนูตั้งค่าก่อน"
            
        client = genai.Client(api_key=self.api_key)
        
        filename, ext = os.path.splitext(os.path.basename(file_path))
        ext = ext.lower()
        
        prompt = "Please look at this file and suggest a short, meaningful filename (without extension). Use format like YYYYMMDD_StoreName_Amount if it's a receipt, or just a descriptive name with underscores instead of spaces. Reply ONLY with the suggested filename."
        
        try:
            if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                img = Image.open(file_path)
                response = client.models.generate_content(
                    model='gemini-flash-lite-latest',
                    contents=[prompt, img]
                )
            else:
                return False, "ฟังก์ชันนี้รองรับเฉพาะไฟล์รูปภาพในตอนนี้"
                
            suggested_name = response.text.strip().replace(" ", "_")
            for char in ['<', '>', ':', '"', '/', '\\', '|', '?', '*']:
                suggested_name = suggested_name.replace(char, '')
                
            new_filename = suggested_name + ext
            new_path = os.path.join(os.path.dirname(file_path), new_filename)
            
            counter = 1
            while os.path.exists(new_path):
                new_path = os.path.join(os.path.dirname(file_path), f"{suggested_name}_{counter}{ext}")
                counter += 1
                
            shutil.move(file_path, new_path)
            self.logger.log_move(file_path, new_path)
            return True, f"เปลี่ยนชื่อไฟล์เป็น: {os.path.basename(new_path)}"
            
        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการทำ Smart Rename: {str(e)}"
