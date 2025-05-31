import telebot
from flask import current_app
from datetime import datetime


class TelegramBot:
    def __init__(self, token, socketio):
        self.bot = telebot.TeleBot(token)
        self.socketio = socketio
        self.manager_chat_id = None

        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            if self.manager_chat_id is None:
                self.manager_chat_id = message.chat.id
                self.bot.reply_to(message, "Вы подключены как менеджер. Отвечайте в формате 'user_id: сообщение'")
                return

            if ':' in message.text:
                try:
                    user_id, response_text = message.text.split(':', 1)
                    self.socketio.emit('receive_message', {
                        'user_id': user_id.strip(),
                        'message': response_text.strip(),
                        'timestamp': datetime.now().strftime("%H:%M"),
                        'from_manager': True
                    })
                except Exception as e:
                    print(f"Ошибка обработки сообщения менеджера: {str(e)}")

    def forward_to_manager(self, user_id, message):
        if self.manager_chat_id:
            try:
                self.bot.send_message(
                    self.manager_chat_id,
                    f"{user_id}: {message}"
                )
                return True
            except Exception as e:
                print(f"Ошибка отправки в Telegram: {str(e)}")
                return False
        return False

    def start_polling(self):
        print("Starting Telegram bot polling...")
        try:
            self.bot.infinity_polling(timeout=30, long_polling_timeout=30)
        except Exception as e:
            print(f"Ошибка polling: {str(e)}")
            # Перезапускаем через 5 секунд
            import time
            time.sleep(5)
            self.start_polling()