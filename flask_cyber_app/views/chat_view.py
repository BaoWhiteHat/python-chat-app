from threading import Thread

from flask import render_template, g, redirect, url_for, flash

from config.extensions import Extension
from flask_cyber_app.controllers.chat import ChatController
from flask_cyber_app.views.base_view import BaseView


class ChatView(BaseView):
    def __init__(self):
        super().__init__(ChatController(Extension.socketio))

    def render_chat(self):
        """Render the chat page for authenticated users."""
        # Ensure the user is authenticated and has an active session
        current_user = getattr(g, "current_user", None)
        current_session = getattr(g, "current_session", None)

        if not current_user or not current_session:
            flash("You must be logged in to access the chat.", category="error")
            return redirect(url_for("auth.login"))

        # Register WebSocket events asynchronously after rendering
        if self.controller and hasattr(self.controller, "register_events"):
            Thread(target=self.controller.register_events).start()

        # Render the chat template
        return render_template("chat.html", user=current_user)
