import os
import random
import time
import uuid
import logging
import threading
from flask import Flask, request, jsonify
import requests
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get environment variables
service_name = os.environ.get('OTEL_SERVICE_NAME', 'unknown-service')
service_port = int(os.environ.get('SERVICE_PORT', '8080'))

# Configure the tracer
resource = Resource.create()  # Use OTEL_RESOURCE_ATTRIBUTES environment variable
trace.set_tracer_provider(TracerProvider(resource=resource))

# Configure the OTLP exporter
otlp_exporter = OTLPSpanExporter()
span_processor = BatchSpanProcessor(span_exporter=otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Create a tracer
tracer = trace.get_tracer(__name__)

# Create a propagator for handling trace context
propagator = TraceContextTextMapPropagator()

# Create Flask application
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Furniture models available
sofa_models = [
    {"id": "classic-001", "name": "Classic Comfort", "price": 899.99, "production_time": 2},
    {"id": "modern-002", "name": "Modern Minimalist", "price": 1299.99, "production_time": 3},
    {"id": "luxury-003", "name": "Luxury Lounge", "price": 2499.99, "production_time": 5},
    {"id": "sectional-004", "name": "Sectional Supreme", "price": 1899.99, "production_time": 4},
    {"id": "limited-edition", "name": "Limited Edition Designer", "price": 4999.99, "production_time": 7}
]

# Customer types
customer_types = ["regular", "premium", "vip"]

# Distribution centers
distribution_centers = {
    "global": ["New York", "Shanghai", "Berlin", "Sydney"],
    "local": ["North District", "South District", "East District", "West District"]
}

# Simulated failures by service
failure_scenarios = {
    "sofa-factory": {"probability": 0.2, "message": "Production line issue: Unable to complete sofa manufacturing"},
    "global-distribution": {"probability": 0.15, "message": "Item lost in global distribution center"},
    "local-distribution": {"probability": 0.1, "message": "Delivery vehicle breakdown"}
}

# Simulated latency scenarios
latency_scenarios = {
    "sofa-factory": {"probability": 0.1, "min_delay": 5, "max_delay": 8, "message": "Production backlog causing delays"},
    "global-distribution": {"probability": 0.1, "min_delay": 6, "max_delay": 10, "message": "Customs inspection delay"},
    "local-distribution": {"probability": 0.1, "min_delay": 3, "max_delay": 7, "message": "Traffic congestion affecting local delivery"}
}

# Generate a unique order ID with a prefix
def generate_order_id():
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"

# Select a random item from a list
def random_item(items):
    return random.choice(items)

# Determine if a failure should occur based on probability
def should_fail(service_name, order):
    # Check if this is a failure demo or has a failure scenario tag
    if order.get("demo") == "failure" and order.get("failure_service") == service_name:
        return True
    
    # Check if this is a background failure scenario
    if order.get("scenario") == "delivery-failure" and order.get("failure_service") == service_name:
        return True
    
    # Regular orders should NOT randomly fail
    return False

# Add latency if applicable for the service
def maybe_add_latency(service_name, span):
    if service_name in latency_scenarios:
        if random.random() < latency_scenarios[service_name]["probability"]:
            scenario = latency_scenarios[service_name]
            delay = random.uniform(scenario["min_delay"], scenario["max_delay"])
            reason = scenario["message"]
            span.set_attribute("latency.seconds", delay)
            span.set_attribute("latency.reason", reason)
            time.sleep(delay)
            return (True, delay, reason)
    return (False, None, None)

# SOFA SHOP SERVICE (entry point)
@app.route('/')
def home():
    if service_name == "sofa-shop":
        return """
        <h1>Sofa Shop - Trace Delivery Demo</h1>
        <p>Welcome to our sofa shop! Here you can order sofas and track their delivery through our system.</p>
        <h2>Endpoints:</h2>
        <ul>
            <li><a href="/catalog">View Catalog</a></li>
            <li><a href="/order">Place New Order</a> (random sofa)</li>
            <li><a href="/order-status?order_id=ORD-12345678">Check Order Status</a> (replace with your order ID)</li>
        </ul>
        <h2>Demo Scenarios:</h2>
        <ul>
            <li><a href="/demo/success">Successful Delivery Demo</a></li>
            <li><a href="/demo/failure">Failed Delivery Demo</a></li>
            <li><a href="/demo/latency">Delivery with Latency Demo</a></li>
        </ul>
        """
    else:
        return f"<h1>{service_name} service</h1><p>This service is part of the trace delivery demo.</p>"

# CATALOG ENDPOINT - SHOP SERVICE
@app.route('/catalog')
def catalog():
    if service_name != "sofa-shop":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    with tracer.start_as_current_span("view-catalog") as span:
        span.set_attribute("action", "view-catalog")
        return jsonify({"sofas": sofa_models})

# ORDER ENDPOINT - SHOP SERVICE
@app.route('/order')
def place_order():
    if service_name != "sofa-shop":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    with tracer.start_as_current_span("place-order") as span:
        # Generate order data
        order_id = generate_order_id()
        sofa = random_item(sofa_models)
        customer_type = random_item(customer_types)
        
        # Set span attributes
        span.set_attribute("order.id", order_id)
        span.set_attribute("sofa.model", sofa["id"])
        span.set_attribute("sofa.name", sofa["name"])
        span.set_attribute("sofa.price", sofa["price"])
        span.set_attribute("customer.type", customer_type)
        span.set_attribute("action", "place-order")
        
        # Create order
        order = {
            "order_id": order_id,
            "sofa": sofa,
            "customer_type": customer_type,
            "timestamp": time.time()
        }
        
        logger.info(f"New order placed: {order_id} for {sofa['name']}")
        
        # Forward to factory for manufacturing
        try:
            factory_url = os.environ.get('SERVICE_FACTORY_URL', 'http://sofa-factory:8081')
            headers = {}
            propagator.inject(headers)
            
            response = requests.post(
                f"{factory_url}/manufacture",
                json=order,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({
                    "message": "Order placed successfully!",
                    "order_id": order_id,
                    "sofa": sofa["name"],
                    "customer_type": customer_type,
                    "status": "manufacturing"
                })
            else:
                span.set_status(trace.StatusCode.ERROR)
                return jsonify({"error": "Failed to process order at factory", "details": response.text}), 500
        
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return jsonify({"error": f"Failed to connect to factory: {str(e)}"}), 500

# ORDER STATUS ENDPOINT - SHOP SERVICE
@app.route('/order-status')
def check_order_status():
    if service_name != "sofa-shop":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    order_id = request.args.get('order_id')
    if not order_id:
        return jsonify({"error": "No order ID provided"}), 400
    
    with tracer.start_as_current_span("check-order-status") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("action", "check-order-status")
        
        # In a real system, we would look up the order status in a database
        # For this demo, we'll return a random status
        statuses = ["manufactured", "picked up", "in global distribution", "in local distribution", "out for delivery", "delivered"]
        status = random_item(statuses)
        
        return jsonify({
            "order_id": order_id,
            "status": status,
            "last_update": time.time()
        })

# DELIVERY NOTIFICATION ENDPOINT - SHOP SERVICE
@app.route('/delivery-notification', methods=['POST'])
def delivery_notification():
    if service_name != "sofa-shop":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    notification = request.json
    order_id = notification.get("order_id")
    notification_type = notification.get("notification_type")
    delivery_time = notification.get("delivery_time")
    
    with tracer.start_as_current_span("process-delivery-notification") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("notification.type", notification_type)
        span.set_attribute("action", "process-notification")
        
        # Add a span event for processing the notification
        span.add_event("notification_received", {
            "order_id": order_id,
            "notification_type": notification_type,
            "timestamp": time.time()
        })
        
        # In a real app, we would update the order status in the database
        # For this demo, we'll just log it
        logger.info(f"Notification received: Order {order_id} has been {notification_type} at {delivery_time}")
        
        # Simulate update to database or other processing
        time.sleep(0.1)
        
        # Add span event for completing notification processing
        span.add_event("notification_processed", {
            "order_id": order_id,
            "success": True,
            "timestamp": time.time()
        })
        
        return jsonify({
            "status": "success",
            "message": f"Notification for order {order_id} processed successfully",
            "notification_type": notification_type
        })

# MANUFACTURE ENDPOINT - FACTORY SERVICE
@app.route('/manufacture', methods=['POST'])
def manufacture():
    if service_name != "sofa-factory":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    order = request.json
    order_id = order.get("order_id")
    sofa = order.get("sofa", {})
    is_background = order.get("background", False)
    
    with tracer.start_as_current_span("manufacture-sofa") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("sofa.model", sofa.get("id", "unknown"))
        span.set_attribute("sofa.name", sofa.get("name", "unknown"))
        span.set_attribute("action", "manufacture")
        span.set_attribute("background", is_background)
        
        # Add a span event for manufacture start
        span.add_event("manufacture_started", {
            "order_id": order_id,
            "timestamp": time.time(),
            "sofa_model": sofa.get("name", "unknown")
        })
        
        # Check for simulated failure
        if should_fail(service_name, order):
            error_message = failure_scenarios[service_name]["message"]
            logger.error(f"Manufacturing failure for order {order_id}: {error_message}")
            span.set_attribute("error", True)
            span.set_attribute("error.message", error_message)
            span.set_attribute("delivery.status", "failed")
            
            # Add span event for the failure
            span.add_event("manufacture_failed", {
                "error": error_message,
                "timestamp": time.time()
            })
            
            # Record an actual exception to show in the trace
            try:
                raise Exception(f"Manufacturing process failed: {error_message}")
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
            
            return jsonify({"error": error_message}), 500
        
        # Add latency if applicable
        latency_result = (False, None, None)
        if order.get("demo") == "latency" and order.get("latency_service") == "sofa-factory":
            # For demo, explicitly add latency
            delay = random.uniform(5, 8)
            reason = "Production backlog causing delays"
            span.set_attribute("latency.seconds", delay)
            span.set_attribute("latency.reason", reason)
            time.sleep(delay)
            latency_result = (True, delay, reason)
        else:
            # Check for random latency
            latency_result = maybe_add_latency(service_name, span)
        
        # If latency was added, record the event
        if latency_result[0]:
            delay = latency_result[1]
            reason = latency_result[2]
            span.add_event("manufacture_delayed", {
                "delay_seconds": delay,
                "reason": reason,
                "timestamp": time.time()
            })
        
        # Create nested spans for the assembly process
        # 1. Frame construction
        with tracer.start_as_current_span("frame-construction") as frame_span:
            frame_span.set_attribute("order.id", order_id)
            frame_span.set_attribute("assembly.step", "frame")
            frame_span.set_attribute("material", "hardwood")
            
            # Simulate work
            time.sleep(0.2)
            
            frame_span.add_event("frame_completed", {
                "timestamp": time.time(),
                "quality_check": "passed"
            })
        
        # 2. Spring installation
        with tracer.start_as_current_span("spring-installation") as spring_span:
            spring_span.set_attribute("order.id", order_id)
            spring_span.set_attribute("assembly.step", "springs")
            spring_span.set_attribute("spring.count", 24)
            
            # Simulate work
            time.sleep(0.15)
            
            spring_span.add_event("springs_installed", {
                "timestamp": time.time(),
                "tension_test": "passed"
            })
        
        # 3. Cushion preparation
        with tracer.start_as_current_span("cushion-preparation") as cushion_span:
            cushion_span.set_attribute("order.id", order_id)
            cushion_span.set_attribute("assembly.step", "cushions")
            
            # Sub-step: foam cutting
            with tracer.start_as_current_span("foam-cutting") as foam_span:
                foam_span.set_attribute("material", "memory foam")
                foam_span.set_attribute("density", "high")
                time.sleep(0.1)
            
            # Sub-step: fabric cutting
            with tracer.start_as_current_span("fabric-cutting") as fabric_span:
                fabric_span.set_attribute("material", "premium leather" if sofa.get("id") == "luxury-003" else "fabric")
                time.sleep(0.1)
            
            # Sub-step: cushion assembly
            with tracer.start_as_current_span("cushion-assembly") as assembly_span:
                assembly_span.set_attribute("components", "foam + fabric + zippers")
                time.sleep(0.15)
            
            cushion_span.add_event("cushions_completed", {
                "timestamp": time.time()
            })
        
        # 4. Final assembly
        with tracer.start_as_current_span("final-assembly") as final_span:
            final_span.set_attribute("order.id", order_id)
            final_span.set_attribute("assembly.step", "final")
            
            # Simulate work
            time.sleep(0.25)
            
            final_span.add_event("assembly_completed", {
                "timestamp": time.time(),
                "inspector": f"Inspector #{random.randint(1, 10)}"
            })
        
        # Simulate manufacturing time (in addition to the assembly steps)
        production_time = sofa.get("production_time", 3)
        time.sleep(production_time / 20)  # Scale down for demo purposes
        
        # Add event for manufacturing completion
        span.add_event("manufacture_completed", {
            "order_id": order_id,
            "timestamp": time.time(),
            "quality_check": "passed",
            "inspector_id": f"QA-{random.randint(100, 999)}"
        })
        
        logger.info(f"Completed manufacturing for order {order_id}")
        
        # Request pickup from global distribution
        try:
            distribution_url = os.environ.get('SERVICE_DISTRIBUTION_URL', 'http://global-distribution:8082')
            headers = {}
            propagator.inject(headers)
            
            response = requests.post(
                f"{distribution_url}/pickup",
                json=order,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({
                    "order_id": order_id,
                    "status": "manufactured",
                    "next_step": "global distribution"
                })
            else:
                error_message = f"Global distribution pickup failed: {response.text}"
                span.set_status(trace.StatusCode.ERROR)
                span.set_attribute("delivery.status", "failed")
                return jsonify({"error": error_message}), 500
        
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            span.set_attribute("delivery.status", "failed")
            return jsonify({"error": f"Failed to connect to global distribution: {str(e)}"}), 500

# PICKUP ENDPOINT - GLOBAL DISTRIBUTION SERVICE
@app.route('/pickup', methods=['POST'])
def global_pickup():
    if service_name != "global-distribution":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    order = request.json
    order_id = order.get("order_id")
    sofa = order.get("sofa", {})
    
    with tracer.start_as_current_span("global-distribution-pickup") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("sofa.model", sofa.get("id", "unknown"))
        distribution_center = random_item(distribution_centers["global"])
        span.set_attribute("distribution.center", distribution_center)
        span.set_attribute("action", "global-pickup")
        
        # Add event for starting the pickup process
        span.add_event("global_pickup_started", {
            "order_id": order_id,
            "distribution_center": distribution_center,
            "timestamp": time.time()
        })
        
        # Check for simulated failure
        if should_fail(service_name, order):
            error_message = failure_scenarios[service_name]["message"]
            logger.error(f"Global distribution failure for order {order_id}: {error_message}")
            span.set_attribute("error", True)
            span.set_attribute("error.message", error_message)
            span.set_attribute("delivery.status", "failed")
            
            # Add event for the failure
            span.add_event("global_pickup_failed", {
                "error": error_message,
                "timestamp": time.time()
            })
            
            # Record an actual exception to show in the trace
            try:
                raise Exception(f"Global distribution failed: {error_message}")
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
            
            return jsonify({"error": error_message}), 500
        
        # Add latency if applicable
        latency_result = (False, None, None)
        if order.get("demo") == "latency" and order.get("latency_service") == "global-distribution":
            # For demo, explicitly add latency
            delay = random.uniform(6, 10)
            reason = "Customs inspection delay"
            span.set_attribute("latency.seconds", delay)
            span.set_attribute("latency.reason", reason)
            time.sleep(delay)
            latency_result = (True, delay, reason)
        else:
            # Check for random latency
            latency_result = maybe_add_latency(service_name, span)
        
        # If latency was added, record the event
        if latency_result[0]:
            delay = latency_result[1]
            reason = latency_result[2]
            span.add_event("global_pickup_delayed", {
                "delay_seconds": delay,
                "reason": reason,
                "timestamp": time.time()
            })
        
        # Create nested spans for logistics operations
        with tracer.start_as_current_span("inventory-processing") as inventory_span:
            inventory_span.set_attribute("order.id", order_id)
            inventory_span.set_attribute("operation", "inventory")
            inventory_span.set_attribute("location", distribution_center)
            
            # Simulate inventory processing
            time.sleep(0.1)
            
            inventory_span.add_event("inventory_processed", {
                "warehouse": f"{distribution_center}-{random.randint(1, 5)}",
                "timestamp": time.time()
            })
        
        with tracer.start_as_current_span("global-logistics") as logistics_span:
            logistics_span.set_attribute("order.id", order_id)
            logistics_span.set_attribute("operation", "logistics")
            
            # Simulate logistics processing
            time.sleep(0.2)
            
            # Select random transport type
            transport = random.choice(["air", "sea", "road", "rail"])
            logistics_span.set_attribute("transport.type", transport)
            
            logistics_span.add_event("transport_arranged", {
                "type": transport,
                "carrier": f"Carrier-{random.randint(100, 999)}",
                "timestamp": time.time()
            })
        
        # Simulate processing time
        time.sleep(0.3)
        
        # Add event for successful pickup
        span.add_event("global_pickup_completed", {
            "order_id": order_id,
            "distribution_center": distribution_center,
            "timestamp": time.time()
        })
        
        logger.info(f"Global distribution processed order {order_id}")
        
        # Forward to local distribution
        try:
            local_url = os.environ.get('SERVICE_LOCAL_URL', 'http://local-distribution:8083')
            headers = {}
            propagator.inject(headers)
            
            response = requests.post(
                f"{local_url}/deliver",
                json=order,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                return jsonify({
                    "order_id": order_id,
                    "status": "in global distribution",
                    "next_step": "local distribution"
                })
            else:
                error_message = f"Local distribution handoff failed: {response.text}"
                span.set_status(trace.StatusCode.ERROR)
                span.set_attribute("delivery.status", "failed")
                return jsonify({"error": error_message}), 500
        
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            span.set_attribute("delivery.status", "failed")
            return jsonify({"error": f"Failed to connect to local distribution: {str(e)}"}), 500

# DELIVER ENDPOINT - LOCAL DISTRIBUTION SERVICE
@app.route('/deliver', methods=['POST'])
def local_deliver():
    if service_name != "local-distribution":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    order = request.json
    order_id = order.get("order_id")
    sofa = order.get("sofa", {})
    
    with tracer.start_as_current_span("local-distribution-delivery") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("sofa.model", sofa.get("id", "unknown"))
        distribution_center = random_item(distribution_centers["local"])
        span.set_attribute("distribution.center", distribution_center)
        span.set_attribute("action", "local-delivery")
        
        # Add event for starting local delivery
        span.add_event("local_delivery_started", {
            "order_id": order_id,
            "distribution_center": distribution_center,
            "timestamp": time.time()
        })
        
        # Check for simulated failure
        if should_fail(service_name, order):
            error_message = failure_scenarios[service_name]["message"]
            logger.error(f"Local distribution failure for order {order_id}: {error_message}")
            span.set_attribute("error", True)
            span.set_attribute("error.message", error_message)
            span.set_attribute("delivery.status", "failed")
            
            # Add event for the failure
            span.add_event("local_delivery_failed", {
                "error": error_message,
                "timestamp": time.time()
            })
            
            # Record an actual exception to show in the trace
            try:
                raise Exception(f"Local delivery failed: {error_message}")
            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.StatusCode.ERROR, str(e))
            
            return jsonify({"error": error_message}), 500
        
        # Add latency if applicable
        latency_result = (False, None, None)
        if order.get("demo") == "latency" and order.get("latency_service") == "local-distribution":
            # For demo, explicitly add latency
            delay = random.uniform(3, 7)
            reason = "Traffic congestion affecting local delivery"
            span.set_attribute("latency.seconds", delay)
            span.set_attribute("latency.reason", reason)
            time.sleep(delay)
            latency_result = (True, delay, reason)
        else:
            # Check for random latency
            latency_result = maybe_add_latency(service_name, span)
        
        # If latency was added, record the event
        if latency_result[0]:
            delay = latency_result[1]
            reason = latency_result[2]
            span.add_event("local_delivery_delayed", {
                "delay_seconds": delay,
                "reason": reason,
                "timestamp": time.time()
            })
        
        # Create nested spans for local delivery operations
        with tracer.start_as_current_span("package-preparation") as prep_span:
            prep_span.set_attribute("order.id", order_id)
            prep_span.set_attribute("operation", "package-prep")
            
            # Simulate packaging operations
            time.sleep(0.15)
            
            prep_span.add_event("package_prepared", {
                "packaging_type": "heavy-duty",
                "timestamp": time.time()
            })
        
        with tracer.start_as_current_span("delivery-route-planning") as route_span:
            route_span.set_attribute("order.id", order_id)
            route_span.set_attribute("operation", "route-planning")
            
            # Simulate route planning
            time.sleep(0.15)
            
            # Pick random delivery details
            vehicle = random.choice(["van", "truck", "specialized transport"])
            route_span.set_attribute("delivery.vehicle", vehicle)
            driver = f"Driver-{random.randint(100, 999)}"
            route_span.set_attribute("delivery.driver", driver)
            
            route_span.add_event("route_planned", {
                "vehicle": vehicle,
                "driver": driver,
                "estimated_arrival": time.time() + 3600,  # 1 hour from now
                "timestamp": time.time()
            })
        
        # Simulate processing time
        time.sleep(0.4)
        
        # Add event for successfully loaded for delivery
        span.add_event("local_delivery_loaded", {
            "order_id": order_id,
            "distribution_center": distribution_center,
            "timestamp": time.time()
        })
        
        logger.info(f"Local distribution processed order {order_id}")
        
        # Notify the shop that the order has been dispatched for delivery
        with tracer.start_as_current_span("notify-shop-delivery-dispatched") as notify_span:
            notify_span.set_attribute("order.id", order_id)
            notify_span.set_attribute("action", "notify-shop")
            
            # Create the notification
            notification = {
                "order_id": order_id,
                "sofa": sofa,
                "customer_type": order.get("customer_type", "regular"),
                "dispatch_time": time.time(),
                "notification_type": "delivery_dispatched",
                "vehicle": vehicle,
                "driver": driver,
                "distribution_center": distribution_center
            }
            
            # Send notification to shop
            shop_url = "http://sofa-shop:8080/delivery-notification"
            headers = {}
            propagator.inject(headers)
            
            notify_span.add_event("sending_notification", {
                "target": "sofa-shop",
                "notification_type": "delivery_dispatched",
                "timestamp": time.time()
            })
            
            # Try to send the notification - don't fail the whole delivery if this fails
            try:
                requests.post(
                    shop_url,
                    json=notification,
                    headers=headers,
                    timeout=1  # Short timeout so we don't block if shop is down
                )
                notify_span.add_event("notification_sent", {
                    "success": True,
                    "timestamp": time.time()
                })
            except Exception as notify_err:
                logger.warning(f"Failed to notify shop of dispatch: {str(notify_err)}")
                notify_span.record_exception(notify_err)
                notify_span.set_status(trace.StatusCode.ERROR, str(notify_err))
                notify_span.add_event("notification_failed", {
                    "success": False,
                    "error": str(notify_err),
                    "timestamp": time.time()
                })
        
        # Deliver to customer
        try:
            customer_url = os.environ.get('SERVICE_CUSTOMER_URL', 'http://customer-house:8084')
            headers = {}
            propagator.inject(headers)
            
            response = requests.post(
                f"{customer_url}/receive",
                json=order,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                span.add_event("local_delivery_completed", {
                    "order_id": order_id,
                    "timestamp": time.time()
                })
                return jsonify({
                    "order_id": order_id,
                    "status": "out for delivery",
                    "next_step": "customer delivery"
                })
            else:
                error_message = f"Customer delivery failed: {response.text}"
                span.set_status(trace.StatusCode.ERROR)
                span.set_attribute("delivery.status", "failed")
                return jsonify({"error": error_message}), 500
        
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            span.set_attribute("delivery.status", "failed")
            return jsonify({"error": f"Failed to connect to customer house: {str(e)}"}), 500

# RECEIVE ENDPOINT - CUSTOMER HOUSE SERVICE
@app.route('/receive', methods=['POST'])
def customer_receive():
    if service_name != "customer-house":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    order = request.json
    order_id = order.get("order_id")
    sofa = order.get("sofa", {})
    customer_type = order.get("customer_type", "regular")
    
    with tracer.start_as_current_span("customer-house-receive") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("sofa.model", sofa.get("id", "unknown"))
        span.set_attribute("customer.type", customer_type)
        span.set_attribute("action", "customer-receive")
        span.set_attribute("delivery.status", "delivered")
        
        # Add span event for delivery
        span.add_event("sofa_delivered", {
            "order_id": order_id,
            "timestamp": time.time(),
            "customer_type": customer_type
        })
        
        # Simulate final delivery
        time.sleep(0.2)
        
        logger.info(f"Order {order_id} successfully delivered to customer")
        
        # Generate customer satisfaction score - VIP customers are generally more satisfied
        satisfaction = random.randint(85, 100) if customer_type == "vip" else random.randint(70, 95)
        
        return jsonify({
            "order_id": order_id,
            "status": "delivered",
            "delivery_time": time.time(),
            "satisfaction": satisfaction
        })

# DEMO ENDPOINTS - SHOP SERVICE
@app.route('/demo/success')
def demo_success():
    if service_name != "sofa-shop":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    # Set environment variables for other services to not fail
    os.environ["FORCE_SUCCESS"] = "true"
    
    with tracer.start_as_current_span("demo-success-flow") as span:
        # Use a predefined sofa for the demo
        order_id = generate_order_id()
        sofa = sofa_models[0]  # Classic sofa
        customer_type = "regular"
        
        span.set_attribute("order.id", order_id)
        span.set_attribute("sofa.model", sofa["id"])
        span.set_attribute("sofa.name", sofa["name"])
        span.set_attribute("customer.type", customer_type)
        span.set_attribute("demo", "success-flow")
        
        # Create order
        order = {
            "order_id": order_id,
            "sofa": sofa,
            "customer_type": customer_type,
            "timestamp": time.time(),
            "demo": "success"
        }
        
        logger.info(f"Demo success flow initiated: {order_id}")
        
        # Forward to factory for manufacturing
        try:
            factory_url = os.environ.get('SERVICE_FACTORY_URL', 'http://sofa-factory:8081')
            headers = {}
            propagator.inject(headers)
            
            response = requests.post(
                f"{factory_url}/manufacture",
                json=order,
                headers=headers
            )
            
            if response.status_code == 200:
                return jsonify({
                    "message": "Success demo initiated!",
                    "order_id": order_id,
                    "sofa": sofa["name"],
                    "trace_id": span.get_span_context().trace_id
                })
            else:
                return jsonify({"error": "Demo failed to start", "details": response.text}), 500
        
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return jsonify({"error": f"Demo failed to start: {str(e)}"}), 500

@app.route('/demo/failure')
def demo_failure_endpoint():
    return demo_failure()

def demo_failure(failure_service=None, is_background=False):
    if service_name != "sofa-shop":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    # Set environment variables for this specific demo
    os.environ["FORCE_FAILURE"] = "true"
    os.environ["FAILURE_SERVICE"] = failure_service or request.args.get('service', 'sofa-factory')
    
    with tracer.start_as_current_span("background-failure-scenario" if is_background else "demo-failure-flow") as span:
        # Use a predefined sofa for the demo
        order_id = generate_order_id()
        sofa = sofa_models[2]  # Luxury sofa
        customer_type = "premium"
        
        span.set_attribute("order.id", order_id)
        span.set_attribute("sofa.model", sofa["id"])
        span.set_attribute("sofa.name", sofa["name"])
        span.set_attribute("customer.type", customer_type)
        span.set_attribute("demo", "failure-flow")
        span.set_attribute("background", is_background)
        span.set_attribute("scenario", "delivery-failure")
        span.set_attribute("failure_service", os.environ["FAILURE_SERVICE"])
        
        # Create order
        order = {
            "order_id": order_id,
            "sofa": sofa,
            "customer_type": customer_type,
            "timestamp": time.time(),
            "demo": "failure",
            "background": is_background,
            "scenario": "delivery-failure",
            "failure_service": os.environ["FAILURE_SERVICE"]
        }
        
        logger.info(f"{'Background' if is_background else 'Demo'} failure flow initiated: {order_id} (failure in {os.environ['FAILURE_SERVICE']})")
        
        # Forward to factory for manufacturing
        try:
            factory_url = os.environ.get('SERVICE_FACTORY_URL', 'http://sofa-factory:8081')
            headers = {}
            propagator.inject(headers)
            
            response = requests.post(
                f"{factory_url}/manufacture",
                json=order,
                headers=headers
            )
            
            if is_background:
                return None
            else:
                return jsonify({
                    "message": "Failure demo initiated!",
                    "order_id": order_id,
                    "sofa": sofa["name"],
                    "failure_service": os.environ["FAILURE_SERVICE"],
                    "trace_id": span.get_span_context().trace_id
                })
        
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            if is_background:
                logger.error(f"Background demo failed to start: {str(e)}")
                return None
            else:
                return jsonify({"error": f"Demo failed to start: {str(e)}"}), 500

@app.route('/demo/latency')
def demo_latency_endpoint():
    return demo_latency()

def demo_latency(latency_service=None, is_background=False):
    if service_name != "sofa-shop":
        return jsonify({"error": f"Not available in {service_name}"}), 404
    
    # Set environment variables for this specific demo
    os.environ["FORCE_LATENCY"] = "true"
    os.environ["LATENCY_SERVICE"] = latency_service or request.args.get('service', 'sofa-factory')
    
    with tracer.start_as_current_span("background-latency-scenario" if is_background else "demo-latency-flow") as span:
        # Use a predefined sofa for the demo
        order_id = generate_order_id()
        sofa = sofa_models[4]  # Limited edition
        customer_type = "vip"
        
        span.set_attribute("order.id", order_id)
        span.set_attribute("sofa.model", sofa["id"])
        span.set_attribute("sofa.name", sofa["name"])
        span.set_attribute("customer.type", customer_type)
        span.set_attribute("demo", "latency-flow")
        span.set_attribute("background", is_background)
        span.set_attribute("scenario", "delivery-latency")
        span.set_attribute("latency_service", os.environ["LATENCY_SERVICE"])
        
        # Create order
        order = {
            "order_id": order_id,
            "sofa": sofa,
            "customer_type": customer_type,
            "timestamp": time.time(),
            "demo": "latency",
            "background": is_background,
            "scenario": "delivery-latency",
            "latency_service": os.environ["LATENCY_SERVICE"]
        }
        
        logger.info(f"{'Background' if is_background else 'Demo'} latency flow initiated: {order_id} (latency in {os.environ['LATENCY_SERVICE']})")
        
        # Forward to factory for manufacturing
        try:
            factory_url = os.environ.get('SERVICE_FACTORY_URL', 'http://sofa-factory:8081')
            headers = {}
            propagator.inject(headers)
            
            response = requests.post(
                f"{factory_url}/manufacture",
                json=order,
                headers=headers
            )
            
            if is_background:
                return None
            else:
                return jsonify({
                    "message": "Latency demo initiated!",
                    "order_id": order_id,
                    "sofa": sofa["name"],
                    "latency_service": os.environ["LATENCY_SERVICE"],
                    "trace_id": span.get_span_context().trace_id
                })
        
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            if is_background:
                logger.error(f"Background demo failed to start: {str(e)}")
                return None
            else:
                return jsonify({"error": f"Demo failed to start: {str(e)}"}), 500

# Background trace generation functions
def generate_random_trace():
    """Generate a random trace in the background"""
    if service_name != "sofa-shop":
        return  # Only the shop should generate random traces
    
    # Randomly choose between normal order, error scenario, or latency scenario
    scenario_type = random.choices(
        ["normal", "error", "latency"], 
        weights=[0.7, 0.15, 0.15], 
        k=1
    )[0]
    
    try:
        if scenario_type == "normal":
            # Normal order flow
            order_id = generate_order_id()
            sofa = random_item(sofa_models)
            customer_type = random_item(customer_types)
            
            with tracer.start_as_current_span("background-successful-order") as span:
                span.set_attribute("order.id", order_id)
                span.set_attribute("sofa.model", sofa["id"])
                span.set_attribute("sofa.name", sofa["name"])
                span.set_attribute("sofa.price", sofa["price"])
                span.set_attribute("customer.type", customer_type)
                span.set_attribute("action", "place-order")
                span.set_attribute("background", True)
                span.set_attribute("scenario", "successful-delivery")
                
                # Add a span event for order creation
                span.add_event("order_created", {
                    "order_id": order_id,
                    "timestamp": time.time(),
                    "customer_type": customer_type,
                    "scenario": "successful-delivery"
                })
                
                # Create order
                order = {
                    "order_id": order_id,
                    "sofa": sofa,
                    "customer_type": customer_type,
                    "timestamp": time.time(),
                    "background": True,
                    "scenario": "successful-delivery"
                }
                
                logger.info(f"Background successful order placed: {order_id} for {sofa['name']}")
                
                # Forward to factory for manufacturing
                factory_url = os.environ.get('SERVICE_FACTORY_URL', 'http://sofa-factory:8081')
                headers = {}
                propagator.inject(headers)
                
                requests.post(
                    f"{factory_url}/manufacture",
                    json=order,
                    headers=headers
                )
        
        elif scenario_type == "error":
            # Error scenario
            failure_service = random.choice(list(failure_scenarios.keys()))
            demo_failure(failure_service=failure_service, is_background=True)
            
        elif scenario_type == "latency":
            # Latency scenario
            latency_service = random.choice(list(latency_scenarios.keys()))
            demo_latency(latency_service=latency_service, is_background=True)
            
    except Exception as e:
        logger.error(f"Error generating background trace: {str(e)}")

def trace_generator_thread():
    """Background thread that generates traces at regular intervals"""
    while True:
        try:
            # Only generate random traces if we're the sofa-shop service
            if service_name == "sofa-shop":
                generate_random_trace()
                
            # Wait between 20-60 seconds before generating the next trace
            delay = random.uniform(10, 20)
            logger.info(f"Next background trace in {delay:.2f} seconds")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Error in trace generation thread: {e}")
            time.sleep(10)  # Wait before retrying

if __name__ == '__main__':
    logger.info(f"Starting {service_name} service on port {service_port}")
    
    # Start the background trace generator thread (only for sofa-shop)
    if service_name == "sofa-shop":
        trace_thread = threading.Thread(target=trace_generator_thread, daemon=True)
        trace_thread.start()
        logger.info("Started background trace generator")
    
    app.run(host='0.0.0.0', port=service_port) 