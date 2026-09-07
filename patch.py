import os
import re

# Patch organizer.py
with open("core/organizer.py", "r", encoding="utf-8") as f:
    content = f.read()

init_old = """    def __init__(self, logger, api_key=""):
        \"\"\"
        :param logger: Instance of ActionLogger
        :param api_key: Gemini API Key for smart_rename
        \"\"\"
        self.logger = logger
        self.api_key = api_key"""
init_new = """    def __init__(self, logger, api_key=""):
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
        return False"""
content = content.replace(init_old, init_new)
content = content.replace("if os.path.isfile(file_path):", "if os.path.isfile(file_path):\n                if self._is_excluded(file_path): continue")

with open("core/organizer.py", "w", encoding="utf-8") as f:
    f.write(content)

# Patch cleaner.py
with open("core/cleaner.py", "r", encoding="utf-8") as f:
    content = f.read()

init_old = """    def __init__(self, logger):
        \"\"\"
        :param logger: Instance of ActionLogger
        \"\"\"
        self.logger = logger"""
init_new = """    def __init__(self, logger):
        self.logger = logger
        self.excluded_folders = []

    def _is_excluded(self, file_path):
        abs_path = os.path.abspath(file_path)
        for ex_folder in self.excluded_folders:
            ex_abs = os.path.abspath(ex_folder)
            try:
                if os.path.commonpath([abs_path, ex_abs]) == ex_abs: return True
            except ValueError: pass
        return False"""
content = content.replace(init_old, init_new)
content = content.replace("                file_hash = self._get_file_hash(filepath)", "                if self._is_excluded(filepath): continue\n                file_hash = self._get_file_hash(filepath)")
content = content.replace("if os.path.isfile(filepath) and not filename.endswith(\".zip\"):", "if os.path.isfile(filepath) and not filename.endswith(\".zip\"):\n                if self._is_excluded(filepath): continue")
content = content.replace("                file_age = current_time - os.path.getmtime(filepath)", "                if self._is_excluded(filepath): continue\n                file_age = current_time - os.path.getmtime(filepath)")

with open("core/cleaner.py", "w", encoding="utf-8") as f:
    f.write(content)

# Patch watcher.py
with open("core/watcher.py", "r", encoding="utf-8") as f:
    content = f.read()

handler_init_old = """    def __init__(self, logger, callbacks):
        \"\"\"
        :param logger: Instance of ActionLogger
        :param callbacks: Dictionary of functions to trigger on certain events.
        \"\"\"
        self.logger = logger
        self.callbacks = callbacks
        self.processed_files = set()"""
handler_init_new = """    def __init__(self, logger, callbacks, excluded_folders=None):
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
        return False"""
content = content.replace(handler_init_old, handler_init_new)
content = content.replace("time.sleep(2)", "time.sleep(2)\n        if self._is_excluded(file_path): return")

manager_init_old = """    def __init__(self, logger):
        \"\"\"
        :param logger: Instance of ActionLogger
        \"\"\"
        self.logger = logger
        self.observer = None"""
manager_init_new = """    def __init__(self, logger):
        self.logger = logger
        self.observer = None
        self.excluded_folders = []"""
content = content.replace(manager_init_old, manager_init_new)
content = content.replace("event_handler = SmartFileHandler(self.logger, callbacks)", "event_handler = SmartFileHandler(self.logger, callbacks, self.excluded_folders)")

with open("core/watcher.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Backend patched")
