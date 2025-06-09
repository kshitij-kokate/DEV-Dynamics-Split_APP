# import os
# import logging
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from sqlalchemy.orm import DeclarativeBase
# from werkzeug.middleware.proxy_fix import ProxyFix

# # Configure logging
# logging.basicConfig(level=logging.DEBUG)

# class Base(DeclarativeBase):
#     pass

# db = SQLAlchemy(model_class=Base)

# # Create the app
# app = Flask(__name__)
# app.secret_key = os.environ.get("SESSION_SECRET")
# app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# # Configure the database
# app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
# app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
#     "pool_recycle": 300,
#     "pool_pre_ping": True,
# }

# # Initialize the app with the extension
# db.init_app(app)

# # Import routes
# from api_routes import api
# from web_routes import web

# # Register blueprints
# app.register_blueprint(api, url_prefix='/api')
# app.register_blueprint(web)

# with app.app_context():
#     # Make sure to import the models here or their tables won't be created
#     import models  # noqa: F401
#     db.create_all()

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000, debug=True)


import os
import logging
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from extensions import db

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SESSION_SECRET")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Database configuration
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL environment variable not set")
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from api_routes import api
    from web_routes import web
    app.register_blueprint(api, url_prefix='/api')
    app.register_blueprint(web)

    # Create tables
    with app.app_context():
        import models  # noqa: F401
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)