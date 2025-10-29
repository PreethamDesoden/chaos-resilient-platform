from flask import Flask, jsonify, request
import requests
import os
import logging
from datetime import datetime
import time
from metrics import (
    metrics_endpoint,
    track_order_request,
    track_request_duration,
    track_inventory_request,
    track_notification_request
)

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

INVENTORY_SERVICE = os.getenv('INVENTORY_SERVICE_URL', 'http://inventory-service:5001')
NOTIFICATION_SERVICE = os.getenv('NOTIFICATION_SERVICE_URL', 'http://notification-service:5002')

@app.route('/metrics', methods=['GET'])
def metrics():
    return metrics_endpoint()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'order-service', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/ready', methods=['GET'])
def ready():
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
    start_time = time.time()
    
    try:
        order_data = request.get_json()
        product_id = order_data.get('product_id')
        quantity = order_data.get('quantity', 1)
        user_email = order_data.get('email')
        
        logging.info(f"Received order: product={product_id}, quantity={quantity}")
        
        try:
            inv_response = requests.post(
                f'{INVENTORY_SERVICE}/check',
                json={'product_id': product_id, 'quantity': quantity},
                timeout=3
            )
            
            if inv_response.status_code != 200:
                track_inventory_request('failed')
                track_order_request('failed', product_id)
                duration = time.time() - start_time
                track_request_duration('/orders', duration)
                return jsonify({'error': 'Product unavailable'}), 400
            
            track_inventory_request('success')
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Inventory service error: {e}")
            track_inventory_request('error')
            track_order_request('error', product_id)
            duration = time.time() - start_time
            track_request_duration('/orders', duration)
            return jsonify({'error': 'Inventory service unavailable'}), 503
        
        order_id = f"ORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
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
            track_notification_request('success')
        except requests.exceptions.RequestException as e:
            logging.warning(f"Notification failed (non-critical): {e}")
            track_notification_request('failed')
        
        logging.info(f"Order created: {order_id}")
        track_order_request('success', product_id)
        duration = time.time() - start_time
        track_request_duration('/orders', duration)
        
        return jsonify({
            'order_id': order_id,
            'status': 'confirmed',
            'product_id': product_id,
            'quantity': quantity
        }), 201
        
    except Exception as e:
        logging.error(f"Order creation failed: {e}")
        track_order_request('error', 'unknown')
        duration = time.time() - start_time
        track_request_duration('/orders', duration)
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