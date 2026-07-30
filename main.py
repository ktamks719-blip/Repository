"""
============================================================
   بوت تيليجرام يبعث إحصائيات قناة يوتيوب يوميًا
============================================================

هذا الملف مقسّم لأقسام واضحة، كل قسم مكتوب عليه اسمه بالعربي
باش ما تتوه وانت تدور على شي. الأقسام بالترتيب:

  1. الإعدادات (البيانات السرية: توكن البوت، مفتاح يوتيوب...)
  2. جلب بيانات القناة من يوتيوب
  3. جلب بيانات آخر فيديو
  4. حفظ واسترجاع الإحصائيات القديمة (باش نحسب نمو اليوم)
  5. تجهيز شكل الرسالة
  6. إرسال الرسالة لتيليجرام
  7. التشغيل الرئيسي (الجزء اللي يشغّل كل شي بالترتيب)

ملاحظة: البيانات (التوكن والمفاتيح) ما هي مكتوبة هنا مباشرة،
تنقرا من "Secrets" بموقع GitHub لأسباب أمان. لو تشغله على
جهازك بدل GitHub، راجع قسم "الإعدادات" تحت.
"""

import os
import json
import sys
import requests
from datetime import datetime


# ============================================================
#   القسم 1: الإعدادات (البيانات السرية)
# ============================================================
#   هذي القيم الأربعة تنقرا تلقائيًا من GitHub Secrets.
#   ما تحتاج تلمس هالسطور — التعديل يصير بموقع GitHub نفسه:
#   Settings → Secrets and variables → Actions
# ------------------------------------------------------------
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")   # توكن بوت تيليجرام
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")       # آيدي المحادثة اللي بيوصلها التقرير
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")         # مفتاح YouTube Data API
YOUTUBE_CHANNEL_ID = os.environ.get("YOUTUBE_CHANNEL_ID")   # آيدي قناتك (يبدأ بـ UC)

# ملف يخزن فيه آخر إحصائية، باش نقدر نحسب "نمو اليوم" مقارنة بالأمس
HISTORY_FILE = os.path.join(os.path.dirname(__file__), "stats_history.json")

REQUIRED_VARS = {
    "TELEGRAM_BOT_TOKEN": TELEGRAM_BOT_TOKEN,
    "TELEGRAM_CHAT_ID": TELEGRAM_CHAT_ID,
    "YOUTUBE_API_KEY": YOUTUBE_API_KEY,
    "YOUTUBE_CHANNEL_ID": YOUTUBE_CHANNEL_ID,
}


def check_env():
    """يتأكد إن كل البيانات المطلوبة موجودة قبل ما يبلش"""
    missing = [k for k, v in REQUIRED_VARS.items() if not v]
    if missing:
        print(f"خطأ: المتغيرات التالية ناقصة: {', '.join(missing)}")
        print("تأكد إنك ضايف الأربعة Secrets بإعدادات GitHub.")
        sys.exit(1)


# ============================================================
#   القسم 2: جلب بيانات القناة من يوتيوب
# ============================================================


def get_channel_stats():
    """يجيب إحصائيات القناة + آخر فيديو نزل"""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "statistics,snippet,contentDetails",
        "id": YOUTUBE_CHANNEL_ID,
        "key": YOUTUBE_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("items"):
        raise ValueError("ما لقيتش القناة، تأكد من YOUTUBE_CHANNEL_ID")

    item = data["items"][0]
    stats = item["statistics"]
    snippet = item["snippet"]
    uploads_playlist_id = item["contentDetails"]["relatedPlaylists"]["uploads"]

    channel_info = {
        "title": snippet["title"],
        "subscribers": int(stats.get("subscriberCount", 0)),
        "views": int(stats.get("viewCount", 0)),
        "video_count": int(stats.get("videoCount", 0)),
    }

    # آخر فيديو نزل
    last_video = get_last_video(uploads_playlist_id)
    channel_info["last_video"] = last_video

    return channel_info


