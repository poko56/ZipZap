import os
from PIL import Image
from pillow_heif import register_heif_opener
from docx2pdf import convert
from moviepy import VideoFileClip

# Register HEIF opener for Pillow to support .heic files
register_heif_opener()

class FileConverter:
    def __init__(self, logger):
        """
        :param logger: Instance of ActionLogger to record actions.
        """
        self.logger = logger

    def convert_image(self, input_path, output_format="JPEG"):
        """แปลงไฟล์รูปภาพที่เปิดยากให้เป็น .jpg หรือ .png"""
        try:
            if not os.path.exists(input_path):
                return False, "ไม่พบไฟล์ต้นฉบับ"
                
            filename, _ = os.path.splitext(os.path.basename(input_path))
            ext = ".jpg" if output_format.upper() in ["JPEG", "JPG"] else ".png"
            output_path = os.path.join(os.path.dirname(input_path), filename + ext)
            
            img = Image.open(input_path)
            if output_format.upper() in ["JPEG", "JPG"] and img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            img.save(output_path, format=output_format)
            self.logger.log_action("CONVERT_IMAGE", f"Converted {os.path.basename(input_path)} to {ext}")
            return True, output_path
        except Exception as e:
            return False, f"แปลงรูปภาพไม่สำเร็จ: {str(e)}"

    def compress_image(self, input_path, max_size_mb=5):
        """ลดขนาดรูปภาพที่มีขนาดใหญ่เกิน max_size_mb"""
        try:
            file_size_mb = os.path.getsize(input_path) / (1024 * 1024)
            if file_size_mb <= max_size_mb:
                return True, "ไฟล์มีขนาดเล็กกว่าขีดจำกัดอยู่แล้ว"
                
            img = Image.open(input_path)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                
            filename, ext = os.path.splitext(os.path.basename(input_path))
            output_path = os.path.join(os.path.dirname(input_path), filename + "_compressed.jpg")
            img.save(output_path, "JPEG", quality=75, optimize=True)
            
            self.logger.log_action("COMPRESS_IMAGE", f"Compressed {os.path.basename(input_path)} (was {file_size_mb:.2f}MB)")
            return True, output_path
        except Exception as e:
            return False, f"บีบอัดรูปภาพไม่สำเร็จ: {str(e)}"

    def convert_docx_to_pdf(self, input_path):
        """แปลงไฟล์ Word เป็น PDF"""
        try:
            if not input_path.lower().endswith(".docx"):
                return False, "รองรับเฉพาะไฟล์ .docx เท่านั้นในตอนนี้"
                
            output_path = os.path.splitext(input_path)[0] + ".pdf"
            convert(input_path, output_path)
            self.logger.log_action("CONVERT_PDF", f"Converted {os.path.basename(input_path)} to PDF")
            return True, output_path
        except Exception as e:
            return False, f"แปลงเป็น PDF ไม่สำเร็จ: {str(e)}"

    def extract_audio(self, input_path):
        """ดึงเสียงออกจากวิดีโอ (MP4 -> MP3)"""
        try:
            if not input_path.lower().endswith((".mp4", ".mov", ".mkv", ".avi")):
                return False, "ไม่รองรับไฟล์วิดีโอนามสกุลนี้"
                
            output_path = os.path.splitext(input_path)[0] + ".mp3"
            video = VideoFileClip(input_path)
            video.audio.write_audiofile(output_path, logger=None)
            video.close()
            
            self.logger.log_action("EXTRACT_AUDIO", f"Extracted audio from {os.path.basename(input_path)}")
            return True, output_path
        except Exception as e:
            return False, f"ดึงเสียงไม่สำเร็จ: {str(e)}"
