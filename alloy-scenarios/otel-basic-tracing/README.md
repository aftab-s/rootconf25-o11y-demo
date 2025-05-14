# OpenTelemetry Basic Tracing with Grafana Alloy

This example demonstrates how to collect and visualize OpenTelemetry traces using Grafana Alloy and Tempo.

## Overview

The example includes:

- A sample Python Flask application that generates various types of traces
- Grafana Alloy as the telemetry pipeline
- Tempo for trace storage and querying
- Prometheus for metrics collection (service graphs)
- Grafana for visualization

## Running the Demo

1. Clone the repository:
   ```
   git clone https://github.com/grafana/alloy-scenarios.git
   cd alloy-scenarios
   ```

2. Navigate to this example directory:
   ```
   cd otel-basic-tracing
   ```

3. Run using Docker Compose:
   ```
   docker compose up -d
   ```
   
   Or use the centralized image management:
   ```
   cd ..
   ./run-example.sh otel-basic-tracing
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

After accessing these endpoints, you can view the traces in Grafana by:

1. Opening http://localhost:3000
2. Navigating to Explore
3. Selecting the Tempo data source
4. Using the Search tab to find and visualize traces

## Service Graphs

This example includes service graph visualization capabilities. As you generate traces with the demo app (especially with the `/chain` endpoint), Tempo will generate service graph metrics that are sent to Prometheus.

To view the service graph:

1. Open Grafana (http://localhost:3000)
2. Navigate to Explore
3. Select the Tempo data source
4. Click on the "Service Graph" tab
5. You should see a visual representation of the relationships between services

## Architecture

```
┌────────────┐     ┌──────────┐      ┌───────┐      ┌─────────┐
│ Demo App   │────▶│ Alloy    │─────▶│ Tempo │─────▶│ Grafana │
│ (OTel SDK) │     │          │      │       │      │         │
└────────────┘     └──────────┘      └───┬───┘      └─────────┘
                                         │                ▲
                                         ▼                │
                                    ┌─────────┐           │
                                    │Prometheus│───────────┘
                                    └─────────┘
```

The Demo App generates traces using the OpenTelemetry SDK and sends them to Alloy, which processes and forwards them to Tempo. Tempo generates service graph metrics and sends them to Prometheus. Grafana queries both Tempo and Prometheus to visualize traces and service graphs.

## Customizing

The Alloy configuration is a simple placeholder. You can modify `config.alloy` to add processors, filters, or additional exporters to demonstrate more complex telemetry pipelines. 