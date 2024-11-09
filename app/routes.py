from flask import render_template, url_for, flash, redirect,jsonify,session
from app import app
from app.db_models import User,Products,Cart
from flask import request
from flask_jwt_extended import create_access_token,get_jwt_identity,jwt_required
import re

    

def is_valid_email(email):
    email_regex = r"(^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$)"
    return re.match(email_regex, email) is not None

# Sign Up endpoint
@app.route('/signup', methods=['POST'])
def signup():
    
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({"error": "Missing required fields"}), 400
    
    if not is_valid_email(email):
        return jsonify({"error": "Invalid email format"}), 400    

    user = User() 
    result = user.save_user(name, email, password)
    return jsonify(result)

#Sign In endpoint
@app.route('/signin', methods=['POST'])
def signin():
    # Get the data from the request
    data = request.json
    
    email = data.get('email')
    password = data.get('password')

    # Check if the email and password are provided
    if not email or not password:
        return jsonify({"error": "Missing required fields"}), 400

    # Find the user by email
    user = User.find_user_by_email(email)

    if not user:
        return jsonify({"error": "Invalid credentials"}), 400

    # Check if the password matches the hashed password in the database
    result,code = User.verify_user_password(email, password)
    
    return jsonify(result),code


@app.route('/logout', methods=['GET'])
def logout():

    session.clear()
    
    return jsonify({"message": "Logout successful"}), 200


#AddProduct endpoint
@app.route('/addproduct', methods=['POST'])
def add_product():
    data = request.json
    
    # Get the product data from the request
    pid = data.get("product_id")
    name = data.get("name")
    description = data.get("description")
    price = data.get("price")
    category = data.get("category")
    
    if not pid or not name or not description or not price or not category:
        return jsonify({"error": "Missing required fields"}), 400    
    

    try:
        price = float(price)  # Ensure the price is a float
        if price < 0:
            return jsonify({"error": "Invalid price"}), 400
    except ValueError:
        return jsonify({"error": "Price must be a valid number"}), 400
    
    result = Products.save_product(pid, name, description, price, category)
    
    return jsonify(result)
    
    
#UpdateProduct
@app.route('/updateproduct/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    # Get the data from the request
    data = request.json
    
    
    result = Products.update_product(product_id,data)
    
    return result

#DeleteProduct
@app.route('/deleteproduct/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    result = Products.delete_product(product_id)
    return result

#GetAllProducts
@app.route('/products', methods=['GET'])
def products():
    
    products = Products.get_all_products()
    
    return products


#Cart Management

@app.route('/cart/add', methods=['POST'])
def add_product_to_cart():
    
    current_user = session.get('user_id')
    if not current_user:
        return jsonify({"error": "User not found"}), 404

    data = request.json
    # Get product_id, user_id, and quantity from request data
    product_id = data.get("product_id")
    user_id = current_user
    quantity = data.get("quantity")
    
    print(user_id)

    # Validate the input data
    if not product_id or user_id == None or  quantity == None:
        return jsonify({"error": "Missing required fields (product_id, user_id, quantity)"}), 400
    
    try:
        quantity = int(quantity)  # Ensure quantity is an integer
    except ValueError:
        return jsonify({"error": "Quantity must be a positive integer"}), 400

    # Call the add_to_cart method from the Cart class
    result = Cart.add_to_cart(product_id, user_id, quantity)

    return result




@app.route('/cart/update', methods=['POST'])
def update_cart():
    # Get current user from JWT token
    current_user = session.get('user_id')
    if not current_user:
        return jsonify({"error": "User not found"}), 404
    
    # Get the product ID and new quantity from the request body
    data = request.json
    product_id = data.get("product_id")
    new_quantity = data.get("quantity")
    
    # Validate the input data
    if not product_id or new_quantity is None:
        return jsonify({"error": "Missing product_id or quantity"}), 400
    
    # Ensure the new quantity is a non-negative integer
    if new_quantity < 0:
        return jsonify({"error": "Quantity must be a non-negative integer"}), 400
    
    result = Cart.cart_update(int(product_id),current_user,int(new_quantity)) 
    return result


@app.route('/cart/delete', methods=['DELETE'])
@jwt_required()
def delete_product_from_cart():
    user_id = session.get("user_id")
    product_id = request.json.get('product_id')
    
    print(product_id,user_id)

    if not product_id:
        return jsonify({"error": "Missing product_id"}), 400

    result = Cart.delete_from_cart(user_id, product_id)
    if result.deleted_count == 0:
        return jsonify({"error": "Product not found in cart"}), 404

    return jsonify({"message": "Product deleted from cart"}), 200

# Get Cart
@app.route('/cart', methods=['GET'])

def get_cart():
    user_id = session.get("user_id")
    cart_items = Cart.get_cart(user_id)
    if not cart_items:
        return jsonify({"message": "Cart is empty"}), 200

    return jsonify({"cart": cart_items}), 200
