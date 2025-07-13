# server.py

# -------------------------------------------------------------------------------
# تم إنشاء هذا المشروع تلقائيًا بواسطة أداة من تطوير قناة "مدرسة الذكاء الاصطناعي"
# يوتيوب  : https://www.youtube.com/@ArabianAiSchool
# إنستغرام: https://www.instagram.com/arabianaischool
# فيسبوك  : https://www.facebook.com/arabianaischool
# تويتر   : https://twitter.com/arabianaischool
# ايميل القناة : arabianaischool@gmail.com
# -------------------------------------------------------------------------------

import sys, os

# ───────────────────────────────────────────────────────────────────────────────
# 1) Setup for bundled binaries (ffmpeg & ImageMagick)
# ───────────────────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    base = sys._MEIPASS
    ffmpeg_path = os.path.join(base, "ffmpeg", "ffmpeg.exe")
    imagemagick_path = os.path.join(base, "ImageMagick", "magick.exe")
else:
    base = os.path.dirname(os.path.abspath(__file__))
    ffmpeg_path = r"ffmpeg.exe"  # fallback local path
    imagemagick_path = r"C:\Program Files\ImageMagick\magick.exe"  # fallback local path

os.environ["FFMPEG_BINARY"] = ffmpeg_path
os.environ["IMAGEMAGICK_BINARY"] = imagemagick_path

import moviepy.config as mpy_config
mpy_config.FFMPEG_BINARY = ffmpeg_path
mpy_config.IMAGEMAGICK_BINARY = imagemagick_path

print("Using ffmpeg:", ffmpeg_path)
print("Using ImageMagick:", imagemagick_path)

# ───────────────────────────────────────────────────────────────────────────────
# 2) Ensure outputs folders exist (images and audio)
# ───────────────────────────────────────────────────────────────────────────────
out_base = os.path.join(os.getcwd(), "outputs")
os.makedirs(out_base, exist_ok=True)
for sub in ("images", "audio"):
    os.makedirs(os.path.join(out_base, sub), exist_ok=True)
    
import threading
import asyncio

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.responses import StreamingResponse

from utils.gemini import query
from utils.write_script import write_content, split_text_to_lines
from utils.image_gen import image_main
from utils.voice_gen import voice_main
from utils.video_creation import video_main

# ───────────────────────────────────────────────────────────────────────────────
# تحديد مسار التشغيل (للتوافق مع PyInstaller onefile)
# ───────────────────────────────────────────────────────────────────────────────
BASE = getattr(sys, "_MEIPASS", os.getcwd())

# ضبط مسارات ffmpeg و ImageMagick الخارجية
os.environ["FFMPEG_BINARY"]      = os.path.join(BASE, "ffmpeg", "ffmpeg.exe")
os.environ["IMAGEMAGICK_BINARY"] = os.path.join(BASE, "ImageMagick", "magick.exe")

# ← إضافة: أبلغ MoviePy عن هذه المسارات أيضاً
import moviepy.config as mpy_config
mpy_config.FFMPEG_BINARY      = os.environ["FFMPEG_BINARY"]
mpy_config.IMAGEMAGICK_BINARY = os.environ["IMAGEMAGICK_BINARY"]

# ← إضافة: التأكد من وجود مجلدات الإخراج
out_base = os.path.join(os.getcwd(), "outputs")
os.makedirs(out_base, exist_ok=True)
for sub in ("images", "audio"):
    os.makedirs(os.path.join(out_base, sub), exist_ok=True)

# ───────────────────────────────────────────────────────────────────────────────
# إعداد FastAPI
# ───────────────────────────────────────────────────────────────────────────────
app = FastAPI(title="ARABIAN AI SCHOOL Video Generator")

# خدمة ملفات static (css، صور، ...)
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE, "static")),
    name="static"
)

# إعداد Jinja2 للقوالب
templates = Jinja2Templates(directory=os.path.join(BASE, "templates"))

