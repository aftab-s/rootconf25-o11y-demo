import os
import random
import time
import threading
import logging
import uuid
from flask import Flask, request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import requests
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure the tracer
resource = Resource.create(attributes={
    SERVICE_NAME: "trace-demo-tail-sampled"
})
trace.set_tracer_provider(TracerProvider(resource=resource))

# Configure the OTLP exporter using environment variables
# OTEL_EXPORTER_OTLP_ENDPOINT will be used automatically
otlp_exporter = OTLPSpanExporter(endpoint="http://alloy:4317/v1/traces", insecure=True)
span_processor = BatchSpanProcessor(span_exporter=otlp_exporter, max_export_batch_size=1)
trace.get_tracer_provider().add_span_processor(span_processor)

# Create a tracer
tracer = trace.get_tracer(__name__)

# Create a propagator for handling trace context
propagator = TraceContextTextMapPropagator()

# Create a Flask application
app = Flask(__name__)

# Instrument Flask
FlaskInstrumentor().instrument_app(app)

# Instrument requests
RequestsInstrumentor().instrument()

# Background trace generation functions
def generate_simple_trace():
    with tracer.start_as_current_span("simple-operation") as span:
        span.set_attribute("operation.type", "simple")
        span.set_attribute("operation.value", random.randint(1, 100))
        # Set a sampling-relevant attribute
        span.set_attribute("test_attr_key_1", "test_attr_val_1" if random.random() < 0.3 else "other_value")
        time.sleep(0.1)  # Simulate work
        logger.info("Generated simple trace")

def generate_nested_trace():
    with tracer.start_as_current_span("parent-operation") as parent:
        parent.set_attribute("operation.type", "parent")
        parent.set_attribute("key1", random.randint(1, 100))  # For numeric attribute sampling
        time.sleep(0.05)  # Simulate work
        
        with tracer.start_as_current_span("child-operation-1") as child1:
            child1.set_attribute("operation.type", "child")
            child1.set_attribute("child.number", 1)
            child1.set_attribute("key2", "value1" if random.random() < 0.5 else "other_value")  # For string attribute sampling
            time.sleep(0.05)  # Simulate work
            
        with tracer.start_as_current_span("child-operation-2") as child2:
            child2.set_attribute("operation.type", "child")
            child2.set_attribute("child.number", 2)
            time.sleep(0.05)  # Simulate work
            
            with tracer.start_as_current_span("grandchild-operation") as grandchild:
                grandchild.set_attribute("operation.type", "grandchild")
                time.sleep(0.05)  # Simulate work
                
        logger.info("Generated nested trace")

def generate_error_trace():
    with tracer.start_as_current_span("error-operation") as span:
        span.set_attribute("operation.type", "error")
        try:
            # Simulate an error
            result = 1 / 0
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            logger.info("Generated error trace")

def generate_high_latency_trace():
    with tracer.start_as_current_span("high-latency-operation") as span:
        span.set_attribute("operation.type", "high-latency")
        # Add a randomized latency between 3-10 seconds
        latency = random.uniform(3.0, 10.0)
        span.set_attribute("latency.seconds", latency)
        time.sleep(latency)  # Simulate high latency work
        logger.info(f"Generated high latency trace with {latency:.2f}s delay")

