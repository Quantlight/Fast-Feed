from flask import Flask
from models import db

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rss_feeds.db'
    app.config['SECRET_KEY'] = 'your_secret_key_here'
    
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
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)