import os
import sys
from PIL import Image as PilImage
# Compatibility shim: make ANTIALIAS an alias for Resampling.LANCZOS if needed
if not hasattr(PilImage, "ANTIALIAS"):
    PilImage.ANTIALIAS = PilImage.Resampling.LANCZOS

from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
    TextClip,
    ColorClip,
    vfx
)

# مسار الخط الخارجي (font.ttf) بجانب ملف exe
font_path = os.path.join(os.getcwd(), "font.ttf")
font = font_path  # يمكن أيضاً استخدام اسم الخط إذا كان مثبتاً

def zoom_in_image(t):
    return 1.5 + (0.1 * t)

def create_text(text, duration):
    """
    إنشاء نص مع التفاف تلقائي بناءً على العرض المحدد.
    """
    text_clip = (
        TextClip(
            txt=text,
            fontsize=80,
            color="white",
            font=font,
            method="caption",
            size=(1000, None),
            align="center"
        )
        .set_duration(duration)
        .set_position(("center", 1450))
    )
    return text_clip

def create_image_clip(image, duration):
    """
    إنشاء مقطع صورة مع تأثير تكبير مستمر.
    """
    image_clip = (
        ImageClip(image)
        .resize(width=1280)  # يستخدم الآن ANTIALIAS خلف الكواليس
        .set_duration(duration + 0.5)
        .set_position(("center", "center"))
    )
    image_clip = image_clip.fx(vfx.resize, zoom_in_image)
    return image_clip

def video_main():
    # قراءة النص المجزأ سطرًا سطرًا
    with open("./outputs/line_by_line.txt", "r", encoding="utf-8") as f:
        content = f.read().split("\n")

    clips = []
    part = 0
    for text in content:
        if text.strip() == "":
            break

        mp3_path = f'./outputs/audio/part{part}.mp3'
        wav_path = f'./outputs/audio/part{part}.wav'

        # اختيار ملف الصوت إن وُجد
        if os.path.exists(mp3_path):
            audioclip = AudioFileClip(mp3_path)
            duration = audioclip.duration
        elif os.path.exists(wav_path):
            audioclip = AudioFileClip(wav_path)
            duration = audioclip.duration
        else:
            print(f"تحذير: لم يتم العثور على ملف الصوت للمقطع part{part}. سيتم استخدام صوت صامت لمدة 5 ثوانٍ.")
            duration = 5
            from moviepy.editor import AudioClip
            audioclip = AudioClip(lambda t: 0, duration=duration)

        # اختيار الصورة إن وُجدت
        image_file = f"./outputs/images/part{part}.jpg"
        if os.path.exists(image_file):
            image_clip = create_image_clip(image_file, duration)
        else:
            print(f"تحذير: لم يتم العثور على الصورة للمقطع part{part}. سيتم استخدام خلفية سوداء.")
            image_clip = ColorClip((1080, 1920), color=(0, 0, 0)).set_duration(duration)

        text_clip = create_text(text, duration)
        segment_bg = ColorClip((1080, 1920), color=(0, 0, 0)).set_duration(duration)

        video_segment = CompositeVideoClip([segment_bg, image_clip, text_clip]).set_audio(audioclip)
        clips.append(video_segment)
        part += 1

    if not clips:
        print("لا توجد مقاطع فيديو لإنشائها.")
        return

    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile("./outputs/youtube_short.mp4", fps=30, audio=True)

if __name__ == "__main__":
    video_main()
