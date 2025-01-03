from flask import render_template


class BaseController:
    """
    BaseController provides common functionalities for controllers handling SQLAlchemy models,
    such as CRUD operations and template rendering.
    """

    def __init__(self, model=None, template_folder=None):
        """
        Initialize the BaseController with an optional model and template folder.

        :param model: SQLAlchemy model class associated with this controller.
        :param template_folder: Path to the templates folder for rendering views.
        """
        self.model = model
        self.template_folder = template_folder

    def render(self, template_name, context=None):
        """
        Render a template with the given context.
        """
        context = context or {}
        if self.template_folder:
            return render_template(f"{self.template_folder}/{template_name}", **context)
        return render_template(template_name, **context)
