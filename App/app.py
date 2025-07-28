from flask import Flask
from models import db
from flask_wtf.csrf import CSRFProtect
from waitress import serve
from dotenv import load_dotenv
import os

load_dotenv()

DEV = os.getenv("DEV")

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rss_feeds.db'
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    app.config['UPLOAD_FOLDER'] = 'uploads' # Define a folder to store uploaded files
    app.config['ALLOWED_EXTENSIONS'] = {'opml', 'xml', 'txt'}

    # app.config['WTF_CSRF_SECRET_KEY'] = 'different-secure-key-here'  # Optional but recommended
    app.config['WTF_CSRF_ENABLED'] = False

    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    csrf = CSRFProtect(app)    
    # Initialize extensions
    db.init_app(app)
    
    # Import routes after app creation to avoid circular imports
    with app.app_context():
        from routes import main as main_blueprint
        app.register_blueprint(main_blueprint)
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    if DEV == "True":
        app.run(debug=True)
    else:
        serve(app, host="0.0.0.0", port=8080)