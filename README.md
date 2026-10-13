# PromptHero & OpenArt AI Pipeline Bot 🤖🎨

> Autonomous Telegram bot for parsing visual generative prompts, downloading video/image assets, and generating production-ready commercial case posts using OpenAI.

[![Python](https://img.shields.io/badge/Python-3.10+-3776ab.svg?logo=python&logoColor=white)](https://python.org)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991.svg?logo=openai&logoColor=white)](https://platform.openai.com)
[![Telegram](https://img.shields.io/badge/Telegram-Bot%20API-26a5e4.svg?logo=telegram&logoColor=white)](https://core.telegram.org/bots)

---

## Overview

**PromptHero AI Pipeline Bot** is a content generation and ingestion utility engineered for AI production studios, digital agencies, and generative video creators.

When supplied with a PromptHero or OpenArt URL, the bot:
1. **Scrapes Asset Metadata**: Parses raw generation prompt, negative prompt, seed, model parameters, and high-definition video/image sources.
2. **Rewrites via OpenAI**: Transforms raw generation tokens into structured, commercial agency posts (scene breakdown, refined prompt snippet, B2B call-to-action, tailored tags) under strict Telegram caption limits ($\le 900$ chars).
3. **Dispatches Media**: Automatically downloads and broadcasts video clips or images directly to target broadcast channels.

---

## System Architecture

```
[PromptHero / OpenArt URL]
            │
            ▼ (BeautifulSoup4 + Requests)
    [Scraper Engine]
      • MP4 / WEBM / JPG Stream
      • Raw Generation Prompt & Model Tags
            │
            ▼ (OpenAI Async Client)
    [LLM Rewriter Engine]
      • Scene Atmospheric Analysis
      • Clean Prompt Extraction (``` block)
      • Commercial Video Production CTA
            │
            ▼ (python-telegram-bot)
    [Target Channel Broadcast]
      (Video / Image + Formatted Rich Caption)
```

---

## Quick Start

### 1. Requirements

- Python 3.10+
- Telegram Bot Token (from `@BotFather`)
- OpenAI API Key

### 2. Installation

```bash
git clone https://github.com/butterflydrunk/prompthero-ai-bot.git
cd prompthero-ai-bot

pip install -r requirements.txt
```

### 3. Configuration

```bash
cp .env.example .env
```

Export the required environment variables:

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export OPENAI_API_KEY="your_openai_api_key"
export TARGET_CHANNEL_ID="@your_channel"
```

### 4. Running the Bot

```bash
python3 bot_2.py
```

---

## License

MIT License. Open for personal and commercial adaptation.
