import os

import ssl
import eventlet
import eventlet.wsgi
from flask import Flask
from config.configs import Config
from config.expection_handler import ExceptionHandler
from config.extensions import Extension
from flask_cyber_app.models.models import User
from flask_cyber_app.routes.all_routes import all_routes
from flask_cyber_app.routes.router import Router

keys_and_certificate = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'keys_and_certificate'))
print(keys_and_certificate)

class App:
    def __init__(self):
        # Specify the location of the templates directory
        template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
        self.app = Flask(__name__, template_folder=template_dir)
        self.router = Router(combined_routes=all_routes)  # Instantiate Router
        self.config_extensions()
        self.register_routes()
        self.initialize_database()

        # self.exception_handler = ExceptionHandler(self.app)

    def config_extensions(self):
        """
        Configure extensions and update the app with necessary settings.
        """
        self.app.config.update(Config.CONFIG)
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
        self.router.register_routes(
            self.app,
            excluded_endpoints=[
                'auth.login',  # Skip session validation for login
                'auth.sign_up',  # Skip session validation for sign-up
            ]
        )  # Call on Router instance

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
        # ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        # ssl_context.load_cert_chain(
        #     certfile=f'{keys_and_certificate}/certificate.crt',
        #     keyfile=f'{keys_and_certificate}/ec-private-key.pem'
        # )
        # # Wrap socket with SSL
        # listener = eventlet.listen(('127.0.0.1', 5000))
        # ssl_socket = ssl_context.wrap_socket(listener, server_side=True)
        #
        # # Run the Eventlet WSGI server with SSL
        # eventlet.wsgi.server(ssl_socket, self.app)

        Extension.socketio.run(
            self.app,
            debug=False,

        )


if __name__ == '__main__':
    app_instance = App()
    app_instance.run()