def generate_delayed_chain_trace():
    """Generate a chain of service calls with service D having high latency"""
    try:
        with tracer.start_as_current_span("delayed-chain-root") as span:
            span.set_attribute("operation.step", "start")
            span.set_attribute("operation.type", "delayed-chain")
            
            # Start the chain with Service A
            req_id = random.randint(1000, 9999)
            
            # Instead of making HTTP calls in the background, simulate the chain directly
            with tracer.start_as_current_span("service-a-handler") as span_a:
                span_a.set_attribute("service", "A")
                span_a.set_attribute("request.id", str(req_id))
                span_a.set_attribute("service.latency", "normal")
                span_a.set_attribute("http.url", "/delayed/service-a")
                time.sleep(0.1)  # Normal latency
                
                with tracer.start_as_current_span("service-b-handler") as span_b:
                    span_b.set_attribute("service", "B")
                    span_b.set_attribute("request.id", str(req_id))
                    span_b.set_attribute("service.latency", "normal")
                    span_b.set_attribute("http.url", "/delayed/service-b")
                    time.sleep(0.15)  # Normal latency
                    
                    with tracer.start_as_current_span("service-c-handler") as span_c:
                        span_c.set_attribute("service", "C")
                        span_c.set_attribute("request.id", str(req_id))
                        span_c.set_attribute("service.latency", "normal")
                        span_c.set_attribute("http.url", "/delayed/service-c")
                        time.sleep(0.2)  # Normal latency
                        
                        with tracer.start_as_current_span("service-d-handler") as span_d:
                            span_d.set_attribute("service", "D")
                            span_d.set_attribute("request.id", str(req_id))
                            span_d.set_attribute("service.latency", "high")
                            span_d.set_attribute("latency.category", "bottleneck")
                            span_d.set_attribute("http.url", "/delayed/service-d")
                            
                            # This service consistently has high latency (3-4 seconds)
                            delay = random.uniform(3.0, 4.0)
                            span_d.set_attribute("latency.seconds", delay)
                            time.sleep(delay)  # High latency
                            
                            with tracer.start_as_current_span("service-e-handler") as span_e:
                                span_e.set_attribute("service", "E")
                                span_e.set_attribute("request.id", str(req_id))
                                span_e.set_attribute("service.latency", "normal")
                                span_e.set_attribute("http.url", "/delayed/service-e")
                                time.sleep(0.1)  # Normal latency
            
            logger.info("Generated delayed chain trace with high latency in Service D")
    except Exception as e:
        logger.error(f"Error generating delayed chain trace: {e}")

