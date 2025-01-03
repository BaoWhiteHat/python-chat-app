import traceback
from flask import render_template


class ExceptionHandler:
    def __init__(self, app):
        """
        Initialize the exception handler with a Flask app instance.
        """
        self.app = app
        self.setup_error_handlers()

    def setup_error_handlers(self):
        """
        Register error handlers for the Flask app.
        """

        @self.app.errorhandler(Exception)
        def handle_general_exception(e):
            # Capture the full traceback
            tb = traceback.format_exc()

            # Log the exception and traceback
            self.app.logger.error(f"Unhandled Exception: {e}")
            self.app.logger.error(f"Traceback:\n{tb}")

            # Render a custom error page
            return render_template("error.html", error=str(e)), 500

        @self.app.errorhandler(404)
        def handle_not_found_error(e):
            # Render a custom 404 error page
            return render_template("error.html", error="Page not found!"), 404
