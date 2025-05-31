# from pydoc import render_doc
from flask import Flask, render_template, request, redirect, url_for, abort
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_socketio import emit  # Добавьте этот импорт
from datetime import datetime

import telebot
from threading import Thread


from telegram_bot import TelegramBot
from chat_manager import ChatManager

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///recipes.db'
app.config["SECRET_KEY"] = "your-secret-key-here"  # Необходимо для SocketIO

db = SQLAlchemy(app)
socketio = SocketIO(app, async_mode='gevent')  # Changed from 'eventlet'

# Конфигурация Telegram бота
TELEGRAM_BOT_TOKEN = '8097607203:AAGTK8Gt_HkMd5pa10yLcfMsg4Mg6rEBGmE'
telegram_bot = TelegramBot(TELEGRAM_BOT_TOKEN, socketio)
chat_manager = ChatManager()
# telegram_bot = telebot.TeleBot("your-bot-token")

Thread(target=telegram_bot.start_polling, daemon=True).start()

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    recipe = db.Column(db.Text, nullable=False)
    # Удаляем image_url и добавляем отношение к изображениям
    images = db.relationship('RecipeImage', backref='post', lazy=True, cascade="all, delete-orphan")

class RecipeImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)



# Обработчики SocketIO
@socketio.on('send_message')
def handle_send_message(data):
    user_id = data['user_id']
    message = data['message']

    # Сохраняем в менеджере чатов
    chat_manager.add_message(user_id, message, is_user=True)

    # Отправляем в Telegram
    telegram_bot.forward_to_manager(user_id, message)

    # Подтверждаем доставку
    emit('message_status', {'status': 'sent', 'timestamp': datetime.now().strftime("%H:%M")})


@socketio.on('get_history')
def handle_get_history(data):
    user_id = data['user_id']
    history = chat_manager.get_chat_history(user_id)
    emit('chat_history', {'history': history})

@app.route("/index")
@app.route("/")
def index():
    posts = Post.query.order_by(Post.id.desc()).limit(3).all()
    return render_template("index.html", posts = posts)

@app.route("/recipes")
def recipes():
    posts = Post.query.order_by(Post.id.desc()).all()
    return render_template("recipes.html", posts = posts)


@app.route("/create", methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        ingredients = request.form['ingredients']
        recipe = request.form['recipe']
        # Получаем список URL изображений
        image_urls = request.form.getlist('image_urls[]')

        post = Post(title=title, description=description,
                    ingredients=ingredients, recipe=recipe)

        # Добавляем изображения
        for url in image_urls:
            if url.strip():  # Пропускаем пустые строки
                post.images.append(RecipeImage(url=url))

        try:
            db.session.add(post)
            db.session.commit()
            return redirect("/")
        except:
            return "Ошибка добавления записи в БД"
    else:
        return render_template("create.html")


@app.route("/recipe/<int:id>")
def show_recipe(id):
    post = Post.query.get_or_404(id)
    return render_template("recipe.html", post=post)


@app.route("/recipe/<int:id>/edit", methods=['GET', 'POST'])
def edit_recipe(id):
    post = Post.query.get_or_404(id)

    if request.method == 'POST':
        post.title = request.form['title']
        post.description = request.form['description']
        post.ingredients = request.form['ingredients']
        post.recipe = request.form['recipe']

        # Удаляем все старые изображения
        for img in post.images:
            db.session.delete(img)

        # Добавляем новые изображения
        image_urls = request.form.getlist('image_urls[]')
        for url in image_urls:
            if url.strip():
                post.images.append(RecipeImage(url=url))

        try:
            db.session.commit()
            return redirect(url_for('show_recipe', id=post.id))
        except:
            return "Ошибка обновления рецепта"
    else:
        return render_template("edit.html", post=post)


@app.route("/recipe/<int:id>/delete", methods=['POST'])
def delete_recipe(id):
    post = Post.query.get_or_404(id)

    try:
        db.session.delete(post)
        db.session.commit()
        return redirect(url_for('recipes'))
    except:
        return "Ошибка удаления рецепта"


if __name__ == "__main__":
    # Для разработки
    socketio.run(app, debug=True, use_reloader=False)

    # Для production используйте:
    # socketio.run(app, host='0.0.0.0', port=5000)