import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy.orm import declarative_base
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize SQLAlchemy with no app yet
db = SQLAlchemy()
migrate = Migrate()

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)  # needed for url_for to generate with https

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
db.init_app(app)
migrate.init_app(app, db)

# Import routes
from api_routes import api
from web_routes import web

# Register blueprints
app.register_blueprint(api, url_prefix='/api')
app.register_blueprint(web)

@app.errorhandler(SQLAlchemyError)
def handle_db_error(error):
    logging.error(f"Database error: {str(error)}")
    return {
        "success": False,
        "message": "A database error occurred",
        "error": str(error) if app.debug else "Internal server error"
    }, 500

if __name__ == "__main__":
    app.run(debug=True)
