from flask_cyber_app.app import App

if __name__ == "__main__":
    app_instance = App()
    print("Template folder:", app_instance.template_folder)
    app_instance.run()

# Gunicorn and WSGI (Web Server Gateway Interface) are both components used in deploying and serving Python
# web applications, particularly those built with web frameworks like Flask and Django.
