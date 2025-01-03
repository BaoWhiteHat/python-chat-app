from config.extensions import Extension
from flask_cyber_app.controllers.auth import AuthController
from flask_cyber_app.controllers.chat import ChatController
from flask_cyber_app.views.chat_view import ChatView

# chat_controller = ChatController(Extension.socketio)
chat_view = ChatView()
auth_controller = AuthController()

all_routes = {
    'auth': [
        {
            'route': '/login',
            'name': 'login',
            'handler': auth_controller.login,
            'methods': ['GET', 'POST'],
        },
        {
            'route': '/logout',
            'name': 'logout',
            'handler': auth_controller.logout,
            'methods': ['GET'],
        },
        {
            'route': '/sign-up',
            'name': 'sign_up',
            'handler': auth_controller.sign_up,
            'methods': ['GET', 'POST'],
        },
    ],
    'chat': [
        {
            'route': '/chat',
            'name': 'chat',
            'handler': chat_view.render_chat,
            'methods': ['GET'],
        },

    ]
}