# خريطة الأصوات المتاحة
voice_options = {
    "هيثم": "UR972wNGq3zluze0LoIp",
    "يحيى": "QRq5hPRAKf5ZhSlTBH6r",
    "سارة": "jAAHNNqlbAX9iWjJPEtE",
    "مازن": "rPNcQ53R703tTmtue1AT",
    "أسماء": "qi4PkV9c01kb869Vh7Su"
}

# قائمة انتظار لكل متصل SSE
listeners: list[asyncio.Queue] = []


# ───────────────────────────────────────────────────────────────────────────────
# SSE ― Server-Sent Events endpoint
# ───────────────────────────────────────────────────────────────────────────────
@app.get("/stream")
def stream():
    async def event_generator():
        q: asyncio.Queue = asyncio.Queue()
        listeners.append(q)
        try:
            while True:
                msg = await q.get()
                yield f"data: {msg}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def broadcast(message: str):
    """أرسل رسالة لكل مستمع SSE."""
    for q in listeners:
        q.put_nowait(message)


# ───────────────────────────────────────────────────────────────────────────────
# صفحة البداية (عرض الواجهة)
# ───────────────────────────────────────────────────────────────────────────────
@app.get("/")
async def get_form(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "voice_options": list(voice_options.keys())
    })


# ───────────────────────────────────────────────────────────────────────────────
# نقطة النهاية لتوليد الفيديو (GET)
# ───────────────────────────────────────────────────────────────────────────────
@app.get("/generate")
async def generate_shorts(
    topic: str = Query(..., description="موضوع الفيديو"),
    voice_name: str = Query(..., description="اسم الصوت")
):
    topic = topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="topic cannot be empty")
    if voice_name not in voice_options:
        raise HTTPException(status_code=400, detail="invalid voice_name")

    voice_id = voice_options[voice_name]
    threading.Thread(
        target=run_pipeline,
        args=(topic, voice_id),
        daemon=True
    ).start()

    broadcast(f"▶️ بدأ إنشاء الفيديو للموضوع: «{topic}» بصوت «{voice_name}».")
    return {"status": "started"}


# ───────────────────────────────────────────────────────────────────────────────
# دالة البايبلاين نفسها مع بث الرسائل لكل مرحلة
# ───────────────────────────────────────────────────────────────────────────────
def run_pipeline(topic: str, voice_id: str):
    try:
        broadcast("1) توليد العنوان...")
        data = query(
            f"أعطِ 5 عناوين لفيديوهات يوتيوب شورتس تتعلق بالموضوع '{topic}' مفصولة بفواصل"
        )
        raw = data["candidates"][0]["content"]["parts"][0]["text"]
        title = [t.strip() for t in raw.replace("،", ",").split(",") if t.strip()][0]
        broadcast(f"2) العنوان: {title}")

        broadcast("3) توليد المحتوى...")
        data2 = query(
            f"اشرح عن هذا الموضوع {title} بإيجاز مدته دقيقة واحدة بدون تعليمات."
        )
        content = data2["candidates"][0]["content"]["parts"][0]["text"]
        broadcast("4) المحتوى مُنشأ.")

        broadcast("5) حفظ المحتوى وتقسيمه إلى سطور...")
        write_content(content)
        split_text_to_lines()
        broadcast("6) حفظ line_by_line.txt.")

        broadcast("7) توليد الصور...")
        image_main()
        broadcast("8) الصور جاهزة.")

        broadcast("9) توليد الصوت...")
        voice_main(voice_id=voice_id)
        broadcast("10) الصوت جاهز.")

        broadcast("11) إنشاء الفيديو...")
        video_main()
        broadcast("12) ✅ انتهى! تجد الملف في outputs/youtube_short.mp4")
    except Exception as e:
        broadcast(f"❌ خطأ أثناء المعالجة: {e}")


# ───────────────────────────────────────────────────────────────────────────────
# نقطة انطلاق التطبيق (لتشغيل exe بدون auto-reload)
# ───────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
