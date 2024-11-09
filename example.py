from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token
from flask_pymongo import PyMongo
import re

# Initialize Flask app
app = Flask(__name__)

# Set up the MongoDB URI (Replace with your MongoDB connection string)
app.config["MONGO_URI"] = "mongodb+srv://user1:1234@cluster0.l0jynza.mongodb.net/Fliper_backend?retryWrites=true&w=majority&appName=Cluster0"
app.config["JWT_SECRET_KEY"] = "your_jwt_secret_key"  # Change this to a secure key

# Initialize extensions
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
mongo = PyMongo(app)
print("Connection SuccessFul")

# Helper function to validate email format
def is_valid_email(email):
    email_regex = r"(^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$)"
    return re.match(email_regex, email) is not None

# Sign Up endpoint
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    # Validate input data
    if not data.get('email') or not data.get('password') or not data.get('name'):
        return jsonify({"error": "Missing required fields"}), 400

    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    # Validate email format
    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400
    
    # Check if email already exists
    if mongo.db.users.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 400
    
    # Hash the password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Create a new user in the database
    new_user = {
        "name": name,
        "email": email,
        "password": hashed_password,
    }
    
    mongo.db.users.insert_one(new_user)

    # Return success message with customer ID
    user_id = str(new_user["_id"])
    return jsonify({"message": "Signup successful", "user_id": user_id}), 201

# Sign In endpoint
@app.route('/signin', methods=['POST'])
def signin():
    data = request.get_json()

    # Validate input data
    if not data.get('email') or not data.get('password'):
        return jsonify({"error": "Missing required fields"}), 400

    email = data.get('email')
    password = data.get('password')

    # Check if email exists in the database
    user = mongo.db.users.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Verify the password
    if not bcrypt.check_password_hash(user['password'], password):
        return jsonify({"error": "Incorrect password"}), 401

    # Generate a JWT session token
    access_token = create_access_token(identity=str(user["_id"]))

    # Return the session token
    return jsonify({"message": "Login successful", "access_token": access_token}), 200

if __name__ == '__main__':
    app.run(debug=True)
