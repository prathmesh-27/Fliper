from app import db
import bcrypt
from flask_jwt_extended import create_access_token
from flask import jsonify
from bson.objectid import ObjectId
from flask import session





class User:
    @staticmethod 
    def save_user(name, email, password):
        if db.users.find_one({"email": email}):
            return {"error": "Email already exists"}, 400

        # Hash the password using bcrypt
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user_data = {
            "name": name,
            "email": email,
            "password": hashed_password.decode('utf-8'), 
        }

        # Insert the new user into MongoDB
        result = db.users.insert_one(user_data)
        return {"message": "User registered successfully", "user_id": str(result.inserted_id)}, 201
    
    @staticmethod
    def find_user_by_email(email):
        # Find the user by email
        return db.users.find_one({"email": email})
    
    @staticmethod
    def verify_user_password(email, password):
        # Fetch user details based on the email
        user = db.users.find_one({"email": email})
        
        if not user:
            return {"error": "Invalid credentials"}, 400

        # Check if provided password matches with the hashed password stored in the database
        if not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            return {"error": "Invalid credentials"}, 400
        
        
        session['user_id'] = str(user["_id"])

        # Return success message along with the JWT token
        return {"message": "Sign-in successful","session_token":str(user['_id'])}, 200        



class Products:
    @staticmethod
    def save_product(pid, name, description, price, category):
        # Check if the product ID (pid) already exists
        if db.Products.find_one({"pid": int(pid)}):
            return {"error": "Product ID already exists"}, 400  # Return error if pid is not unique
    
        # If pid is unique, create the product data
        product_data = {
            "pid": int(pid),
            "name": name,
            "description": description,
            "price": price, 
            "category": category
        }

    # Insert the new product into MongoDB
        result = db.Products.insert_one(product_data)
    
        return {"message": "Product Added successfully"}, 201
    
    @staticmethod
    def update_product(product_id,data):
     # Validate the product ID exists
        product = db.Products.find_one({"pid": product_id})
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
    
     # Validate fields to update (only fields provided in the request will be updated)
        updated_data = {}
    
    # Check for missing fields and add to the updated_data dictionary if valid
        if data.get("name"):
            updated_data["name"] = data.get("name")
        if data.get("description"):
            updated_data["description"] = data.get("description")
        if data.get("price"):
        # Validate that the price is a valid number and not negative
            try:
                price = float(data.get("price"))
                if price < 0:
                    return jsonify({"error": "Price must be a positive number"}), 400
                updated_data["price"] = price
            except ValueError:
                return jsonify({"error": "Price must be a valid number"}), 400
            
            if data.get("category"):
                updated_data["category"] = data.get("category")

    # If no fields are provided to update
        if not updated_data:
            return jsonify({"error": "No valid fields provided to update"}), 400

    # Update the product details in the database
        result = db.Products.update_one({"pid": product_id}, {"$set": updated_data})

    # Check if the update was successful
        if result.matched_count == 0:
            return jsonify({"error": "Product not found"}), 404

        return jsonify({"message": "Product updated successfully"}), 200    

    @staticmethod
    def delete_product(product_id):
        # Validate the product ID exists
        product = db.Products.find_one({"pid": product_id})
        
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        # Delete the product from the database
        result = db.Products.delete_one({"pid": product_id})

        # Check if the deletion was successful
        if result.deleted_count == 0:
            return jsonify({"error": "Product not found"}), 404
        
        # Return success message
        return jsonify({"message": "Product deleted successfully"}), 200    
    
    
    @staticmethod
    def get_all_products():
        # Retrieve all products from the database
        products = db.Products.find()    
            
        products = list(products)
        print(products)
            
        if len(products) == 0:
            return jsonify({"message": "No products available"}), 404

        # Create a list of products to return in the response
        product_list = []
        for product in products:
            product_list.append({
            "product_id": product["pid"],
            "name": product["name"],
            "description": product["description"],
            "price": product["price"],
            "category": product["category"]
         })

        return jsonify({"products": product_list}), 200
    
    
