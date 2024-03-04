from flask import Flask
from routes import app
from models import init_db, db
from summarizer import ai_summarizer

if __name__ == '__main__':
    init_db(app)  # Initialize SQLAlchemy with the Flask app
    with app.app_context():
        db.create_all()
    app.run(debug=True)