# New function for generating true multi-service traces
def generate_multi_service_trace_bg():
    """Generate a trace that spans multiple services with true service.name differentiation"""
    try:
        # Create a unique trace ID for correlating spans
        trace_id = str(uuid.uuid4())
        transaction_id = str(uuid.uuid4())[:8]
        logger.info(f"Generating multi-service trace. Transaction ID: {transaction_id}")
        
        # Simulate a microservice architecture with:
        # 1. Frontend service (web-ui)
        # 2. API Gateway (api-gateway)
        # 3. Authentication service (auth-service)
        # 4. User service (user-service)
        # 5. Notification service (notification-service)
        # 6. Database service (db-service)
        
        # Create a custom resource for each service
        web_ui_resource = Resource.create(attributes={SERVICE_NAME: "web-ui"})
        api_gw_resource = Resource.create(attributes={SERVICE_NAME: "api-gateway"})
        auth_resource = Resource.create(attributes={SERVICE_NAME: "auth-service"})
        user_resource = Resource.create(attributes={SERVICE_NAME: "user-service"})
        notif_resource = Resource.create(attributes={SERVICE_NAME: "notification-service"})
        db_resource = Resource.create(attributes={SERVICE_NAME: "db-service"})
        
        # Create tracers for each service
        web_ui_tracer = trace.get_tracer("web-ui-tracer", resource=web_ui_resource)
        api_gw_tracer = trace.get_tracer("api-gw-tracer", resource=api_gw_resource)
        auth_tracer = trace.get_tracer("auth-tracer", resource=auth_resource)
        user_tracer = trace.get_tracer("user-tracer", resource=user_resource)
        notif_tracer = trace.get_tracer("notif-tracer", resource=notif_resource)
        db_tracer = trace.get_tracer("db-tracer", resource=db_resource)
        
        # 1. Frontend service (web-ui) - User logs in
        with web_ui_tracer.start_as_current_span("login-page-render") as web_span:
            web_span.set_attribute("component", "web-ui")
            web_span.set_attribute("transaction.id", transaction_id)
            web_span.set_attribute("user.action", "login")
            web_span.set_attribute("http.method", "GET")
            web_span.set_attribute("http.url", "/login")
            time.sleep(0.1)
            
            # 2. Send login request to API Gateway
            with api_gw_tracer.start_as_current_span("api-gateway-login-handler") as api_span:
                api_span.set_attribute("component", "api-gateway")
                api_span.set_attribute("transaction.id", transaction_id)
                api_span.set_attribute("endpoint", "/api/v1/login")
                api_span.set_attribute("http.method", "POST")
                time.sleep(0.15)
                
                # 3. API Gateway calls Authentication Service
                with auth_tracer.start_as_current_span("authenticate-user") as auth_span:
                    auth_span.set_attribute("component", "auth-service")
                    auth_span.set_attribute("transaction.id", transaction_id)
                    auth_span.set_attribute("auth.method", "password")
                    time.sleep(0.2)
                    
                    # 4. Auth service calls User Service to retrieve user details
                    with user_tracer.start_as_current_span("get-user-details") as user_span:
                        user_span.set_attribute("component", "user-service")
                        user_span.set_attribute("transaction.id", transaction_id)
                        user_span.set_attribute("user.id", f"user_{random.randint(1000, 9999)}")
                        
                        # 5. User service calls DB Service
                        with db_tracer.start_as_current_span("db-query") as db_span:
                            db_span.set_attribute("component", "db-service")
                            db_span.set_attribute("transaction.id", transaction_id)
                            db_span.set_attribute("db.operation", "SELECT")
                            db_span.set_attribute("db.table", "users")
                            
                            # Randomly introduce database latency
                            if random.random() < 0.3:
                                delay = random.uniform(0.5, 1.5)
                                db_span.set_attribute("db.latency", delay)
                                db_span.set_attribute("latency.category", "slow-query")
                                time.sleep(delay)
                            else:
                                time.sleep(0.1)
                
                # 6. After successful login, send notification
                with notif_tracer.start_as_current_span("send-login-notification") as notif_span:
                    notif_span.set_attribute("component", "notification-service")
                    notif_span.set_attribute("transaction.id", transaction_id)
                    notif_span.set_attribute("notification.type", "login_alert")
                    notif_span.set_attribute("notification.channel", random.choice(["email", "sms", "push"]))
                    time.sleep(0.15)
        
        logger.info(f"Generated multi-service trace with transaction ID: {transaction_id}")
        return transaction_id
    except Exception as e:
        logger.error(f"Error generating multi-service trace: {e}")
        return None

def generate_trace_batch():
    """Generates a batch of different trace types"""
    trace_generators = [
        generate_simple_trace,
        generate_nested_trace,
        generate_error_trace,
        generate_high_latency_trace,
        generate_delayed_chain_trace,
        generate_multi_service_trace_bg  # Add the new trace type
    ]
    
    # Randomly select which traces to generate with weighted probabilities
    weights = [0.20, 0.20, 0.15, 0.1, 0.15, 0.2]  # Add weight for multi-service trace
    
    for _ in range(random.randint(3, 8)):  # Generate 3-8 traces per batch
        selected_generator = random.choices(trace_generators, weights=weights, k=1)[0]
        selected_generator()
        time.sleep(random.uniform(0.1, 0.5))  # Small delay between traces

def trace_generator_thread():
    """Background thread that generates traces at regular intervals"""
    while True:
        try:
            generate_trace_batch()
            # Wait between 5-15 seconds before generating the next batch
            delay = random.uniform(5, 15)
            logger.info(f"Next trace batch in {delay:.2f} seconds")
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Error in trace generation: {e}")
            time.sleep(5)  # Wait before retrying

