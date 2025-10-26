from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pymongo import MongoClient
from datetime import timedelta
import os

# Blueprints
from routes.auth import auth_bp
from routes.lessons import lessons_bp
from dotenv import load_dotenv

load_dotenv(dotenv_path='../.env')

# App factory

def create_app():
    app = Flask(__name__)
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'dev-key')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
    app.config['MONGODB_URI'] = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/innoserve-dev')
    app.config['CORS_ORIGINS'] = os.environ.get('CORS_ORIGINS', 'http://localhost:5173')

    # Extensions
    CORS(app, origins=app.config['CORS_ORIGINS'].split(','))
    JWTManager(app)
    limiter = Limiter(key_func=get_remote_address, default_limits=["1000 per day", "100 per hour"])
    limiter.init_app(app)

    # MongoDB
    app.mongo = MongoClient(app.config['MONGODB_URI'])

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(lessons_bp, url_prefix='/api/lessons')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5001)