# ============================================================
#   القسم 3: جلب بيانات آخر فيديو نزل بالقناة
# ============================================================
def get_last_video(uploads_playlist_id):
    """يجيب آخر فيديو من قائمة تشغيل الرفعات + إحصائياته"""
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet",
        "playlistId": uploads_playlist_id,
        "maxResults": 1,
        "key": YOUTUBE_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if not data.get("items"):
        return None

    video_snippet = data["items"][0]["snippet"]
    video_id = video_snippet["resourceId"]["videoId"]

    # جيب إحصائيات الفيديو (مشاهدات/لايكات/تعليقات)
    stats_url = "https://www.googleapis.com/youtube/v3/videos"
    stats_params = {
        "part": "statistics",
        "id": video_id,
        "key": YOUTUBE_API_KEY,
    }
    stats_resp = requests.get(stats_url, params=stats_params, timeout=15)
    stats_resp.raise_for_status()
    stats_data = stats_resp.json()
    video_stats = stats_data["items"][0]["statistics"] if stats_data.get("items") else {}

    return {
        "title": video_snippet["title"],
        "video_id": video_id,
        "published_at": video_snippet["publishedAt"],
        "views": int(video_stats.get("viewCount", 0)),
        "likes": int(video_stats.get("likeCount", 0)),
        "comments": int(video_stats.get("commentCount", 0)),
    }


# ============================================================
#   القسم 4: حفظ واسترجاع الإحصائيات القديمة (نمو اليوم)
# ============================================================
def load_history():
    """يقرا آخر إحصائية محفوظة (يعني إحصائية أمس)"""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_history(data):
    """يحفظ الإحصائية الحالية باش تصير هي "أمس" بالتقرير الجاي"""
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def format_number(n):
    """يفرمت الأرقام بفواصل: 12345 → 12,345"""
    return f"{n:,}"


# ============================================================
#   القسم 5: تجهيز شكل الرسالة اللي بتنبعث لتيليجرام
# ============================================================
def build_message(stats, previous):
    today = datetime.now().strftime("%Y-%m-%d")

    subs_growth_line = ""
    if previous:
        diff = stats["subscribers"] - previous.get("subscribers", stats["subscribers"])
        sign = "+" if diff >= 0 else ""
        subs_growth_line = f"   └ نمو اليوم: {sign}{format_number(diff)}\n"

    views_growth_line = ""
    if previous:
        diff_views = stats["views"] - previous.get("views", stats["views"])
        sign = "+" if diff_views >= 0 else ""
        views_growth_line = f"   └ نمو اليوم: {sign}{format_number(diff_views)}\n"

    msg = (
        f"📊 *تقرير قناة {stats['title']}*\n"
        f"📅 {today}\n\n"
        f"👥 *المشتركين:* {format_number(stats['subscribers'])}\n"
        f"{subs_growth_line}"
        f"👁 *إجمالي المشاهدات:* {format_number(stats['views'])}\n"
        f"{views_growth_line}"
        f"🎬 *عدد الفيديوهات:* {format_number(stats['video_count'])}\n"
    )

    if stats.get("last_video"):
        v = stats["last_video"]
        msg += (
            f"\n🆕 *آخر فيديو:*\n"
            f"«{v['title']}»\n"
            f"   👁 {format_number(v['views'])}  "
            f"👍 {format_number(v['likes'])}  "
            f"💬 {format_number(v['comments'])}\n"
            f"   🔗 https://youtu.be/{v['video_id']}\n"
        )

    return msg


# ============================================================
#   القسم 6: إرسال الرسالة لتيليجرام
# ============================================================
def send_telegram_message(text):
    """يبعث الرسالة الجاهزة للبوت متاعك على تيليجرام"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, data=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


# ============================================================
#   القسم 7: التشغيل الرئيسي — هذا اللي يشغّل كل شي بالترتيب
# ============================================================
def main():
    # الخطوة أ: تأكد إن البيانات كلها موجودة
    check_env()

    # الخطوة ب: جيب إحصائيات القناة الحالية من يوتيوب
    print("جاري جلب إحصائيات القناة...")
    stats = get_channel_stats()

    # الخطوة ج: جيب إحصائيات أمس (لو موجودة) باش نحسب النمو
    history = load_history()
    previous = history.get("last_stats")

    # الخطوة د: جهّز نص الرسالة
    message = build_message(stats, previous)

    # الخطوة هـ: ابعث الرسالة لتيليجرام
    print("جاري إرسال الرسالة لتيليجرام...")
    send_telegram_message(message)

    # الخطوة و: احفظ إحصائيات اليوم باش تصير "أمس" بالتقرير الجاي
    history["last_stats"] = {
        "subscribers": stats["subscribers"],
        "views": stats["views"],
        "video_count": stats["video_count"],
        "date": datetime.now().strftime("%Y-%m-%d"),
    }
    save_history(history)

    print("تم الإرسال بنجاح ✅")


# نقطة انطلاق السكريبت — من هنا يبلش كل شي لما تشغّل الملف
if __name__ == "__main__":
    main()
