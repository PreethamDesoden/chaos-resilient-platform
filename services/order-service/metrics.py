from prometheus_client import Counter, Histogram, generate_latest, REGISTRY
from flask import Response
import time

# Metrics
order_requests_total = Counter(
    'order_requests_total',
    'Total number of order requests',
    ['status', 'product_id']
)

order_request_duration = Histogram(
    'order_request_duration_seconds',
    'Order request duration in seconds',
    ['endpoint']
)

inventory_requests_total = Counter(
    'inventory_requests_total',
    'Total requests to inventory service',
    ['status']
)

notification_requests_total = Counter(
    'notification_requests_total',
    'Total requests to notification service',
    ['status']
)

def metrics_endpoint():
    """Expose metrics for Prometheus scraping"""
    return Response(generate_latest(REGISTRY), mimetype='text/plain')

def track_order_request(status, product_id):
    """Track order request metrics"""
    order_requests_total.labels(status=status, product_id=product_id).inc()

def track_request_duration(endpoint, duration):
    """Track request duration"""
    order_request_duration.labels(endpoint=endpoint).observe(duration)

def track_inventory_request(status):
    """Track inventory service requests"""
    inventory_requests_total.labels(status=status).inc()

def track_notification_request(status):
    """Track notification service requests"""
    notification_requests_total.labels(status=status).inc()