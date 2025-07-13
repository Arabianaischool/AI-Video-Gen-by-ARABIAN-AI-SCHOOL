import requests
import sys 
import time

try:
    secret = open("gemini_secret.txt")
except:
    print("لم يتم العثور على مفتاح GEMINI. الرجاء تسمية الملف gemini_secret.txt")
    print("قم بلصق المفتاح في الملف النصي")
    print("سيتم الإغلاق خلال 5 ثوانٍ")
    time.sleep(5)
    sys.exit()
API_KEY = secret.read().strip()
if API_KEY == "":
    print("مفتاح GEMINI فارغ")
    print("سيتم الإغلاق خلال 5 ثوانٍ")
    time.sleep(5)
    sys.exit()

URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=" + API_KEY

def query(text):
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": text}
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(URL, json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data
    else:
        print(f"خطأ: {response.status_code}")
        print(response.text)
