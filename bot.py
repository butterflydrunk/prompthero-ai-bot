import os
import requests
from bs4 import BeautifulSoup
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text or "prompthero.com/prompt" not in text:
        return
    
    # Извлечение URL
    url = [word for word in text.split() if "prompthero.com/prompt" in word][0]
    
    try:
        await update.message.reply_text("⏳ Обрабатываю ссылку...")
        
        # Скачиваем страницу
        response = requests.get(url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем теги
        video_tag = soup.find('meta', property='og:video')
        desc_tag = soup.find('meta', property='og:description')
        
        if not video_tag or not desc_tag:
            await update.message.reply_text("❌ Не удалось найти видео или промпт на странице.")
            return
            
        video_url = video_tag['content']
        description = desc_tag['content']
        
        # Очистка промпта
        import re
        match = re.search(r'prompt · "(.*?)"\. Create amazing', description, re.DOTALL)
        if match:
            clean_prompt = match.group(1)
        else:
            # Fallback
            clean_prompt = re.sub(r'^.*?prompt · "', '', description)
            clean_prompt = re.sub(r'"\. Create amazing.*$', '', clean_prompt)
            
        # Скачиваем видео во временный файл
        video_resp = requests.get(video_url, stream=True)
        video_resp.raise_for_status()
        
        video_path = "temp_video.mp4"
        with open(video_path, 'wb') as f:
            for chunk in video_resp.iter_content(chunk_size=8192):
                f.write(chunk)
                
        # Отправляем видео с промптом
        with open(video_path, 'rb') as video_file:
            await context.bot.send_video(
                chat_id=update.message.chat_id,
                video=video_file,
                caption=f"**Промпт:**\\n`{clean_prompt}`",
                parse_mode="MarkdownV2"
            )
            
        # Удаляем временный файл
        os.remove(video_path)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")

def main():
    if not TOKEN:
        print("Set TELEGRAM_BOT_TOKEN environment variable!")
        return
        
    application = Application.builder().token(TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Бот запущен. Ожидание ссылок с PromptHero...")
    application.run_polling()

if __name__ == '__main__':
    main()
