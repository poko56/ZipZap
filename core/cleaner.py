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

    TRASH_DIR_NAME = ".zipzap_trash"

    def _get_trash_folder(self, base_folder):
        return os.path.join(base_folder, self.TRASH_DIR_NAME)

    def _prune_trash_dirs(self, root, dirs):
        """ตัด .zipzap_trash ออกจากการ walk ไฟล์ที่ย้ายเข้า trash แล้วจะได้ไม่ถูกสแกนซ้ำ"""
        dirs[:] = [d for d in dirs if d != self.TRASH_DIR_NAME]

    def _move_to_trash(self, filepath, trash_folder):
        """ย้ายไฟล์เข้า trash folder แทนการลบถาวร แล้ว log_move ให้ปุ่ม Undo กู้คืนได้
        คืนค่า path ปลายทางที่ไฟล์ถูกย้ายไปเก็บ"""
        os.makedirs(trash_folder, exist_ok=True)
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)
        trash_path = os.path.join(trash_folder, filename)
        counter = 1
        while os.path.exists(trash_path):
            trash_path = os.path.join(trash_folder, f"{name}_{counter}{ext}")
            counter += 1

        shutil.move(filepath, trash_path)
        self.logger.log_move(filepath, trash_path)
        return trash_path

    def scan_duplicates(self, folder_path):
        """Scan and return a list of duplicate files dicts: {'path': p, 'size': s, 'original': org}"""
        results = []
        if not os.path.exists(folder_path): return results

        hashes = {}
        for root, dirs, files in os.walk(folder_path):
            self._prune_trash_dirs(root, dirs)
            for filename in files:
                filepath = os.path.join(root, filename)
                if self._is_excluded(filepath): continue
                file_hash = self._get_file_hash(filepath)
                if file_hash:
                    if file_hash in hashes:
                        try:
                            size = os.path.getsize(filepath)
                            results.append({"path": filepath, "size": size, "original": hashes[file_hash], "type": "duplicate"})
                        except: pass
                    else:
                        hashes[file_hash] = filepath
        return results

    def scan_junk(self, folder_path):
        """Scan and return a list of temporary/junk files (e.g., .tmp, .log, .cache)"""
        results = []
        if not os.path.exists(folder_path): return results
        junk_exts = ['.tmp', '.log', '.cache', '.bak', '.dat']
        
        for root, dirs, files in os.walk(folder_path):
            self._prune_trash_dirs(root, dirs)
            for filename in files:
                filepath = os.path.join(root, filename)
                if self._is_excluded(filepath): continue
                if any(filename.lower().endswith(ext) for ext in junk_exts):
                    try:
                        size = os.path.getsize(filepath)
                        results.append({"path": filepath, "size": size, "type": "junk"})
                    except: pass
        return results

    def scan_large_files(self, folder_path, min_size_mb=50, days_old=30):
        """Scan and return files larger than min_size_mb AND older than days_old"""
        results = []
        if not os.path.exists(folder_path): return results
        
        min_bytes = min_size_mb * 1024 * 1024
        old_seconds = days_old * 24 * 60 * 60
        current_time = time.time()
        
        for root, dirs, files in os.walk(folder_path):
            self._prune_trash_dirs(root, dirs)
            for filename in files:
                filepath = os.path.join(root, filename)
                if self._is_excluded(filepath): continue
                try:
                    size = os.path.getsize(filepath)
                    if size > min_bytes:
                        file_age = current_time - os.path.getmtime(filepath)
                        if file_age > old_seconds:
                            results.append({"path": filepath, "size": size, "type": "large"})
                except: pass
        return results

    def clean_files(self, file_paths, base_folder=None):
        """ย้ายไฟล์ในลิสต์เข้า .zipzap_trash แทนการลบถาวร แล้วคืนค่าจำนวนไฟล์กับพื้นที่ที่ได้คืน

        ย้ายแทน os.remove เพราะ log_move ทำให้ปุ่ม Undo กู้ไฟล์กลับได้เหมือนการย้าย/เปลี่ยนชื่อ
        อื่นๆ ในโปรแกรม (ของเดิมลบทิ้งถาวร กดพลาดแล้วไฟล์หายเลย)

        :param base_folder: โฟลเดอร์ที่จะสร้าง .zipzap_trash ไว้ข้างใน ถ้าไม่ระบุจะใช้โฟลเดอร์
                            ที่ไฟล์นั้นอยู่ (กันเคสไฟล์มาจากคนละไดรฟ์ ย้ายข้ามไดรฟ์ไม่ได้)
        """
        saved_bytes = 0
        deleted_count = 0
        for path in file_paths:
            try:
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    trash_root = base_folder if base_folder else os.path.dirname(path)
                    self._move_to_trash(path, self._get_trash_folder(trash_root))
                    saved_bytes += size
                    deleted_count += 1
            except Exception as e:
                self.logger.log_action("ERROR", f"Failed to move {path} to trash: {e}")

        saved_mb = saved_bytes / (1024 * 1024)
        self.logger.log_action("CLEAN_UP", f"Moved {deleted_count} files to trash, freed {saved_mb:.2f} MB")
        return deleted_count, saved_mb
