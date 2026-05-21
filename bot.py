import os
import json
import time
import random
import logging
import threading
import requests
import feedparser
import schedule
from google import genai
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from islamic_posts import POSTS as FALLBACK_POSTS

# ─── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── Config (from environment variables) ───────────────────────────────────
TELEGRAM_BOT_TOKEN  = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID", "@noraalas")
GEMINI_API_KEY      = os.environ.get("GEMINI_API_KEY", "")

if not TELEGRAM_BOT_TOKEN:
    raise SystemExit("❌  TELEGRAM_BOT_TOKEN is not set.")
if not GEMINI_API_KEY:
    raise SystemExit("❌  GEMINI_API_KEY is not set.")

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
QURAN_API    = "https://api.quran.com/api/v4"
PUBLISHED_CACHE = Path(__file__).parent / "published_posts.json"

# ─── Gemini setup ──────────────────────────────────────────────────────────
gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ════════════════════════════════════════════════════════════════════════════
# TELEGRAM HELPERS
# ════════════════════════════════════════════════════════════════════════════

def send_message(text: str, parse_mode: str = "HTML") -> bool:
    """Send a message to the Telegram channel."""
    if not text or not text.strip():
        log.error("send_message called with empty text — skipped.")
        return False
    try:
        resp = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": TELEGRAM_CHANNEL_ID, "text": text, "parse_mode": parse_mode},
            timeout=30,
        )
        data = resp.json()
        if data.get("ok"):
            log.info("✅  Message sent successfully.")
            return True
        log.error("Telegram error: %s", data.get("description"))
        return False
    except Exception as exc:
        log.error("send_message exception: %s", exc)
        return False


# ════════════════════════════════════════════════════════════════════════════
# 1. ISLAMIC AI POST  (every hour)
# ════════════════════════════════════════════════════════════════════════════

ISLAMIC_TOPICS = [
    "آية قرآنية مع تفسيرها",
    "حديث نبوي شريف مع شرحه",
    "دعاء مأثور من السنة النبوية",
    "فضل من فضائل الأعمال الصالحة",
    "قصة من قصص الأنبياء والمرسلين",
    "حكمة إسلامية وموعظة حسنة",
    "ذكر من أذكار الصباح أو المساء",
    "فقرة عن أخلاق المسلم",
    "تذكير بأحد أركان الإسلام الخمسة",
    "معلومة عن سيرة النبي محمد ﷺ",
]


def generate_islamic_post() -> str:
    topic = random.choice(ISLAMIC_TOPICS)
    prompt = f"""أنت بوت إسلامي يخدم المسلمين. اكتب منشوراً إسلامياً جميلاً ومفيداً باللغة العربية عن موضوع: "{topic}".

الشروط:
- اكتب المنشور بأسلوب راقٍ ومؤثر
- ابدأ بالبسملة أو تحية إسلامية
- إذا ذكرت آية قرآنية، ضعها بين قوسين مزدوجين
- إذا ذكرت حديثاً، اذكر راويه
- اختم بدعاء قصير أو صلاة على النبي
- لا تكتب أكثر من 300 كلمة
- استخدم الرموز التعبيرية المناسبة (مثل 🌙 ⭐ 📖 🤲 ☪️)

اكتب المنشور مباشرة دون مقدمات."""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
        )
        text = response.text.strip()
        if text:
            log.info("Generated AI Islamic post — topic: %s (%d chars)", topic, len(text))
            return text
        raise ValueError("Empty response from Gemini")
    except Exception as exc:
        log.warning("Gemini unavailable (%s) — using fallback post library.", exc.__class__.__name__)
        post = random.choice(FALLBACK_POSTS)
        log.info("Using fallback post (%d chars)", len(post))
        return post


def job_islamic_post():
    log.info("⏰  [SCHEDULER] Running Islamic post job...")
    try:
        content = generate_islamic_post()
        send_message(content)
    except Exception as exc:
        log.error("Islamic post job failed: %s", exc)


