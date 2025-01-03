from config.extensions import Extension
from flask_cyber_app.controllers.chat import ChatController

chat_controller = ChatController(Extension.socketio)

chat_routes = [
    {
        'route': '/chat',
        'name': 'chat',
        'handler': chat_controller.register_events,
        'methods': ['GET'],
    },
    # {
    #     'route': '/chat/messages',
    #     'name': 'chat_messages',
    #     'handler': chat_controller.get_messages,
    #     'methods': ['GET', 'POST'],
    # },
]