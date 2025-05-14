import os
import random
import time
import uuid
from flask import Flask, request
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
import requests

# Configure the tracer
resource = Resource.create(attributes={
    SERVICE_NAME: "trace-demo"
})
trace.set_tracer_provider(TracerProvider(resource=resource))

# Configure the OTLP exporter using environment variables
# OTEL_EXPORTER_OTLP_ENDPOINT will be used automatically
otlp_exporter = OTLPSpanExporter(endpoint="http://alloy:4317/v1/traces", insecure=True)
span_processor = BatchSpanProcessor(span_exporter=otlp_exporter, max_export_batch_size=1)
trace.get_tracer_provider().add_span_processor(span_processor)

# Create a tracer
tracer = trace.get_tracer(__name__)

# Create a Flask application
app = Flask(__name__)

# Instrument Flask
FlaskInstrumentor().instrument_app(app)

# Instrument requests
RequestsInstrumentor().instrument()

@app.route('/')
def home():
    return """
    <h1>OpenTelemetry Service Graph Demo</h1>
    <p>This app demonstrates OpenTelemetry tracing with Grafana Alloy and service graph generation.</p>
    <ul>
        <li><a href="/simple">Simple Trace</a></li>
        <li><a href="/nested">Nested Trace</a></li>
        <li><a href="/error">Error Trace</a></li>
        <li><a href="/chain">Chain of Services</a></li>
        <li><a href="/delayed-chain">Delayed Chain (with Service D having high latency)</a></li>
        <li><a href="/multi-service">Multi-Service Trace (with different service.name values)</a></li>
    </ul>
    """

@app.route('/simple')
def simple_trace():
    with tracer.start_as_current_span("simple-operation") as span:
        span.set_attribute("operation.type", "simple")
        span.set_attribute("operation.value", random.randint(1, 100))
        time.sleep(0.1)  # Simulate work
        return {"status": "ok", "message": "Simple trace generated"}

@app.route('/nested')
def nested_trace():
    with tracer.start_as_current_span("parent-operation") as parent:
        parent.set_attribute("operation.type", "parent")
        time.sleep(0.05)  # Simulate work
        
        with tracer.start_as_current_span("child-operation-1") as child1:
            child1.set_attribute("operation.type", "child")
            child1.set_attribute("child.number", 1)
            time.sleep(0.05)  # Simulate work
            
        with tracer.start_as_current_span("child-operation-2") as child2:
            child2.set_attribute("operation.type", "child")
            child2.set_attribute("child.number", 2)
            time.sleep(0.05)  # Simulate work
            
            with tracer.start_as_current_span("grandchild-operation") as grandchild:
                grandchild.set_attribute("operation.type", "grandchild")
                time.sleep(0.05)  # Simulate work
                
        return {"status": "ok", "message": "Nested trace generated"}

@app.route('/error')
def error_trace():
    with tracer.start_as_current_span("error-operation") as span:
        span.set_attribute("operation.type", "error")
        try:
            # Simulate an error
            result = 1 / 0
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            return {"status": "error", "message": "Error trace generated"}

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
        time.sleep(0.15)  # Simulate work
        
        # Randomly fail sometimes to show error traces
        if random.random() < 0.2:  # 20% chance of failure
            span.set_status(trace.StatusCode.ERROR, "Random failure")
            return {"status": "error", "message": "Service C failed randomly"}
        
        return {"status": "ok", "message": "Service C completed successfully"}

# New delayed chain implementation
@app.route('/delayed-chain')
def delayed_chain_trace():
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
        span.set_attribute("client.service.name", "frontend")
        span.set_attribute("request.id", req_id)
        span.set_attribute("service.latency", "normal")
        span.set_attribute("http.method", "GET")
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
        span.set_attribute("client.service.name", "service-a")
        span.set_attribute("request.id", req_id)
        span.set_attribute("service.latency", "normal")
        span.set_attribute("http.method", "GET")
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
        span.set_attribute("client.service.name", "service-b")
        span.set_attribute("request.id", req_id)
        span.set_attribute("service.latency", "normal")
        span.set_attribute("http.method", "GET")
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
        span.set_attribute("client.service.name", "service-c")
        span.set_attribute("request.id", req_id)
        span.set_attribute("service.latency", "high")
        span.set_attribute("latency.category", "bottleneck")
        span.set_attribute("http.method", "GET")
        
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
        span.set_attribute("client.service.name", "service-d")
        span.set_attribute("request.id", req_id)
        span.set_attribute("service.latency", "normal")
        span.set_attribute("http.method", "GET")
        time.sleep(0.1)  # Normal latency
        
        return {"status": "ok", "message": "Service E completed (chain end)"}

@app.route('/multi-service')
def multi_service_trace():
    transaction_id = generate_multi_service_trace()
    return {
        "status": "ok", 
        "message": "Multi-service trace generated", 
        "transaction_id": transaction_id,
        "services": ["web-ui", "api-gateway", "auth-service", "user-service", "notification-service", "db-service"]
    }
