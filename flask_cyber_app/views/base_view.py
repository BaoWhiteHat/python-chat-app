class BaseView:
    def __init__(self, controller=None):
        """
        Initialize the views with an optional controller.
        :param controller: The controller associated with this views.
        """
        self.controller = controller
