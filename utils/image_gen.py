import os
import requests
from PIL import Image
from io import BytesIO
from tqdm import tqdm
from urllib.parse import quote_plus

# تحتاج أولاً لتثبيت مكتبة الترجمة:
# pip install googletrans==4.0.0-rc1

from googletrans import Translator

def image_main():
    # 1) مسار مجلد الإخراج
    out_dir = os.path.join(os.getcwd(), "outputs", "images")
    os.makedirs(out_dir, exist_ok=True)

    # 2) قراءة line_by_line.txt
    line_file = os.path.join(os.getcwd(), "outputs", "line_by_line.txt")
    with open(line_file, "r", encoding="utf-8") as f:
        prompts = [line.strip() for line in f if line.strip()]

    # 3) إعداد المترجم
    translator = Translator()

    # 4) جلب وحفظ الصور
    for part, prompt in enumerate(tqdm(prompts, desc="Downloading images")):
        try:
            # ترجم من العربية للإنجليزية
            translated = translator.translate(prompt, src="ar", dest="en").text
            # شيفرة URL
            encoded = quote_plus(translated)
            url = f"https://image.pollinations.ai/prompt/{encoded}"

            resp = requests.get(url, timeout=30)
            resp.raise_for_status()

            img = Image.open(BytesIO(resp.content)).convert("RGB")

            out_path = os.path.join(out_dir, f"part{part}.jpg")
            img.save(out_path, format="JPEG")

        except Exception as e:
            print(f"خطأ في تحميل أو حفظ الصورة [{prompt}]: {e}")

if __name__ == "__main__":
    image_main()
