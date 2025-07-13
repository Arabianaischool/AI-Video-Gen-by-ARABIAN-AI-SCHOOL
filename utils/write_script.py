import re
from utils.gemini import query

def get_title():
    topic = input("اسم الموضوع: ")
    while True:
        print("جارٍ توليد العناوين...")
        data = query(f"أعطِ 5 عناوين لفيديوهات يوتيوب شورتس تتعلق بالموضوع '{topic}' مفصولة بفواصل")
        if data:
            # نقسم النص باستخدام الفاصلة الإنجليزية أو العربية
            titles = re.split(r'[,،]', data["candidates"][0]["content"]["parts"][0]["text"])
            # إزالة الفراغات الزائدة والتأكد من أن كل عنوان غير فارغ
            titles = [t.strip() for t in titles if t.strip()]
            # إضافة الموضوع كخيار إضافي إذا كان ذلك مرغوباً
            titles.append(topic)
            for i in range(len(titles)):
                print(str(i) + " : " + titles[i])
            choice = int(input("أدخل خيارك من العناوين: "))
            if choice == -1:
                continue
            print("تم الحصول على العنوان!")
            with open("./outputs/title.txt", "w", encoding='utf-8') as f:
                f.write(titles[choice])
            return titles[choice]
        else:
            print("خطأ فادح :(")
            exit()

def get_content(title):
    while True:
        data = query(f"اشرح عن هذا الموضوع {title} بإيجاز لمدة دقيقة واحدة. كن مبدعًا.")
        if data:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            print(content)
            satisfied = input("هل يناسبك؟ (نعم/لا): ")
            if satisfied != "لا":
                return content
            else:
                continue
        else:
            print("خطأ فادح :(")
            exit()

def write_content(content):
    with open("./outputs/text.txt", "w", encoding='utf-8') as f:
        f.write(content)

def split_text_to_lines():
    with open("./outputs/text.txt", "r", encoding="utf-8") as f:
        text_input = f.read()
    text_input = text_input.replace(':',' ').replace('-',' ').replace('_'," ").replace('!','.').replace('*',"").replace(',','.')
    with open("./outputs/line_by_line.txt", "w", encoding="utf-8") as f_out:
        for line in text_input.strip().split("\n"):
            for sentence in line.split('.'):
                sentence = sentence.strip()
                if sentence:
                    f_out.write(sentence + "\n")

if __name__ == "__main__":
    write_content(get_content(get_title()))
