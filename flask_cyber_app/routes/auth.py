from flask_cyber_app.controllers.auth import AuthController

auth_controller = AuthController()

auth_routes = [
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
]
