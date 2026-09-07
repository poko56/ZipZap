import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SmartFileHandler(FileSystemEventHandler):
    def __init__(self, logger, callbacks, excluded_folders=None):
        self.logger = logger
        self.callbacks = callbacks
        self.processed_files = set()
        self.excluded_folders = excluded_folders or []

    def _is_excluded(self, file_path):
        abs_path = os.path.abspath(file_path)
        for ex_folder in self.excluded_folders:
            ex_abs = os.path.abspath(ex_folder)
            try:
                if os.path.commonpath([abs_path, ex_abs]) == ex_abs: return True
            except ValueError: pass
        return False

    def process_file(self, file_path):
        time.sleep(2)
        if self._is_excluded(file_path): return
        if not os.path.exists(file_path):
            return
            
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            return
            
        filename = os.path.basename(file_path)
        
        if "Convert_to_PDF" in file_path:
            if filename.lower().endswith((".docx", ".txt")) and 'on_pdf_convert' in self.callbacks:
                self.logger.log_action("WATCHER", f"Detected {filename} in Convert_to_PDF. Triggering conversion.")
                self.callbacks['on_pdf_convert'](file_path)
        else:
            if 'on_new_file' in self.callbacks:
                self.logger.log_action("WATCHER", f"Detected new file {filename}. Triggering auto-sort.")
                self.callbacks['on_new_file'](file_path)

    def on_created(self, event):
        if not event.is_directory:
            file_path = event.src_path
            if file_path not in self.processed_files:
                self.processed_files.add(file_path)
                threading.Thread(target=self.process_file, args=(file_path,), daemon=True).start()

    def on_moved(self, event):
        if not event.is_directory:
            file_path = event.dest_path
            if file_path not in self.processed_files:
                self.processed_files.add(file_path)
                threading.Thread(target=self.process_file, args=(file_path,), daemon=True).start()


class WatcherManager:
    def __init__(self, logger):
        self.logger = logger
        self.observer = None
        self.excluded_folders = []
        
    def start_watching(self, path, callbacks):
        if not os.path.exists(path):
            return False, "ไม่พบโฟลเดอร์เป้าหมาย"
            
        os.makedirs(os.path.join(path, "Convert_to_PDF"), exist_ok=True)
            
        if self.observer is not None:
            self.stop_watching()
            
        event_handler = SmartFileHandler(self.logger, callbacks, self.excluded_folders)
        self.observer = Observer()
        self.observer.schedule(event_handler, path, recursive=True)
        self.observer.start()
        self.logger.log_action("WATCHER_START", f"Started monitoring {path}")
        return True, f"ระบบเริ่มจับตาดูการเปลี่ยนแปลงในโฟลเดอร์ {path} แล้ว"
        
    def stop_watching(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
            self.logger.log_action("WATCHER_STOP", "Stopped monitoring")
            return True, "หยุดระบบจับตาดูโฟลเดอร์แล้ว"
        return False, "ระบบไม่ได้เปิดทำงานอยู่"
