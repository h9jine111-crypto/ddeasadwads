import asyncio
import os
import qrcode
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from openai import OpenAI

# ========= НАСТРОЙКИ =========
API_ID = 32012812
API_HASH = "9fc5466fdbb972074e541c9b9fea2339"

# ВСТАВЬ СВОЙ ТОКЕН GITHUB (ghp_...)
GITHUB_TOKEN = "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"

# Используем мощную модель GPT-4o-mini (она бесплатна через Github Models)
client_ai = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key=GITHUB_TOKEN,
)


# ============================

class UserBot:
    def __init__(self):
        self.session_file = "session.txt"
        session_str = ""
        if os.path.exists(self.session_file):
            with open(self.session_file, "r") as f: session_str = f.read().strip()

        self.client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        self.queue = asyncio.Queue()

    async def get_ai_reply(self, text):
        try:
            response = client_ai.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "ты обычный парень в тг. пиши мелко, коротко, без заглавных. если бесят — хами. ты живой человек."
                    },
                    {
                        "role": "user",
                        "content": text,
                    }
                ],
                model="gpt-4o-mini",  # Самая быстрая и стабильная
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Ошибка: {e}")
            return "бля, чет я приуныл. давай позже."

    async def handle(self, event):
        chat_id = event.chat_id
        await self.client.send_read_acknowledge(chat_id)

        user_text = event.message.text or ""
        if event.message.photo: user_text += " [прислал фото]"

        if not user_text: return

        reply = await self.get_ai_reply(user_text)

        async with self.client.action(chat_id, 'typing'):
            await asyncio.sleep(1)
            await event.reply(reply.lower())

    async def start(self):
        await self.client.connect()
        if not await self.client.is_user_authorized():
            qr = await self.client.qr_login()
            qrcode.QRCode().add_data(qr.url).print_ascii(invert=True)
            await qr.wait()
            with open(self.session_file, "w") as f: f.write(self.client.session.save())

        print("--- Бот на Github Models запущен! ---")

        @self.client.on(events.NewMessage(incoming=True))
        async def handler(event):
            if event.is_private or event.mentioned:
                await self.queue.put(event)

        while True:
            ev = await self.queue.get()
            try:
                await self.handle(ev)
            except Exception as e:
                print(f"Runtime error: {e}")
            self.queue.task_done()


if __name__ == "__main__":
    asyncio.run(UserBot().start())