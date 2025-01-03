import os

from flask import Flask
from config.configs import Config
from config.extensions import Extension
from flask_cyber_app.models.models import User
from flask_cyber_app.routes.router import Router


class App:
    def __init__(self):
        # Specify the location of the templates directory
        template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
        print(template_dir)
        self.app = Flask(__name__, template_folder=template_dir)
        self.router = Router()  # Instantiate Router
        self.config_extensions()
        self.register_routes()
        self.initialize_database()

    def config_extensions(self):
        """
        Configure extensions and update the app with necessary settings.
        """
        self.app.config.update(Config.DB_CONFIG)
        Extension.db.init_app(self.app)
        Extension.socketio.init_app(self.app)
        Extension.login_manager.init_app(self.app)
        Extension.login_manager.login_view = 'auth.login'

        @Extension.login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))

    def register_routes(self):
        """
        Register all application routes using the Router class.
        """
        self.router.register_routes(self.app)  # Call on Router instance

    def initialize_database(self):
        """
        Initialize the database and create tables if they do not exist.
        """
        with self.app.app_context():
            Extension.db.create_all()

    def run(self):
        """
        Run the application using SocketIO.
        """
        Extension.socketio.run(self.app, debug=True)


if __name__ == '__main__':
    app_instance = App()
    app_instance.run()