class Cart:
    @staticmethod
    def add_to_cart(product_id, user_id, quantity):
        product_id = int(product_id)
        # Validate that quantity is a positive integer
        if quantity <= 0:
            return jsonify({"error": "Quantity must be a positive integer"}), 400
        
        # Check if the product exists in the database
        product = db.Products.find_one({"pid": product_id})
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        # Find the user's cart in the database
        cart = db.Cart.find_one({"user_id": ObjectId(user_id)})  # Assuming user_id is an ObjectId
        
        # If cart doesn't exist, create a new cart entry
        if not cart:
            cart_data = {
                "user_id": ObjectId(user_id),
                "items": [{"product_id": product_id, "quantity": quantity}]
            }
            db.Cart.insert_one(cart_data)
            return jsonify({"message": "Product added to cart successfully"}), 201
        
        # If cart exists, check if the product is already in the cart
        existing_item = None
        for item in cart["items"]:
            if item["product_id"] == product_id:
                existing_item = item
                break
        
        if existing_item:
            # Update the quantity if the product is already in the cart
            db.Cart.update_one(
                {"user_id": ObjectId(user_id), "items.product_id": product_id},
                {"$set": {"items.$.quantity": existing_item["quantity"] + quantity}}
            )
            return jsonify({"message": "Cart updated successfully"}), 200
        else:
            # Add the new product to the cart
            db.Cart.update_one(
                {"user_id": ObjectId(user_id)},
                {"$push": {"items": {"product_id": product_id, "quantity": quantity}}}
            )
            return jsonify({"message": "Product added to cart successfully"}), 201
        
    @staticmethod
    def cart_update(product_id,current_user,new_quantity):
                # Retrieve the product from the Products collection to check stock
        product = db.Products.find_one({"pid": product_id})
    
        if not product:
            return jsonify({"error": "Product not found"}), 404
    
    # Check if the product is in the user's cart
        cart_item = db.Cart.find_one({"user_id": current_user, "product_id": product_id})
    
        if not cart_item:
            return jsonify({"error": "Product not in cart"}), 404
    
    # Check if the new quantity exceeds available stock
        if new_quantity > product["stock"]:
            return jsonify({"error": "Insufficient stock available"}), 400
    
    # Update the cart (remove product if quantity is 0)
        if new_quantity == 0:
            db.Cart.delete_one({"user_id": current_user, "product_id": product_id})
            return jsonify({"message": "Product removed from cart"}), 200
    
    # Update the cart with the new quantity
        db.Cart.update_one(
        {"user_id": current_user, "product_id": product_id},
        {"$set": {"quantity": new_quantity}}
            )
    
    # Fetch the updated cart details
        updated_cart = db.Cart.find({"user_id": current_user})
        cart_items = []
        for item in updated_cart:
            product_info = db.Products.find_one({"pid": item["product_id"]})
            cart_items.append({
                "product_id": item["product_id"],
                "name": product_info["name"],
                "quantity": item["quantity"],
                "price": product_info["price"]
                })
    
        return jsonify({"message": "Cart updated successfully", "cart": cart_items}), 200
        
    @staticmethod
    def delete_from_cart(user_id, product_id):
        return db.Cart.delete_one({"user_id": user_id, "product_id": product_id})

    @staticmethod
    def get_cart(user_id):
        print(user_id)
        user_id = ObjectId(user_id)
        result = []
        cart_items = db.Cart.find({"user_id": user_id})
        
        for item in cart_items:
            item['_id'] = str(item['_id'])
            item['user_id'] = str(item['user_id'])
            item['item'] = list(item['items'])
            result.append(item)

        
        return list(db.Cart.find_one({"user_id":user_id }))      
    
    
    
# Order Model
class Order:
    @staticmethod
    def place_order(user_id, shipping_details):
        cart_items = Cart.get_cart(user_id)
        if not cart_items:
            return None
        order_id = db.Orders.insert_one({
            "user_id": user_id,
            "cart_items": cart_items,
            "shipping_details": shipping_details,
            "status": "Placed"
        }).inserted_id
        Cart.clear_cart(user_id)
        return str(order_id)

    @staticmethod
    def get_orders_by_customer(user_id):
        return list(db.Orders.find({"user_id": user_id}))

    @staticmethod
    def get_all_orders():
        return list(db.Orders.find())      
        
    