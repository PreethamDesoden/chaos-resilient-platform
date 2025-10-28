from flask import Flask, jsonify, request
import requests
import os
import logging
from datetime import datetime

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

INVENTORY_SERVICE = os.getenv('INVENTORY_SERVICE_URL', 'http://inventory-service:5001')
NOTIFICATION_SERVICE = os.getenv('NOTIFICATION_SERVICE_URL', 'http://notification-service:5002')

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'order-service', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/ready', methods=['GET'])
def ready():
    # Check if dependent services are reachable
    try:
        inv_response = requests.get(f'{INVENTORY_SERVICE}/health', timeout=2)
        notif_response = requests.get(f'{NOTIFICATION_SERVICE}/health', timeout=2)
        
        if inv_response.status_code == 200 and notif_response.status_code == 200:
            return jsonify({'status': 'ready'}), 200
        return jsonify({'status': 'not ready', 'reason': 'dependencies unavailable'}), 503
    except Exception as e:
        return jsonify({'status': 'not ready', 'reason': str(e)}), 503

@app.route('/orders', methods=['POST'])
def create_order():
    try:
        order_data = request.get_json()
        product_id = order_data.get('product_id')
        quantity = order_data.get('quantity', 1)
        user_email = order_data.get('email')
        
        logging.info(f"Received order: product={product_id}, quantity={quantity}")
        
        # Check inventory
        try:
            inv_response = requests.post(
                f'{INVENTORY_SERVICE}/check',
                json={'product_id': product_id, 'quantity': quantity},
                timeout=3
            )
            
            if inv_response.status_code != 200:
                return jsonify({'error': 'Product unavailable'}), 400
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Inventory service error: {e}")
            return jsonify({'error': 'Inventory service unavailable'}), 503
        
        # Create order
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Send notification (fire and forget with retry)
        try:
            requests.post(
                f'{NOTIFICATION_SERVICE}/notify',
                json={
                    'email': user_email,
                    'order_id': order_id,
                    'product_id': product_id
                },
                timeout=2
            )
        except requests.exceptions.RequestException as e:
            logging.warning(f"Notification failed (non-critical): {e}")
        
        logging.info(f"Order created: {order_id}")
        return jsonify({
            'order_id': order_id,
            'status': 'confirmed',
            'product_id': product_id,
            'quantity': quantity
        }), 201
        
    except Exception as e:
        logging.error(f"Order creation failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/orders/<order_id>', methods=['GET'])
def get_order(order_id):
    return jsonify({
        'order_id': order_id,
        'status': 'processing',
        'created_at': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)