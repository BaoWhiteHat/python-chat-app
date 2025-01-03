from flask import Blueprint
from .auth import auth_routes
from .chat import chat_routes


class Router:
    def __init__(self):
        # Define route collections
        self.routes = {
            'auth': auth_routes,
            'chat': chat_routes,
        }

    def register_routes(self, app):
        """
        Dynamically register blueprints and their routes with the Flask app.
        """
        for blueprint_name, routes in self.routes.items():
            # Create a new blueprint for each route collection
            blueprint = Blueprint(blueprint_name, __name__)
            for route in routes:
                blueprint.add_url_rule(
                    route['route'],  # Corrected key name
                    route['name'],
                    view_func=route['handler'],
                    methods=route['methods']
                )
            # Register the blueprint with the app
            app.register_blueprint(blueprint, url_prefix=f'/{blueprint_name}')