# API endpoints
@app.route('/')
def home():
    return """
    <h1>OpenTelemetry Tail Sampling Demo</h1>
    <p>This app demonstrates OpenTelemetry tracing with Tail Sampling using Grafana Alloy.</p>
    <p>The app automatically generates various types of traces in the background.</p>
    <p>You can also trigger trace generation manually using these endpoints:</p>
    <ul>
        <li><a href="/simple">Simple Trace</a></li>
        <li><a href="/nested">Nested Trace</a></li>
        <li><a href="/error">Error Trace</a></li>
        <li><a href="/high-latency">High Latency Trace</a></li>
        <li><a href="/chain">Chain of Services</a></li>
        <li><a href="/delayed-chain">Delayed Chain (with Service D having high latency)</a></li>
        <li><a href="/multi-service">Multi-Service Trace (with different service.name values)</a></li>
        <li><a href="/batch">Generate Trace Batch</a></li>
    </ul>
    """

@app.route('/simple')
def simple_trace():
    generate_simple_trace()
    return {"status": "ok", "message": "Simple trace generated"}

@app.route('/nested')
def nested_trace():
    generate_nested_trace()
    return {"status": "ok", "message": "Nested trace generated"}

@app.route('/error')
def error_trace():
    generate_error_trace()
    return {"status": "ok", "message": "Error trace generated"}

@app.route('/high-latency')
def high_latency_trace():
    generate_high_latency_trace()
    return {"status": "ok", "message": "High latency trace generated"}

@app.route('/batch')
def batch_trace():
    generate_trace_batch()
    return {"status": "ok", "message": "Trace batch generated"}

@app.route('/multi-service')
def multi_service_trace():
    transaction_id = generate_multi_service_trace_bg()
    return {
        "status": "ok", 
        "message": "Multi-service trace generated", 
        "transaction_id": transaction_id,
        "services": ["web-ui", "api-gateway", "auth-service", "user-service", "notification-service", "db-service"]
    }

@app.route('/chain')
def chain_trace():
    with tracer.start_as_current_span("chain-root") as span:
        span.set_attribute("operation.step", "start")
        
        # Simulate a chain of service calls
        try:
            # Call ourselves to simulate microservice calls
            # In a real world example these would be different services
            service_b_url = f"http://localhost:8080/service/b?id={random.randint(1000, 9999)}"
            response = requests.get(service_b_url)
            return {"status": "ok", "message": "Chain trace generated", "data": response.json()}
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return {"status": "error", "message": "Failed to complete chain"}

@app.route('/service/b')
def service_b():
    req_id = request.args.get('id', 'unknown')
    with tracer.start_as_current_span(f"service-b-handler") as span:
        span.set_attribute("service", "B")
        span.set_attribute("request.id", req_id)
        span.set_attribute("http.url", "/service/b")  # For URL-based sampling
        time.sleep(0.1)  # Simulate work
        
        # Call service C
        service_c_url = f"http://localhost:8080/service/c?id={req_id}"
        response = requests.get(service_c_url)
        return {"status": "ok", "message": "Service B completed", "data": response.json()}

@app.route('/service/c')
def service_c():
    req_id = request.args.get('id', 'unknown')
    with tracer.start_as_current_span(f"service-c-handler") as span:
        span.set_attribute("service", "C")
        span.set_attribute("request.id", req_id)
        span.set_attribute("http.url", "/service/c")  # For URL-based sampling
        time.sleep(0.15)  # Simulate work
        
        # Randomly fail sometimes to show error traces
        if random.random() < 0.2:  # 20% chance of failure
            span.set_status(trace.StatusCode.ERROR, "Random failure")
            return {"status": "error", "message": "Service C failed randomly"}
        
        return {"status": "ok", "message": "Service C completed successfully"}

