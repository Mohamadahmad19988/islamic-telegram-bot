# 🌙 Islamic Telegram Bot

بوت تيليجرام إسلامي ينشر تلقائياً في قناة **@noraalas**

## ما يفعله البوت

| المهمة | كل |
|---|---|
| 📿 منشور إسلامي بالذكاء الاصطناعي | ساعة |
| 📰 منشورات المدونتين | ساعتين |
| 📖 آية قرآنية مع رابط تلاوة | 6 ساعات |
| 🏓 Self-ping (يمنع النوم على Render) | 10 دقائق |

## النشر على Render.com مجاناً

### 1. متطلبات
- حساب [GitHub](https://github.com)
- حساب [Render.com](https://render.com) (مجاني)
- توكن GitHub: [أنشئ واحداً هنا](https://github.com/settings/tokens/new?scopes=repo&description=islamic-bot)

### 2. رفع الكود على GitHub

```bash
bash setup.sh YOUR_GITHUB_TOKEN YOUR_GITHUB_USERNAME
```

مثال:
```bash
bash setup.sh ghp_xxxxxxxxxxxx ahmed123
```

### 3. ربط المستودع بـ Render

1. اذهب إلى [render.com/new](https://render.com/new) ← **Web Service**
2. اختر مستودع `islamic-telegram-bot`
3. اضبط الإعدادات:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python3 bot.py`
   - **Plan:** Free
4. أضف متغيرات البيئة:

| المتغير | القيمة |
|---|---|
| `TELEGRAM_BOT_TOKEN` | توكن البوت |
| `TELEGRAM_CHANNEL_ID` | `@noraalas` |
| `GEMINI_API_KEY` | مفتاح Gemini |

5. اضغط **Deploy** ✅

### 4. تفعيل النشر التلقائي عند التحديث (اختياري)

بعد النشر الأول، انسخ **Deploy Hook URL** من Render ثم:
1. اذهب إلى GitHub → مستودعك → **Settings** → **Secrets** → **Actions**
2. أضف secret باسم `RENDER_DEPLOY_HOOK` والقيمة هي رابط الـ hook

الآن كل `git push` سينشر تلقائياً! 🚀

## متغيرات البيئة

| المتغير | الوصف | مطلوب |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | توكن البوت من @BotFather | ✅ |
| `TELEGRAM_CHANNEL_ID` | معرف القناة مثل `@noraalas` | ✅ |
| `GEMINI_API_KEY` | مفتاح Gemini AI | ✅ |
| `RENDER_EXTERNAL_URL` | يُضبط تلقائياً من Render | ⚙️ |
| `PORT` | يُضبط تلقائياً من Render | ⚙️ |

## المدونات المتابَعة

- [alqoranalkareemm.blogspot.com](https://alqoranalkareemm.blogspot.com)
- [islam3256.blogspot.com](https://islam3256.blogspot.com)
