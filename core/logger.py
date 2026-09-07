import os
import json
import shutil
import datetime

class ActionLogger:
    def __init__(self, log_txt="action_log.txt", log_json="action_log.json"):
        self.log_txt = log_txt
        self.log_json = log_json

    def get_timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log_action(self, action_type, details):
        """บันทึกประวัติการทำงานลงไฟล์ text"""
        log_entry = f"[{self.get_timestamp()}] {action_type}: {details}\n"
        with open(self.log_txt, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def log_move(self, original_path, new_path):
        """บันทึกข้อมูลการย้ายหรือเปลี่ยนชื่อไฟล์ลง json เพื่อใช้ทำ Undo"""
        action = {
            "timestamp": self.get_timestamp(),
            "original_path": original_path,
            "new_path": new_path
        }
        
        logs = []
        if os.path.exists(self.log_json):
            try:
                with open(self.log_json, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except json.JSONDecodeError:
                logs = []
                
        logs.append(action)
        with open(self.log_json, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=4)
            
        self.log_action("MOVE/RENAME", f"From '{original_path}' -> '{new_path}'")

    def undo_last_action(self):
        """เรียกคืนไฟล์กลับสู่ตำแหน่งเดิมหรือชื่อเดิม (Undo)"""
        if not os.path.exists(self.log_json):
            return False, "ไม่พบประวัติการทำงานใดๆ"
            
        try:
            with open(self.log_json, "r", encoding="utf-8") as f:
                logs = json.load(f)
                
            if not logs:
                return False, "ไม่มีประวัติให้ย้อนกลับแล้ว"
                
            last_action = logs.pop()
            new_path = last_action["new_path"]
            original_path = last_action["original_path"]
            
            if os.path.exists(new_path):
                os.makedirs(os.path.dirname(original_path), exist_ok=True)
                shutil.move(new_path, original_path)
                
                with open(self.log_json, "w", encoding="utf-8") as f:
                    json.dump(logs, f, ensure_ascii=False, indent=4)
                    
                self.log_action("UNDO", f"Reverted '{new_path}' -> '{original_path}'")
                return True, f"ย้อนกลับสำเร็จ ไฟล์กลับไปที่ {original_path}"
            else:
                with open(self.log_json, "w", encoding="utf-8") as f:
                    json.dump(logs, f, ensure_ascii=False, indent=4)
                return False, f"หาไฟล์ {new_path} ไม่พบ ไม่สามารถย้อนกลับได้"
                
        except Exception as e:
            return False, f"เกิดข้อผิดพลาดในการย้อนกลับ: {str(e)}"
