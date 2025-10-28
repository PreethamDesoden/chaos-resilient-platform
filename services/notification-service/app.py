from flask import Flask, jsonify, request
import logging
from datetime import datetime
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Store notifications in memory (for demo purposes)
notifications_log = []

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'notification-service', 'timestamp': datetime.now().isoformat()}), 200

@app.route('/ready', methods=['GET'])
def ready():
    return jsonify({'status': 'ready'}), 200

@app.route('/notify', methods=['POST'])
def send_notification():
    try:
        data = request.get_json()
        email = data.get('email')
        order_id = data.get('order_id')
        product_id = data.get('product_id')
        
        # Simulate email sending delay
        time.sleep(0.1)
        
        notification = {
            'email': email,
            'order_id': order_id,
            'product_id': product_id,
            'message': f'Order {order_id} confirmed for product {product_id}',
            'sent_at': datetime.now().isoformat(),
            'status': 'sent'
        }
        
        notifications_log.append(notification)
        logging.info(f"Notification sent: {email} for order {order_id}")
        
        return jsonify({
            'status': 'sent',
            'notification_id': f"NOTIF-{len(notifications_log)}",
            'sent_at': notification['sent_at']
        }), 200
        
    except Exception as e:
        logging.error(f"Notification failed: {e}")
        return jsonify({'error': 'Failed to send notification'}), 500

@app.route('/notifications', methods=['GET'])
def get_notifications():
    return jsonify({
        'total': len(notifications_log),
        'notifications': notifications_log[-10:],  # Last 10 notifications
        'timestamp': datetime.now().isoformat()
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=False)