# code fixed thanks to @hedss
def generate_multi_service_trace():
    """Generate a trace that spans multiple services with true service.name differentiation"""
    try:
        # Create a unique transaction ID for correlating spans
        transaction_id = str(uuid.uuid4())[:8]

        # Create a custom resource for each service
        web_ui_resource = Resource.create(attributes={SERVICE_NAME: "web-ui"})
        api_gw_resource = Resource.create(attributes={SERVICE_NAME: "api-gateway"})
        auth_resource = Resource.create(attributes={SERVICE_NAME: "auth-service"})
        user_resource = Resource.create(attributes={SERVICE_NAME: "user-service"})
        notif_resource = Resource.create(attributes={SERVICE_NAME: "notification-service"})
        db_resource = Resource.create(attributes={SERVICE_NAME: "db-service"})

        # Create trace providers with each resource
        web_ui_provider = TracerProvider(resource=web_ui_resource)
        api_gw_provider = TracerProvider(resource=api_gw_resource)
        auth_provider = TracerProvider(resource=auth_resource)
        user_provider = TracerProvider(resource=user_resource)
        notif_provider = TracerProvider(resource=notif_resource)
        db_provider = TracerProvider(resource=db_resource)

        # Connect the providers to the same OTLP exporter via span processors
        web_ui_provider.add_span_processor(span_processor)
        api_gw_provider.add_span_processor(span_processor)
        auth_provider.add_span_processor(span_processor)
        user_provider.add_span_processor(span_processor)
        notif_provider.add_span_processor(span_processor)
        db_provider.add_span_processor(span_processor)

        # Create tracers for each service using their respective providers
        web_ui_tracer = web_ui_provider.get_tracer("web-ui-tracer")
        api_gw_tracer = api_gw_provider.get_tracer("api-gw-tracer")
        auth_tracer = auth_provider.get_tracer("auth-tracer")
        user_tracer = user_provider.get_tracer("user-tracer")
        notif_tracer = notif_provider.get_tracer("notif-tracer")
        db_tracer = db_provider.get_tracer("db-tracer")

        # 1. Frontend service (web-ui) - User logs in
        with web_ui_tracer.start_as_current_span("login-page-render", kind=trace.SpanKind.SERVER) as web_span:
            web_span.set_attribute("component", "web-ui")
            web_span.set_attribute("transaction.id", transaction_id)
            web_span.set_attribute("user.action", "login")
            web_span.set_attribute("http.method", "GET")
            web_span.set_attribute("http.url", "/login")
            time.sleep(0.1)

            # 2. Send login request to API Gateway
            with web_ui_tracer.start_as_current_span("api-gateway-request", kind=trace.SpanKind.CLIENT) as web_client_span:
                web_client_span.set_attribute("component", "web-ui")
                web_client_span.set_attribute("transaction.id", transaction_id)
                web_client_span.set_attribute("http.method", "POST")
                web_client_span.set_attribute("http.url", "/api/v1/login")

                # API Gateway receives the request
                with api_gw_tracer.start_as_current_span("api-gateway-login-handler", kind=trace.SpanKind.SERVER) as api_span:
                    api_span.set_attribute("component", "api-gateway")
                    api_span.set_attribute("transaction.id", transaction_id)
                    api_span.set_attribute("endpoint", "/api/v1/login")
                    api_span.set_attribute("http.method", "POST")
                    time.sleep(0.15)

                    # 3. API Gateway calls Authentication Service
                    with api_gw_tracer.start_as_current_span("auth-service-request", kind=trace.SpanKind.CLIENT) as api_client_span:
                        api_client_span.set_attribute("component", "api-gateway")
                        api_client_span.set_attribute("transaction.id", transaction_id)
                        api_client_span.set_attribute("http.method", "POST")
                        api_client_span.set_attribute("http.url", "/auth/authenticate")

                        # Auth service receives the request
                        with auth_tracer.start_as_current_span("authenticate-user", kind=trace.SpanKind.SERVER) as auth_span:
                            auth_span.set_attribute("component", "auth-service")
                            auth_span.set_attribute("transaction.id", transaction_id)
                            auth_span.set_attribute("auth.method", "password")
                            time.sleep(0.2)

                            # 4. Auth service calls User Service
                            with auth_tracer.start_as_current_span("user-service-request", kind=trace.SpanKind.CLIENT) as auth_client_span:
                                auth_client_span.set_attribute("component", "auth-service")
                                auth_client_span.set_attribute("transaction.id", transaction_id)
                                auth_client_span.set_attribute("http.method", "GET")
                                auth_client_span.set_attribute("http.url", "/user/details")

                                # User service receives the request
                                with user_tracer.start_as_current_span("get-user-details", kind=trace.SpanKind.SERVER) as user_span:
                                    user_span.set_attribute("component", "user-service")
                                    user_span.set_attribute("transaction.id", transaction_id)
                                    user_span.set_attribute("user.id", f"user_{random.randint(1000, 9999)}")

                                    # 5. User service calls DB Service
                                    with user_tracer.start_as_current_span("db-service-request", kind=trace.SpanKind.CLIENT) as user_client_span:
                                        user_client_span.set_attribute("component", "user-service")
                                        user_client_span.set_attribute("transaction.id", transaction_id)
                                        user_client_span.set_attribute("db.operation", "SELECT")
                                        user_client_span.set_attribute("db.table", "users")

                                        # DB service receives the request
                                        with db_tracer.start_as_current_span("db-query", kind=trace.SpanKind.SERVER) as db_span:
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
                    with api_gw_tracer.start_as_current_span("notification-service-request", kind=trace.SpanKind.CLIENT) as notif_client_span:
                        notif_client_span.set_attribute("component", "api-gateway")
                        notif_client_span.set_attribute("transaction.id", transaction_id)
                        notif_client_span.set_attribute("http.method", "POST")
                        notif_client_span.set_attribute("http.url", "/notifications/send")

                        # Notification service receives the request
                        with notif_tracer.start_as_current_span("send-login-notification", kind=trace.SpanKind.SERVER) as notif_span:
                            notif_span.set_attribute("component", "notification-service")
                            notif_span.set_attribute("transaction.id", transaction_id)
                            notif_span.set_attribute("notification.type", "login_alert")
                            notif_span.set_attribute("notification.channel", random.choice(["email", "sms", "push"]))
                            time.sleep(0.15)

        return transaction_id
    except Exception as e:
        print(f"Error generating multi-service trace: {e}")
        return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 