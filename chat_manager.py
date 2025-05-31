from datetime import datetime


class ChatManager:
    def __init__(self):
        self.chats = {}  # {user_id: [messages]}

    def add_message(self, user_id, message, is_user=False):
        if user_id not in self.chats:
            self.chats[user_id] = []

        self.chats[user_id].append({
            'text': message,
            'is_user': is_user,
            'timestamp': datetime.now().strftime("%H:%M")
        })

    def get_chat_history(self, user_id, limit=20):
        if user_id in self.chats:
            return self.chats[user_id][-limit:]
        return []

    def close_chat(self, user_id):
        if user_id in self.chats:
            del self.chats[user_id]