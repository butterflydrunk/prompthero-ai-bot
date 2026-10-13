import os
import re
import json
import asyncio
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openai import AsyncOpenAI

# Проверка токенов
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID")

if not TELEGRAM_TOKEN or not OPENAI_API_KEY or not TARGET_CHANNEL_ID:
    print("❌ ВАЖНО: Установите переменные окружения TELEGRAM_BOT_TOKEN, OPENAI_API_KEY и TARGET_CHANNEL_ID")
    exit(1)

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Тот самый экспертный системный промпт (Вариант 2)
SYSTEM_PROMPT = """Ты — профессиональный AI-инженер и владелец премиального агентства AI-видеопродакшена. Твоя задача: переписать сырой концепт для видеогенерации в экспертный Telegram-пост.

Структура поста:

Лаконичный и стильный заголовок. Он должен отражать коммерческую задачу или нишу (например, для автосервиса, ресторана и т.д.). ВАЖНО: Никаких знаков '#' или '###' в заголовке!

Разбор сцены: кратко опиши атмосферу и кинематографический эффект. Обязательно укажи, что это лишь "база", которую нужно докрутить на монтаже (упомяни автосубтитры, динамичную склейку или эффекты), чтобы показать сложный технический процесс.

Промпт в блоке кода (```): Не копируй оригинальный текст 1-в-1. Сделай из него короткую, выверенную выжимку на английском (максимум 2-3 предложения), добавив кинематографические теги (освещение, стиль). ВАЖНО: Не ставь кавычки вокруг промпта!

Call-to-Action (CTA) для бизнеса: напиши просто фразу "Закажите профессиональный коммерческий UGC-ролик под ключ." (без ссылок-заглушек и без призывов для креаторов!).

2-3 целевых хештега.

Ограничения и Тон:

Тон: сдержанный, экспертный, уважительный. Никакой воды.

Эмодзи: строгий минимум (3-4 на весь пост, используй только как маркеры списков или логические акценты).

Лимиты: КРИТИЧЕСКИ ВАЖНО — длина всего поста строго до 900 символов (лимит Telegram для постов с медиа). Общее количество предложений не должно превышать 7-8."""

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text or not ("prompthero.com/prompt" in text or "openart.ai" in text):
        return
    
    # Извлечение URL
    url_match = re.search(r'(https?://[^\s]+)', text)
    if not url_match:
        return
    url = url_match.group(1)
    
    status_msg = await update.message.reply_text("⏳ Анализирую страницу...")
    
    try:
        # 1. Fetch HTML
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        media_url = ""
        media_type = 'none'
        clean_prompt = ""
        
        if "openart.ai" in url:
            script_match = re.search(r'<script id="__NEXT_DATA__".*?>(.*?)</script>', response.text, re.DOTALL)
            if script_match:
                data = json.loads(script_match.group(1))
                story = data.get('props', {}).get('pageProps', {}).get('initShareStory', {})
                
                vid_url = story.get('last_export_url')
                img_url = story.get('last_export_thumbnail_url')
                
                if vid_url and str(vid_url).endswith('.mp4'):
                    media_url = vid_url
                    media_type = 'video'
                elif img_url:
                    media_url = img_url
                    media_type = 'photo'
                
                inputs = story.get('category_inputs', {})
                clean_prompt = inputs.get('script_content', '') or story.get('title', '')
        else:
            # 2. HTML Extract PromptHero
            soup = BeautifulSoup(response.text, 'html.parser')
            video_tag = soup.find('meta', property='og:video')
            image_tag = soup.find('meta', property='og:image')
            desc_tag = soup.find('meta', property='og:description')
            
            video_url = video_tag['content'] if video_tag else None
            image_url = image_tag['content'] if image_tag else None
            description = desc_tag['content'] if desc_tag else ""
            
            # 3. Clean Prompt (Full text extraction from HTML div)
            prompt_div = soup.find('div', class_=lambda x: x and 'bg-muted/50' in x and 'rounded-lg' in x)
            if prompt_div:
                clean_prompt = prompt_div.get_text(separator=' ', strip=True)
                clean_prompt = clean_prompt.replace('See less', '').replace('Recent', '').strip()
            else:
                clean_prompt = description # Fallback
                
            # 4. Has Media? (Логика из n8n)
            if video_url:
                media_url = video_url
                media_type = 'video'
            elif image_url:
                media_url = image_url
                media_type = 'photo'
            
        if media_type == 'none':
            await status_msg.edit_text("⚠️ Ошибка парсинга: на странице не найдено медиа. Возможно, сработала защита Cloudflare или ссылка содержит нестандартный контент.")
            return

        await status_msg.edit_text("🧠 Генерирую пост через OpenAI...")

        # 5. AI SMM Manager (OpenAI API)
        chat_completion = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": clean_prompt}
            ]
        )
        ai_post = chat_completion.choices[0].message.content
        
        await status_msg.edit_text("📥 Скачиваю медиа...")

        # 6. Download Media
        media_resp = requests.get(media_url, headers=HEADERS, stream=True, timeout=30)
        media_resp.raise_for_status()
        
        ext = "mp4" if media_type == 'video' else "jpg"
        temp_file = f"temp_media_{update.message.chat_id}.{ext}"
        
        with open(temp_file, 'wb') as f:
            for chunk in media_resp.iter_content(chunk_size=8192):
                f.write(chunk)
                
        await status_msg.edit_text("🚀 Отправляю результат...")
        
        # 7. Switch Media Type & Send to Channel
        with open(temp_file, 'rb') as f_media:
            if len(ai_post) <= 1024:
                if media_type == 'video':
                    await context.bot.send_video(chat_id=TARGET_CHANNEL_ID, video=f_media, caption=ai_post, parse_mode=None)
                else:
                    await context.bot.send_photo(chat_id=TARGET_CHANNEL_ID, photo=f_media, caption=ai_post, parse_mode=None)
            else:
                # Если текст длиннее лимита, отправляем медиа без подписи, а текст — ответом на это медиа
                if media_type == 'video':
                    msg = await context.bot.send_video(chat_id=TARGET_CHANNEL_ID, video=f_media)
                else:
                    msg = await context.bot.send_photo(chat_id=TARGET_CHANNEL_ID, photo=f_media)
                await context.bot.send_message(chat_id=TARGET_CHANNEL_ID, text=ai_post, reply_to_message_id=msg.message_id, parse_mode=None)
                
        # Очистка
        os.remove(temp_file)
        await status_msg.edit_text("✅ Пост успешно опубликован в канале!")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Системная ошибка: {str(e)}")

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Бот запущен! Ожидание ссылок с PromptHero...")
    application.run_polling()

if __name__ == '__main__':
    main()
