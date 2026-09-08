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

    def scan_duplicates(self, folder_path):
        """Scan and return a list of duplicate files dicts: {'path': p, 'size': s, 'original': org}"""
        results = []
        if not os.path.exists(folder_path): return results
        
        hashes = {}
        for root, _, files in os.walk(folder_path):
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
        
        for root, _, files in os.walk(folder_path):
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
        
        for root, _, files in os.walk(folder_path):
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

    def clean_files(self, file_paths):
        """Delete files from a provided list and return space saved"""
        saved_bytes = 0
        deleted_count = 0
        for path in file_paths:
            try:
                if os.path.exists(path):
                    size = os.path.getsize(path)
                    os.remove(path)
                    saved_bytes += size
                    deleted_count += 1
            except Exception as e:
                self.logger.log_action("ERROR", f"Failed to delete {path}: {e}")
                
        saved_mb = saved_bytes / (1024 * 1024)
        self.logger.log_action("CLEAN_UP", f"Deleted {deleted_count} files, freed {saved_mb:.2f} MB")
        return deleted_count, saved_mb
