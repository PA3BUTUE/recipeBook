# init_db.py
from app import db, app

with app.app_context():
    # Удаляем все существующие таблицы
    db.drop_all()

    # Создаем новые таблицы
    db.create_all()

    print("База данных успешно пересоздана!")