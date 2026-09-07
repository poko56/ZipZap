import os
import datetime
from google import genai

class AIAssistant:
    def __init__(self, api_key=""):
        self.api_key = api_key

    def scan_directory(self, folder_path):
        """อ่านข้อมูลไฟล์ในโฟลเดอร์ และจัดรูปแบบเป็น Text สำหรับส่งให้ AI"""
        if not os.path.exists(folder_path):
            return "ไม่พบโฟลเดอร์"
            
        file_info_list = []
        for root, _, files in os.walk(folder_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    stat = os.stat(filepath)
                    size_kb = stat.st_size / 1024
                    mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d')
                    rel_path = os.path.relpath(filepath, folder_path)
                    
                    file_info = f"- {rel_path} (Size: {size_kb:.1f} KB, Date: {mtime})"
                    file_info_list.append(file_info)
                except Exception:
                    pass
                    
        # Limit to 500 files to avoid context window explosion
        if len(file_info_list) > 500:
            file_info_list = file_info_list[:500]
            file_info_list.append("... (มีไฟล์มากเกินไป แสดงผลแค่ 500 รายการแรก)")
            
        return "\n".join(file_info_list)

    def ask_ai(self, folder_path, user_query):
        """ส่งคำถามและรายการไฟล์ให้ Gemini ประมวลผล"""
        if not self.api_key:
            return "กรุณาตั้งค่า Gemini API Key ในเมนู 'ตั้งค่า' ก่อนใช้งาน AI Assistant ครับ"
            
        if not folder_path or not os.path.exists(folder_path):
            return "กรุณาเลือกโฟลเดอร์เป้าหมายในหน้าแผงควบคุมก่อนครับ"
            
        try:
            client = genai.Client(api_key=self.api_key)
            
            # Scan files
            file_tree = self.scan_directory(folder_path)
            
            system_prompt = (
                "You are a helpful File Manager AI Assistant. "
                "The user will ask you questions about their files. "
                "Here is the list of files in their current folder:\n\n"
                f"{file_tree}\n\n"
                "Please answer the user's question clearly and concisely in Thai language. "
                "Only rely on the file list provided above. "
                "IMPORTANT: Whenever you mention a specific file in your response, you MUST append its exact relative path "
                "using this format: [OPEN: relative/path/to/file.ext]. "
                "For example: '1. budget.xlsx [OPEN: budget.xlsx]'"
            )
            
            prompt = f"{system_prompt}\n\nUser Query: {user_query}"
            
            response = client.models.generate_content(
                model='gemini-flash-lite-latest',
                contents=prompt
            )
            return response.text
            
        except Exception as e:
            return f"เกิดข้อผิดพลาดในการเชื่อมต่อกับ AI: {str(e)}"