# ════════════════════════════════════════════════════════════════════════════
# 2. BLOG PUBLISHER  (every 2 hours)
# ════════════════════════════════════════════════════════════════════════════

BLOGS = [
    {"name": "القرآن الكريم",  "url": "https://alqoranalkareemm.blogspot.com/feeds/posts/default?alt=rss"},
    {"name": "الإسلام",         "url": "https://islam3256.blogspot.com/feeds/posts/default?alt=rss"},
]


def load_published() -> set:
    if PUBLISHED_CACHE.exists():
        try:
            return set(json.loads(PUBLISHED_CACHE.read_text()))
        except Exception:
            pass
    return set()


def save_published(ids: set):
    PUBLISHED_CACHE.write_text(json.dumps(list(ids)))


def clean_html(raw: str) -> str:
    import re
    text = re.sub(r"<[^>]+>", "", raw)
    for entity, char in [("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"')]:
        text = text.replace(entity, char)
    return text.strip()


def format_blog_message(blog_name: str, title: str, link: str, summary: str) -> str:
    snippet = clean_html(summary)[:300]
    return (
        f"📰 <b>{blog_name}</b>\n\n"
        f"<b>{title}</b>\n\n"
        + (f"{snippet}...\n\n" if snippet else "")
        + f'🔗 <a href="{link}">اقرأ المزيد</a>\n\n'
        "بسم الله الرحمن الرحيم 🌙"
    )


def job_publish_blogs():
    log.info("⏰  [SCHEDULER] Running blog publisher job...")
    published = load_published()
    new_count = 0

    for blog in BLOGS:
        try:
            feed = feedparser.parse(blog["url"])
            for entry in feed.entries[:3]:
                post_id = entry.get("id") or entry.get("link", "")
                if not post_id or post_id in published:
                    continue

                title   = entry.get("title", "بدون عنوان")
                link    = entry.get("link", "")
                summary = entry.get("summary") or entry.get("content", [{}])[0].get("value", "")

                msg = format_blog_message(blog["name"], title, link, summary)
                if send_message(msg):
                    published.add(post_id)
                    save_published(published)
                    new_count += 1
                    log.info("Published blog post: [%s] %s", blog["name"], title)
                    time.sleep(2)
        except Exception as exc:
            log.error("Blog job failed for %s: %s", blog["name"], exc)

    log.info("Blog job done — %d new post(s) published.", new_count)


# ════════════════════════════════════════════════════════════════════════════
# 3. QURAN VERSE WITH AUDIO  (every 6 hours)
# ════════════════════════════════════════════════════════════════════════════

# Curated surahs with their verse counts
SURAHS = [
    (1, "الفاتحة", 7),    (2, "البقرة", 286),   (3, "آل عمران", 200),
    (4, "النساء", 176),   (5, "المائدة", 120),   (6, "الأنعام", 165),
    (12, "يوسف", 111),    (17, "الإسراء", 111),  (18, "الكهف", 110),
    (19, "مريم", 98),     (20, "طه", 135),       (23, "المؤمنون", 118),
    (24, "النور", 64),    (36, "يس", 83),         (39, "الزمر", 75),
    (40, "غافر", 85),     (55, "الرحمن", 78),    (56, "الواقعة", 96),
    (67, "الملك", 30),    (73, "المزمل", 20),    (76, "الانسان", 31),
    (87, "الأعلى", 19),   (89, "الفجر", 30),     (93, "الضحى", 11),
    (94, "الشرح", 8),     (97, "القدر", 5),       (99, "الزلزلة", 8),
    (103, "العصر", 3),    (108, "الكوثر", 3),    (110, "النصر", 3),
    (112, "الإخلاص", 4),  (113, "الفلق", 5),     (114, "الناس", 6),
]


def fetch_quran_verse() -> dict:
    surah_id, surah_name, verses_count = random.choice(SURAHS)
    ayah = random.randint(1, verses_count)
    verse_key = f"{surah_id}:{ayah}"

    url = (
        f"{QURAN_API}/verses/by_key/{verse_key}"
        "?language=ar&fields=text_uthmani&translations=131&audio=7"
    )
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    verse = data["verse"]
    text  = verse["text_uthmani"]

    raw_translation = ""
    if verse.get("translations"):
        import re
        raw_translation = re.sub(r"<[^>]+>", "", verse["translations"][0].get("text", ""))[:400]

    audio_url = f"https://verses.quran.com/{verse['audio']['url']}"
    page_url  = f"https://quran.com/{surah_id}?startingVerse={ayah}"

    log.info("Fetched Quran verse: %s — %s", verse_key, surah_name)
    return {
        "verse_key": verse_key,
        "surah_name": surah_name,
        "ayah": ayah,
        "text": text,
        "translation": raw_translation,
        "audio_url": audio_url,
        "page_url": page_url,
    }


def format_quran_message(v: dict) -> str:
    return (
        "📖 <b>آية من القرآن الكريم</b>\n\n"
        f"سورة <b>{v['surah_name']}</b> — الآية {v['ayah']}\n\n"
        f"<b>﴿ {v['text']} ﴾</b>\n\n"
        + (f"📝 <i>{v['translation']}</i>\n\n" if v["translation"] else "")
        + f'🎧 <a href="{v["audio_url"]}">استمع للتلاوة</a>  |  '
        f'🔗 <a href="{v["page_url"]}">اقرأ في Quran.com</a>\n\n'
        "اللهم اجعل القرآن ربيع قلوبنا 🌙"
    )


def job_quran_verse():
    log.info("⏰  [SCHEDULER] Running Quran verse job...")
    try:
        verse = fetch_quran_verse()
        msg   = format_quran_message(verse)
        send_message(msg)
    except Exception as exc:
        log.error("Quran verse job failed: %s", exc)


# ════════════════════════════════════════════════════════════════════════════
# SCHEDULER SETUP
# ════════════════════════════════════════════════════════════════════════════

def job_self_ping():
    """Ping this service every 10 minutes to prevent Render free tier sleep."""
    render_url = os.environ.get("RENDER_EXTERNAL_URL", "")
    if not render_url:
        return
    try:
        requests.get(render_url, timeout=10)
        log.info("🏓  Self-ping OK → %s", render_url)
    except Exception as exc:
        log.warning("Self-ping failed: %s", exc)


def setup_scheduler():
    schedule.every(1).hours.do(job_islamic_post)
    schedule.every(2).hours.do(job_publish_blogs)
    schedule.every(6).hours.do(job_quran_verse)
    schedule.every(10).minutes.do(job_self_ping)

    log.info("Scheduler configured:")
    log.info("  📿 Islamic post   → every 1 hour")
    log.info("  📰 Blog publisher → every 2 hours")
    log.info("  📖 Quran verse    → every 6 hours")
    log.info("  🏓 Self-ping      → every 10 minutes (keeps Render awake)")


def run_all_once():
    """Run all jobs immediately on startup."""
    log.info("▶️  Running all jobs once on startup...")
    job_islamic_post()
    job_publish_blogs()
    job_quran_verse()


# ════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK SERVER  (required by Render.com free tier)
# ════════════════════════════════════════════════════════════════════════════

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"ok","bot":"Islamic Telegram Bot","running":true}')

    def log_message(self, *args):
        pass  # silence access logs


def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    log.info("Health check server listening on port %d", port)
    server.serve_forever()


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("🤖  Islamic Telegram Bot starting...")
    log.info("    Channel : %s", TELEGRAM_CHANNEL_ID)
    log.info("    Time    : %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    health_thread = threading.Thread(target=start_health_server, daemon=True)
    health_thread.start()

    setup_scheduler()
    run_all_once()

    log.info("✅  Bot is running. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        time.sleep(30)
