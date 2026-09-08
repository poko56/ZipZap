"""
สร้างไฟล์ทดสอบสำหรับ ZipZap ลง TestFolder/

ต่างจากเวอร์ชันเดิม: ทุกไฟล์เป็น "ไฟล์จริง" ตามนามสกุล ไม่ใช่ข้อความ "AAAA..."
ที่ตั้งนามสกุลหลอก (แบบเดิมทำให้ทดสอบ convert_image/convert_docx_to_pdf/extract_audio
ไม่ได้จริง เพราะไฟล์เปิดไม่ขึ้นตั้งแต่แรก) และไฟล์ duplicate_of_* จะก็อปปี้ไบต์จากไฟล์
ต้นทางจริงๆ (ไม่ใช่สุ่มเนื้อหาใหม่) เพื่อให้ remove_duplicates มีของให้เจอจริง

ใช้ path สัมพัทธ์กับตำแหน่งสคริปต์เอง (เดิม hardcode /Users/pokoman/... ซึ่งเป็น
path เฉพาะเครื่อง Mac ของผู้เขียนเดิม รันบนเครื่องอื่นไม่ได้)
"""

import argparse
import io
import os
import random
import time

import numpy as np
from PIL import Image, ImageDraw
import pillow_heif
from docx import Document
from openpyxl import Workbook
from pptx import Presentation
from moviepy import AudioClip, ColorClip


# ---------- ตัวสร้างไฟล์แต่ละประเภท (คืนค่า path ที่สร้างจริง) ----------

def make_txt(path, rng):
    lines = [
        "Meeting notes",
        f"Attendees: {rng.randint(3, 12)} people",
        "Action items:",
        "- Follow up on budget review",
        "- Prepare next quarter roadmap",
        f"Reference number: {rng.randint(1000, 9999)}",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def make_docx(path, rng):
    doc = Document()
    doc.add_heading("Report", level=1)
    doc.add_paragraph(f"Generated for testing. Reference: {rng.randint(1000, 9999)}")
    doc.add_paragraph("Summary of this quarter's progress and next steps.")
    doc.save(path)
    return path


def make_xlsx(path, rng):
    wb = Workbook()
    ws = wb.active
    ws.append(["Item", "Amount", "Date"])
    for _ in range(5):
        ws.append([f"Item-{rng.randint(1, 99)}", rng.randint(100, 10000), "2025-01-01"])
    wb.save(path)
    return path


def make_pptx(path, rng):
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[0])
    slide.shapes.title.text = "Presentation"
    slide.placeholders[1].text = f"Generated for testing #{rng.randint(1000, 9999)}"
    prs.save(path)
    return path


def _random_image(rng, size=(800, 600)):
    """สร้างภาพจริงที่มีเนื้อหาต่างกันทุกครั้ง (สี่เหลี่ยม/วงกลมสุ่มสี) ไม่ใช่ภาพว่างเปล่า"""
    img = Image.new("RGB", size, (rng.randint(180, 255), rng.randint(180, 255), rng.randint(180, 255)))
    draw = ImageDraw.Draw(img)
    for _ in range(rng.randint(3, 8)):
        x0, y0 = rng.randint(0, size[0] - 100), rng.randint(0, size[1] - 100)
        x1, y1 = x0 + rng.randint(20, 100), y0 + rng.randint(20, 100)
        color = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
        if rng.random() < 0.5:
            draw.rectangle([x0, y0, x1, y1], fill=color)
        else:
            draw.ellipse([x0, y0, x1, y1], fill=color)
    return img


def make_jpg(path, rng):
    _random_image(rng).save(path, "JPEG", quality=85)
    return path


def make_png(path, rng):
    _random_image(rng, size=(600, 400)).save(path, "PNG")
    return path


def make_heic(path, rng):
    img = _random_image(rng, size=(640, 480))
    heif_file = pillow_heif.from_pillow(img)
    heif_file.save(path, quality=80)
    return path


