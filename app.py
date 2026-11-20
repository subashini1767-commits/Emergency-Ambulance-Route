import os

from flask import Flask, redirect, url_for

from config import Config
from database.db import init_db
from routes.auth import auth_bp
from routes.emergency import emergency_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    @app.after_request
    def disable_browser_cache(response):
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response

    init_db(app)

    app.register_blueprint(auth_bp)
    app.register_blueprint(emergency_bp)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login_page'))

    return app


app = create_app()


if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=int(os.environ.get('PORT', '5000')),
        debug=False,
        use_reloader=False,
    )
