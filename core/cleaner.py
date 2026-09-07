import os
import hashlib
import zipfile
import shutil
import time

class StorageCleaner:
    def __init__(self, logger):
        self.logger = logger
        self.excluded_folders = []

    def _is_excluded(self, file_path):
        abs_path = os.path.abspath(file_path)
        for ex_folder in self.excluded_folders:
            ex_abs = os.path.abspath(ex_folder)
            try:
                if os.path.commonpath([abs_path, ex_abs]) == ex_abs: return True
            except ValueError: pass
        return False

    def _get_file_hash(self, filepath):
        hasher = hashlib.md5()
        try:
            with open(filepath, 'rb') as f:
                buf = f.read(65536)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = f.read(65536)
            return hasher.hexdigest()
        except Exception:
            return None

    def remove_duplicates(self, folder_path):
        """สแกนหาไฟล์ที่ซ้ำซ้อนกัน และลบไฟล์ที่ซ้ำทิ้ง (เช็คผ่าน Hash MD5)"""
        if not os.path.exists(folder_path):
            return False, "ไม่พบโฟลเดอร์ที่ระบุ"
            
        hashes = {}
        duplicates_removed = 0
        saved_bytes = 0
        
        for root, _, files in os.walk(folder_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                if self._is_excluded(filepath): continue
                file_hash = self._get_file_hash(filepath)
                
                if file_hash:
                    if file_hash in hashes:
                        file_size = os.path.getsize(filepath)
                        saved_bytes += file_size
                        os.remove(filepath)
                        self.logger.log_action("REMOVE_DUPLICATE", f"Deleted {filepath} (duplicate of {hashes[file_hash]})")
                        duplicates_removed += 1
                    else:
                        hashes[file_hash] = filepath
                        
        saved_mb = saved_bytes / (1024 * 1024)
        return True, f"ลบไฟล์ซ้ำ {duplicates_removed} ไฟล์ | ได้พื้นที่คืนมา {saved_mb:.2f} MB"

    def auto_zip_old_files(self, folder_path, months_old=6):
        """ตรวจสอบไฟล์ที่ไม่ได้ถูกใช้งานเกิน x เดือน แล้วจับบีบอัดเป็น .zip"""
        if not os.path.exists(folder_path):
            return False, "ไม่พบโฟลเดอร์ที่ระบุ"
            
        current_time = time.time()
        six_months_seconds = months_old * 30 * 24 * 60 * 60
        
        files_to_zip = []
        
        for filename in os.listdir(folder_path):
            filepath = os.path.join(folder_path, filename)
            if os.path.isfile(filepath) and not filename.endswith(".zip"):
                if self._is_excluded(filepath): continue
                if self._is_excluded(filepath): continue
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > six_months_seconds:
                    files_to_zip.append(filepath)
                    
        if not files_to_zip:
            return True, "ไม่พบไฟล์ที่เก่าเกินกำหนดให้บีบอัด"
            
        zip_name = os.path.join(folder_path, f"Archive_{int(current_time)}.zip")
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files_to_zip:
                zipf.write(file, os.path.basename(file))
                
        for file in files_to_zip:
            os.remove(file)
            
        self.logger.log_action("AUTO_ZIP", f"Zipped {len(files_to_zip)} files into {os.path.basename(zip_name)}")
        return True, f"บีบอัดไฟล์เก่าจำนวน {len(files_to_zip)} ไฟล์ เป็น {os.path.basename(zip_name)}"

    def empty_junk_folder(self, folder_path, days_old=7):
        """ลบไฟล์ขยะที่อยู่ในโฟลเดอร์ชั่วคราวทิ้งเมื่อครบ x วัน"""
        if not os.path.exists(folder_path):
            return False, "ไม่พบโฟลเดอร์ที่ระบุ"
            
        current_time = time.time()
        seven_days_seconds = days_old * 24 * 60 * 60
        deleted_count = 0
        
        for root, dirs, files in os.walk(folder_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                if self._is_excluded(filepath): continue
                file_age = current_time - os.path.getmtime(filepath)
                if file_age > seven_days_seconds:
                    os.remove(filepath)
                    self.logger.log_action("EMPTY_JUNK", f"Deleted old junk file {filepath}")
                    deleted_count += 1
                    
        return True, f"ลบไฟล์ขยะที่อายุเกิน {days_old} วันไปแล้วจำนวน {deleted_count} ไฟล์"
