from pathlib import Path
from flask import Flask
from routes import main
from database import init_db


def create_app(config=None):
    app = Flask(__name__)
    app.config['DATABASE'] = str(Path(app.instance_path) / 'medications.sqlite3')
    app.config['REMINDER_TIMEZONE'] = 'America/Chicago'
    if config:
        app.config.update(config)
    app.register_blueprint(main)
    init_db(app)
    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
