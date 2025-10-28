from flask import Flask, jsonify, request
import logging
from datetime import datetime
import random

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Simulated inventory database
inventory = {
    'PROD-001': {'name': 'Laptop', 'stock': 50},
    'PROD-002': {'name': 'Mouse', 'stock': 200},
    'PROD-003': {'name': 'Keyboard', 'stock': 100},
    'PROD-004': {'name': 'Monitor', 'stock': 30},
    'PROD-005': {'name': 'Headphones', 'stock': 75}
}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'inventory-service', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/ready', methods=['GET'])
def ready():
    return jsonify({'status': 'ready'}), 200

@app.route('/check', methods=['POST'])
def check_inventory():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        logging.info(f"Checking inventory: product={product_id}, quantity={quantity}")
        
        if product_id not in inventory:
            return jsonify({'available': False, 'reason': 'Product not found'}), 404
        
        available_stock = inventory[product_id]['stock']
        
        if available_stock >= quantity:
            # Simulate stock reservation
            inventory[product_id]['stock'] -= quantity
            logging.info(f"Stock reserved: {quantity} units of {product_id}. Remaining: {inventory[product_id]['stock']}")
            return jsonify({
                'available': True,
                'product_id': product_id,
                'reserved': quantity,
                'remaining_stock': inventory[product_id]['stock']
            }), 200
        else:
            return jsonify({
                'available': False,
                'reason': 'Insufficient stock',
                'requested': quantity,
                'available_stock': available_stock
            }), 400
            
    except Exception as e:
        logging.error(f"Inventory check failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/inventory', methods=['GET'])
def get_inventory():
    return jsonify({'inventory': inventory, 'timestamp': datetime.now().isoformat()}), 200

@app.route('/inventory/<product_id>', methods=['GET'])
def get_product(product_id):
    if product_id in inventory:
        return jsonify({
            'product_id': product_id,
            'details': inventory[product_id],
            'timestamp': datetime.now().isoformat()
        }), 200
    return jsonify({'error': 'Product not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)