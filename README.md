# بوت إحصائيات يوتيوب اليومي على تيليجرام

يبعث كل يوم رسالة فيها: المشتركين، إجمالي المشاهدات، عدد الفيديوهات،
نمو المشتركين والمشاهدات مقارنة بالأمس، وآخر فيديو نزل مع إحصائياته.

يشتغل مجانًا وتلقائيًا عبر **GitHub Actions** — ما تحتاج سيرفر ولا يبقى جهازك شغال.

---

## الخطوات

### 1) جيب البيانات المطلوبة

| المتغير | من وين تجيبه |
|---|---|
| `TELEGRAM_BOT_TOKEN` | من [@BotFather](https://t.me/BotFather) في تيليجرام: `/newbot` |
| `TELEGRAM_CHAT_ID` | ابعث رسالة للبوت، بعدها افتح `https://api.telegram.org/bot<TOKEN>/getUpdates` ودور على `chat.id` |
| `YOUTUBE_API_KEY` | عندك جاهز من Google Cloud Console |
| `YOUTUBE_CHANNEL_ID` | من يوتيوب: Settings → Advanced settings (يبدأ بـ `UC`) |

### 2) ارفع المشروع على GitHub
- اعمل حساب GitHub (لو ما عندكش)
- اعمل Repository جديد (خليه **Private** أفضل)
- ارفع كل ملفات هذا المجلد لهناك

### 3) خزّن البيانات كـ Secrets (مش داخل الكود)
في الـ Repository:
`Settings → Secrets and variables → Actions → New repository secret`

ضيف الأربعة دول واحد واحد:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `YOUTUBE_API_KEY`
- `YOUTUBE_CHANNEL_ID`

### 4) جرّب التشغيل يدويًا
روح لتبويب **Actions** في الـ Repository → اختر workflow اسمه
**Daily YouTube Stats Report** → دوس **Run workflow**.

لو كل شي مضبوط، بتوصلك رسالة في تيليجرام خلال ثواني.

### 5) خلاص، صار تلقائي
السكريبت مبرمج يشتغل كل يوم الساعة **9 صباحًا بتوقيت ليبيا** تلقائيًا
(بدون ما تسوي شي). تقدر تغيّر التوقيت من ملف
`.github/workflows/daily-report.yml` بتعديل سطر الـ cron.

> ملاحظة: أوقات تشغيل GitHub Actions المجدولة ممكن تتأخر بضع دقائق
> عن الوقت المحدد بالضبط (طبيعي في الخطة المجانية).

---

## تشغيله على جهازك بدل GitHub (اختياري)

```bash
pip install -r requirements.txt

export TELEGRAM_BOT_TOKEN="xxxx"
export TELEGRAM_CHAT_ID="xxxx"
export YOUTUBE_API_KEY="xxxx"
export YOUTUBE_CHANNEL_ID="UCxxxx"

python main.py
```

باش يبعث كل يوم تلقائي من جهازك، لازم تضيفه لـ Task Scheduler (ويندوز)
أو cron (لينكس/ماك) يشغّله مرة كل يوم.

---

## تعديل شكل الرسالة

كل تنسيق الرسالة موجود في دالة build_message() داخل main.py —
تقدر تضيف أو تشيل أي سطر بسهولة.
