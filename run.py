# run.py
from app.app import create_app

# Создаем экземпляр приложения
app = create_app()

if __name__ == '__main__':
    # Запускаем приложение
    app.run(host='127.0.0.1', port=5000, debug=True)