# run.py
from app.app import create_app
from app.config import FLASK_ENV

# Получаем режим из переменной FLASK_ENV, по умолчанию 'development'
config_name = FLASK_ENV

# Создаем экземпляр приложения
app = create_app(config_name=config_name)

if __name__ == '__main__':
    # Запускаем приложение (только для разработки/тестирования)
    app.run(host='127.0.0.1', port=5000, debug=config_name != 'production')