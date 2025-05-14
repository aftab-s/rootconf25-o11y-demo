# Trace Delivery Demo

This scenario demonstrates how distributed tracing works using a realistic sofa delivery workflow. It shows the journey of a sofa order from the shop to the customer's house, passing through multiple services.

## Overview

The demo includes five interconnected services simulating a sofa ordering and delivery process:

1. **Sofa Shop** - Where customers browse sofas and place orders
2. **Sofa Factory** - Manufactures the ordered sofas with detailed assembly steps
3. **Global Distribution Center** - Handles global logistics and shipping
4. **Local Distribution Center** - Manages local delivery logistics
5. **Customer House** - The final destination for delivery

Each service generates spans as part of a complete trace that follows the sofa from order to delivery. This demo includes three main scenarios:

1. **Successful Delivery** - A complete, happy-path delivery with no issues
2. **Failed Delivery** - Simulated failures at different points in the delivery process
3. **Latency Issues** - Abnormal delays in one service affecting the entire delivery process

## Architecture

```
┌────────────┐     ┌──────────────┐     ┌─────────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  Sofa Shop │────▶│ Sofa Factory │────▶│ Global Distribution │────▶│ Local Distribution│────▶│ Customer House │
└────────────┘     └──────────────┘     └─────────────────────┘     └──────────────────┘     └────────────────┘
                                                                            │
                                                                            │
                                                                            ▼
                                                                     ┌────────────┐
                                                                     │ Sofa Shop  │
                                                                     └────────────┘
                                                                     (notification)
```

All services are instrumented with OpenTelemetry to generate traces, which are collected by Grafana Alloy and visualized in Grafana via Tempo.

## Demo Features

- **Realistic Business Process**: Simulates a real-world business workflow with multiple services and dependencies
- **Trace Context Propagation**: Demonstrates how trace context is passed between services
- **Background Trace Generation**: Automatically generates traces for all scenarios periodically
- **Nested Spans**: Shows detailed manufacturing steps with nested spans and span events
- **Bidirectional Communication**: Local Distribution center notifies the Shop when delivery is dispatched
- **Error Cases**: Shows how errors are recorded and propagated in traces with exceptions
- **Latency Visualization**: Illustrates how performance bottlenecks appear in traces
- **Span Events**: Each service adds detailed span events to provide context for operations
- **Tail Sampling**: Demonstrates tail sampling policies that focus on errors, latency issues, and specific order attributes
- **Service Graph**: Visualizes the connections between services 

## Running the Demo

1. Clone the repository:
   ```
   git clone https://github.com/grafana/alloy-scenarios.git
   cd alloy-scenarios
   ```

2. Navigate to this example directory:
   ```
   cd trace-delivery
   ```

3. Run using Docker Compose:
   ```
   docker compose up -d
   ```
   
   Or use the centralized image management:
   ```
   cd ..
   ./run-example.sh trace-delivery
   ```

4. Access the Sofa Shop at http://localhost:8080

## Demo Scenarios

### 1. Successful Delivery

Navigate to http://localhost:8080/demo/success to trigger a successful delivery flow, which will:
- Create an order for a Classic Comfort sofa
- Process it through all stages of the delivery pipeline
- Show the detailed manufacturing steps with nested spans
- Have the Local Distribution center notify the Shop of the dispatch
- Complete delivery successfully
- Generate a full trace that can be examined in Grafana

### 2. Failed Delivery

Navigate to http://localhost:8080/demo/failure to simulate a failure scenario, which will:
- Create an order for a Luxury Lounge sofa
- Simulate a failure at one of the services (factory by default)
- Record an actual exception in the trace with detailed error information
- Generate an error trace that will be sampled by the error policy

You can change where the failure occurs by adding a query parameter:
- http://localhost:8080/demo/failure?service=sofa-factory
- http://localhost:8080/demo/failure?service=global-distribution
- http://localhost:8080/demo/failure?service=local-distribution

### 3. Latency Issues

Navigate to http://localhost:8080/demo/latency to simulate a latency scenario, which will:
- Create an order for a Limited Edition Designer sofa
- Introduce significant latency in one service (factory by default)
- Add span events explaining the cause of the latency
- Demonstrate how tail sampling captures high-latency traces

You can change where the latency occurs by adding a query parameter:
- http://localhost:8080/demo/latency?service=sofa-factory
- http://localhost:8080/demo/latency?service=global-distribution
- http://localhost:8080/demo/latency?service=local-distribution

## Background Trace Generation

The demo automatically generates traces in the background to populate your trace data:
- Successful delivery traces (70% of background traces)
- Failure scenarios (15% of background traces)
- Latency scenarios (15% of background traces)

This helps ensure you have data to analyze without having to manually trigger scenarios.

## Viewing Traces

1. Open Grafana at http://localhost:3000
2. Navigate to Explore
3. Select Tempo as the data source
4. Click on the "Search" tab and select filters like:
   - `delivery.status = "failed"` to see failed deliveries
   - `sofa.model = "limited-edition"` to see traces for limited edition sofas
   - `customer.type = "vip"` to see VIP customer orders
   - `background = true` to see background-generated traces
   - `scenario = "delivery-failure"` to see failure scenarios
5. Or explore the service graph by clicking the "Service Graph" tab

## Span Events

Each span in the trace contains detailed events providing context about what's happening:
- **Manufacturing**: Events for each assembly step like frame construction, spring installation, etc.
- **Distribution**: Events for package preparation, routing, loading, etc.
- **Delivery**: Events for delivery dispatched, delivered, etc.
- **Failure**: Detailed information about what went wrong and where
- **Latency**: Information about delays and their causes

## Tail Sampling Policies

This demo configures Grafana Alloy with six tail sampling policies:

1. **Failed Delivery Policy**: Captures all traces with `delivery.status = "failed"`
2. **Error Policy**: Samples traces with errors
3. **Latency Policy**: Samples traces exceeding 5 seconds in duration
4. **VIP Customer Policy**: Samples all orders from VIP customers
5. **Limited Edition Policy**: Samples all orders for limited edition sofas
6. **Probabilistic Policy**: Samples 20% of all remaining traces

These policies ensure important traces (errors, performance issues, VIP customers) are retained while still sampling a representative subset of normal traffic.

## Troubleshooting

If you encounter issues:

1. **Missing services**: Ensure all containers are running with `docker compose ps`
2. **Network issues**: Check if services can communicate with each other
3. **Trace data missing**: Verify Alloy and Tempo are configured properly
4. **Service failures**: Check logs with `docker compose logs <service-name>`

## Customizing the Demo

You can modify the demo in several ways:

- Edit `app.py` to change service behavior, add new features, or adjust timing
- Modify `config.alloy` to change sampling policies or add new connectors
- Edit failure and latency probabilities in the script to increase/decrease error rates
- Add new sofa models or customer types to expand the demo

## Learning from the Demo

This demo helps understand:

1. How distributed tracing works across multiple services
2. How trace context is propagated through HTTP requests
3. How nested spans create a hierarchical view of operations
4. How span events provide detailed context about operations
5. How to use tail sampling to focus on important traces
6. How to troubleshoot errors and performance issues using traces
7. How service graphs visualize the relationships between services 