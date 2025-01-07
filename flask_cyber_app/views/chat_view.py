from threading import Thread

from flask import render_template, g, redirect, url_for, flash, session

from config.extensions import Extension
from flask_cyber_app.controllers.chat import ChatController
from flask_cyber_app.views.base_view import BaseView


class ChatView(BaseView):
    def __init__(self):
        super().__init__(ChatController(Extension.socketio))

    def render_chat(self):
        """Render the chat page for authenticated users."""
        current_user = session.get("current_user")
        current_session = session.get("current_session")

        if not current_user or not current_session:
            flash("You must be logged in to access the chat.", category="error")
            return redirect(url_for("auth.login"))

        # Render the chat template
        return render_template("chat.html", user=current_user)
