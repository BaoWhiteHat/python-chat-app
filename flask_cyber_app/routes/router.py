from flask import Blueprint, session, redirect, url_for, request
from datetime import datetime
from flask_cyber_app.models.models import Session, User


class Router:
    def __init__(self, combined_routes):
        """
        Initialize the Router with a combined dictionary of all routes.
        :param combined_routes: Dictionary with blueprint names as keys and route collections as values.
        """
        self.combined_routes = combined_routes

    def register_routes(self, app, excluded_endpoints=None):
        """
        Dynamically register blueprints and their routes with the Flask app.
        Apply middleware for session validation, excluding specific endpoints.
        """
        excluded_endpoints = excluded_endpoints or []

        @app.before_request
        def validate_session():
            """Middleware to validate session before each request."""
            if request.endpoint in excluded_endpoints:
                return

            session_id = session.get("session_id")
            print(session_id)
            if not session_id:
                return redirect(url_for("auth.login"))

            active_session = Session.query.get(session_id)
            print(active_session)
            if not active_session or active_session.expires_at < datetime.utcnow():
                print("session expire ?")
                session.pop("session_id", None)
                return redirect(url_for("auth.login"))

            # Fetch user object explicitly
            user = User.query.get(active_session.user_id)
            print(f"user:{user}")
            if not user:
                session.pop("session_id", None)
                return redirect(url_for("auth.login"))

            # Store session and user in Flask's session object
            session["current_session"] = active_session.id
            session["current_user"] = user.id

        # Register blueprints and routes
        for blueprint_name, routes in self.combined_routes.items():
            blueprint = Blueprint(blueprint_name, __name__)
            for route in routes:
                blueprint.add_url_rule(
                    route['route'],
                    route['name'],
                    view_func=route['handler'],
                    methods=route['methods']
                )
            app.register_blueprint(blueprint, url_prefix=f'/{blueprint_name}')