def make_pdf(path, rng):
    """สร้าง PDF จริงแบบ single-page จากภาพเอกสารจำลอง (ไม่ต้องพึ่ง reportlab)"""
    img = Image.new("RGB", (850, 1100), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((60, 60), "Document", fill=(0, 0, 0))
    draw.text((60, 100), f"Reference: {rng.randint(1000, 9999)}", fill=(0, 0, 0))
    draw.rectangle([60, 150, 790, 152], fill=(0, 0, 0))
    img.save(path, "PDF")
    return path


def make_mp3(path, rng):
    freq = rng.choice([330, 392, 440, 494])
    duration = rng.uniform(1.0, 2.5)
    clip = AudioClip(lambda t: np.sin(freq * 2 * np.pi * t) * 0.3, duration=duration, fps=44100)
    clip.write_audiofile(path, logger=None)
    return path


def make_mp4(path, rng):
    """สร้างวิดีโอสั้นๆ พร้อมเสียง (เพื่อให้ extract_audio ทดสอบได้จริง)"""
    duration = rng.uniform(1.0, 2.0)
    color = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
    vclip = ColorClip(size=(320, 240), color=color, duration=duration).with_fps(24)
    freq = rng.choice([330, 392, 440])
    aclip = AudioClip(lambda t: np.sin(freq * 2 * np.pi * t) * 0.3, duration=duration, fps=44100)
    vclip = vclip.with_audio(aclip)
    vclip.write_videofile(path, logger=None, audio_codec="aac")
    return path


def make_zip(path, rng):
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("readme.txt", f"backup contents #{rng.randint(1000, 9999)}")
    with open(path, "wb") as f:
        f.write(buf.getvalue())
    return path


# นามสกุล -> ฟังก์ชันสร้างไฟล์จริง
GENERATORS = {
    ".txt": make_txt,
    ".docx": make_docx,
    ".xlsx": make_xlsx,
    ".pptx": make_pptx,
    ".jpg": make_jpg,
    ".png": make_png,
    ".heic": make_heic,
    ".pdf": make_pdf,
    ".mp3": make_mp3,
    ".mp4": make_mp4,
    ".zip": make_zip,
}


def create_large_test_folder(test_dir=None, count=60, seed=None):
    if test_dir is None:
        test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TestFolder")

    rng = random.Random(seed)

    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    os.makedirs(os.path.join(test_dir, "Convert_to_PDF"), exist_ok=True)

    # ชื่อไฟล์: template + นามสกุลที่ต้องมีตัวสร้างจริงรองรับ
    templates = [
        ("report_Q{}.docx", ["Q1", "Q2", "Q3", "Q4"]),
        ("budget_202{}.xlsx", ["3", "4", "5", "6"]),
        ("meeting_notes_{}.txt", ["jan", "feb", "mar", "apr", "may", "jun"]),
        ("vacation_{}_{}.jpg", ["japan", "korea", "thai", "usa"], ["2023", "2024", "2025"]),
        ("receipt_{}_{}.png", ["starbucks", "apple", "amazon", "shopee"], ["jan", "feb", "mar"]),
        ("project_proposal_{}.pdf", ["v1", "v2", "final", "draft"]),
        ("invoice_{}.pdf", [str(i) for i in range(1001, 1020)]),
        ("presentation_{}.pptx", ["marketing", "sales", "dev", "design"]),
        ("song_{}.mp3", ["rock", "pop", "jazz", "lofi"]),
        ("interview_{}.mp4", ["candidate1", "candidate2", "candidate3"]),
        ("backup_{}.zip", ["db", "files", "config"]),
        ("screenshot_{}.png", [str(i) for i in range(1, 10)]),
        ("IMG_{}.heic", [str(i) for i in range(9900, 9920)]),
    ]

    files_created = 0
    created_by_ext = {}  # นามสกุล -> list ของ path ที่สร้างสำเร็จแล้ว (ไว้ก็อปปี้ทำ duplicate)
    now = time.time()

    for i in range(count):
        tmpl = rng.choice(templates)
        name_template = tmpl[0]
        args = [rng.choice(opts) for opts in tmpl[1:]]
        filename = name_template.format(*args)
        ext = os.path.splitext(filename)[1].lower()
        generator = GENERATORS.get(ext)
        if generator is None:
            continue

        is_duplicate = (i % 5 == 0) and created_by_ext.get(ext)

        if is_duplicate:
            # ไฟล์ duplicate_of_* ก็อปปี้ไบต์จากไฟล์ประเภทเดียวกันที่สร้างไปแล้วจริงๆ
            # เพื่อให้ MD5 ตรงกัน remove_duplicates ถึงจะมีของให้เจอ (ของเดิมแค่สุ่มเนื้อหาใหม่
            # ทั้งที่ตั้งชื่อว่า duplicate ทำให้ตรวจ MD5 แล้วไม่มีไฟล์ซ้ำจริงสักคู่)
            source_path = rng.choice(created_by_ext[ext])
            filename = f"duplicate_of_{os.path.basename(source_path)}"
            file_path = os.path.join(test_dir, filename)
            if os.path.exists(file_path):
                continue
            import shutil as _shutil
            _shutil.copy2(source_path, file_path)
        else:
            # ถ้า i % 5 == 0 แต่ยังไม่มีไฟล์ประเภทนี้ให้ก็อปปี้เลย (เพิ่งเจอชนิดนี้ครั้งแรก)
            # ก็สร้างเป็นไฟล์ปกติไปก่อน ไม่ตั้งชื่อ duplicate_of_ หลอกๆ เพราะเนื้อหาไม่ได้ซ้ำใคร
            file_path = os.path.join(test_dir, filename)
            if os.path.exists(file_path):
                continue
            generator(file_path, rng)
            # เก็บเฉพาะไฟล์ "ต้นฉบับ" ไว้เป็นแหล่งก็อปปี้ ไม่เอาไฟล์ duplicate มาต่อยอดเป็น
            # duplicate ซ้อน duplicate อีกที (ชื่อจะพันกันโดยไม่จำเป็น)
            created_by_ext.setdefault(ext, []).append(file_path)

        # สุ่มวันที่แก้ไขไฟล์ย้อนหลังได้ถึง 2 ปี (ไว้ทดสอบ sort_by_date / auto_zip_old_files)
        days_ago = rng.randint(0, 730)
        mtime = now - (days_ago * 24 * 60 * 60)
        os.utime(file_path, (mtime, mtime))
        files_created += 1

    # ภาพขนาดใหญ่ (real photo-like JPEG ความละเอียดสูง) ไว้ทดสอบ compress_image (เกณฑ์ 5MB)
    huge_path = os.path.join(test_dir, "raw_camera_photo.jpg")
    noise = (np.random.default_rng(seed).integers(0, 256, (3000, 4000, 3), dtype=np.uint8))
    Image.fromarray(noise).save(huge_path, "JPEG", quality=100)
    files_created += 1

    print(f"Created {files_created} files in {test_dir}")
    return test_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=None, help="โฟลเดอร์ปลายทาง (ค่าเริ่มต้น: ./TestFolder ข้างสคริปต์นี้)")
    parser.add_argument("--count", type=int, default=60, help="จำนวนไฟล์ที่จะสร้าง (ค่าเริ่มต้น 60)")
    parser.add_argument("--seed", type=int, default=None, help="random seed สำหรับผลลัพธ์ที่ทำซ้ำได้")
    args = parser.parse_args()
    create_large_test_folder(test_dir=args.out, count=args.count, seed=args.seed)
