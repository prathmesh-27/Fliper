from flask import Flask
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_jwt_extended import JWTManager
from flask_pymongo import PyMongo

app = Flask(__name__)

# Configuration settings
app.config["MONGO_URI"] = "mongodb+srv://user1:1234@cluster0.l0jynza.mongodb.net/Fliper_backend?retryWrites=true&w=majority&appName=Cluster0"
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SESSION_TYPE"] = "filesystem"  # Store session in filesystem

Session(app)
db = PyMongo(app).db
print("Connection to database SuccessFul")

bcrypt = Bcrypt(app)

from app import routes