# Add the delayed chain implementation
@app.route('/delayed-chain')
def delayed_chain_trace_endpoint():
    with tracer.start_as_current_span("delayed-chain-root") as span:
        span.set_attribute("operation.step", "start")
        span.set_attribute("operation.type", "delayed-chain")
        
        try:
            # Start the chain with Service A
            service_a_url = f"http://localhost:8080/delayed/service-a?id={random.randint(1000, 9999)}"
            response = requests.get(service_a_url)
            return {
                "status": "ok", 
                "message": "Delayed chain trace generated", 
                "data": response.json()
            }
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return {"status": "error", "message": "Failed to complete delayed chain"}

@app.route('/delayed/service-a')
def delayed_service_a():
    req_id = request.args.get('id', 'unknown')
    with tracer.start_as_current_span("service-a-handler") as span:
        span.set_attribute("service", "A")
        span.set_attribute("request.id", req_id)
        span.set_attribute("service.latency", "normal")
        span.set_attribute("http.url", "/delayed/service-a")
        time.sleep(0.1)  # Normal latency
        
        # Call service B
        service_b_url = f"http://localhost:8080/delayed/service-b?id={req_id}"
        response = requests.get(service_b_url)
        return {"status": "ok", "message": "Service A completed", "data": response.json()}

@app.route('/delayed/service-b')
def delayed_service_b():
    req_id = request.args.get('id', 'unknown')
    with tracer.start_as_current_span("service-b-handler") as span:
        span.set_attribute("service", "B")
        span.set_attribute("request.id", req_id)
        span.set_attribute("service.latency", "normal")
        span.set_attribute("http.url", "/delayed/service-b")
        time.sleep(0.15)  # Normal latency
        
        # Call service C
        service_c_url = f"http://localhost:8080/delayed/service-c?id={req_id}"
        response = requests.get(service_c_url)
        return {"status": "ok", "message": "Service B completed", "data": response.json()}

@app.route('/delayed/service-c')
def delayed_service_c():
    req_id = request.args.get('id', 'unknown')
    with tracer.start_as_current_span("service-c-handler") as span:
        span.set_attribute("service", "C")
        span.set_attribute("request.id", req_id)
        span.set_attribute("service.latency", "normal")
        span.set_attribute("http.url", "/delayed/service-c")
        time.sleep(0.2)  # Normal latency
        
        # Call the slow service D
        service_d_url = f"http://localhost:8080/delayed/service-d?id={req_id}"
        response = requests.get(service_d_url)
        return {"status": "ok", "message": "Service C completed", "data": response.json()}

@app.route('/delayed/service-d')
def delayed_service_d():
    req_id = request.args.get('id', 'unknown')
    with tracer.start_as_current_span("service-d-handler") as span:
        span.set_attribute("service", "D")
        span.set_attribute("request.id", req_id)
        span.set_attribute("service.latency", "high")
        span.set_attribute("latency.category", "bottleneck")
        span.set_attribute("http.url", "/delayed/service-d")
        
        # This service consistently has high latency (3-4 seconds)
        delay = random.uniform(3.0, 4.0)
        span.set_attribute("latency.seconds", delay)
        time.sleep(delay)  # High latency
        
        # Call final service E
        service_e_url = f"http://localhost:8080/delayed/service-e?id={req_id}"
        response = requests.get(service_e_url)
        return {"status": "ok", "message": "Service D completed (with delay)", "data": response.json()}

@app.route('/delayed/service-e')
def delayed_service_e():
    req_id = request.args.get('id', 'unknown')
    with tracer.start_as_current_span("service-e-handler") as span:
        span.set_attribute("service", "E")
        span.set_attribute("request.id", req_id)
        span.set_attribute("service.latency", "normal")
        span.set_attribute("http.url", "/delayed/service-e")
        time.sleep(0.1)  # Normal latency
        
        return {"status": "ok", "message": "Service E completed (chain end)"}

if __name__ == '__main__':
    # Start the background trace generator thread
    trace_thread = threading.Thread(target=trace_generator_thread, daemon=True)
    trace_thread.start()
    
    logger.info("Starting the application with background trace generation")
    app.run(host='0.0.0.0', port=8080) 