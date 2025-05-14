# Alloy Service Graphs with OpenTelemetry

This example demonstrates how to use Grafana Alloy to generate service graphs from OpenTelemetry traces and send them to Prometheus via OTLP HTTP, instead of relying on Tempo's built-in metrics generator.

## Overview

The example includes:

- A sample Python Flask application that generates various types of traces
- Grafana Alloy as the telemetry pipeline with service graph generation
- Tempo for trace storage and querying (without metrics generation)
- Prometheus with OTLP receiver enabled for metrics collection
- Memcached for Tempo caching
- Grafana for visualization

## Running the Demo

1. Clone the repository:
   ```
   git clone https://github.com/grafana/alloy-scenarios.git
   cd alloy-scenarios
   ```

2. Navigate to this example directory:
   ```
   cd alloy-service-graphs
   ```

3. Run using Docker Compose:
   ```
   docker compose up -d
   ```
   
   Or use the centralized image management:
   ```
   cd ..
   ./run-example.sh alloy-service-graphs
   ```

4. Access the demo application at http://localhost:8080
5. Access Grafana at http://localhost:3000
6. Access Prometheus at http://localhost:9090

## What to Expect

The demo application provides several endpoints that generate different types of traces:

- **/simple**: Generates a simple trace with a single span
- **/nested**: Generates a trace with nested spans (parent-child relationships)
- **/error**: Generates a trace that includes an error
- **/chain**: Simulates a chain of service calls to demonstrate distributed tracing

After accessing these endpoints, you can view the traces and service graphs in Grafana.

## Alloy Service Graph Generation

This example demonstrates using Alloy's `otelcol.connector.servicegraph` component to generate service graphs from traces, which offers several advantages over using Tempo's built-in metrics generator:

1. **More Flexibility**: Alloy's service graph connector allows for customization of dimensions and collection intervals
2. **Pipeline Integration**: The service graph metrics can be part of a larger telemetry pipeline with additional processing
3. **Reduced Load on Tempo**: By offloading the service graph generation to Alloy, Tempo can focus on trace storage and querying

The key component in the Alloy configuration is:

```
otelcol.connector.servicegraph "default" {
  metrics_flush_interval = "10s"
  dimensions = ["http.method"]
  
  output {
    metrics = [otelcol.exporter.otlphttp.prometheus.input]
  }
}
```

## Prometheus OTLP Integration

This example uses Prometheus's OTLP HTTP receiver endpoint. This approach has several benefits:

1. **Native OTLP Integration**: Uses the OpenTelemetry Protocol directly between Alloy and Prometheus
2. **Simplified Configuration**: Uses Prometheus's built-in OTLP receiver without needing special ports
3. **Better Metadata Handling**: Resource attributes from OTLP are properly promoted to Prometheus labels

The OTLP HTTP exporter configuration in Alloy is:

```
otelcol.exporter.otlphttp "prometheus" {
  client {
    endpoint = "http://prometheus:9090/api/v1/otlp"
    tls {
      insecure = true
    }
  }
}
```

And in Prometheus, we've enabled the OTLP receiver and configured resource attributes to be promoted to labels:

```
otlp:
  promote_resource_attributes:
    - service.instance.id
    - service.name
    - service.namespace
    - service.version
    - deployment.environment
    # ...and more relevant attributes
```

## Viewing Service Graphs

To view the service graph:

1. Open Grafana (http://localhost:3000)
2. Navigate to Explore
3. Select the Tempo data source
4. Click on the "Service Graph" tab
5. You should see a visual representation of the relationships between services

The service graph metrics are stored in Prometheus with the following metrics:
- `calls_total`: Total number of calls between services
- `calls_failed_total`: Total number of failed calls between services
- `latency`: Histogram of latencies between services

The metrics are segmented by HTTP method, allowing you to see which endpoints are being called.

## Architecture

```
┌────────────┐     ┌──────────────────────┐      ┌───────┐      ┌─────────┐
│ Demo App   │────▶│ Alloy                │─────▶│ Tempo │─────▶│ Grafana │
│ (OTel SDK) │     │ ┌──────────────────┐ │      │       │      │         │
└────────────┘     │ │Service Graph Gen.│ │      └───────┘      └─────────┘
                   │ └────────┬─────────┘ │                          ▲
                   └──────────┼───────────┘                          │
                              │                                      │
                              ▼                                      │
                        ┌─────────┐                                  │
                        │Prometheus│──────────────────────────────────┘
                        │  (OTLP)  │
                        └─────────┘
```

In this architecture:
1. The Demo App generates traces using the OpenTelemetry SDK and sends them to Alloy
2. Alloy processes the traces and:
   - Generates service graph metrics using the servicegraph connector
   - Forwards the raw traces to Tempo
3. Service graph metrics are sent to Prometheus via OTLP HTTP
4. Grafana queries both Tempo for traces and Prometheus for service graph metrics

## Customizing

The Alloy configuration can be further customized to add:
- Additional processors for trace data
- Filtering based on service names or other attributes
- Custom dimensions for the service graph metrics (currently using HTTP method)
- Additional metrics exporters for different backend systems 