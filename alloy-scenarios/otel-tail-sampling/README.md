# OpenTelemetry Tail Sampling with Grafana Alloy

This example demonstrates how to implement tail sampling for OpenTelemetry traces using Grafana Alloy, allowing you to intelligently filter and sample traces based on various criteria.

## Overview

The example includes:

- A Python Flask application that automatically generates different types of traces in the background
- Grafana Alloy configured with tail sampling policies and transform processor
- Tempo for trace storage and querying
- Prometheus for metrics collection
- Grafana for visualization
- Live debugging for monitoring the sampling process

## Running the Demo

1. Clone the repository:
   ```
   git clone https://github.com/grafana/alloy-scenarios.git
   cd alloy-scenarios
   ```

2. Navigate to this example directory:
   ```
   cd otel-tail-sampling
   ```

3. Run using Docker Compose:
   ```
   docker compose up -d
   ```
   
   Or use the centralized image management:
   ```
   cd ..
   ./run-example.sh otel-tail-sampling
   ```

4. Access the demo application at http://localhost:8080
5. Access Grafana at http://localhost:3000
6. Access Prometheus at http://localhost:9090
7. Access Alloy's live debugging endpoint at http://localhost:12345/debug/livedebugging

## What to Expect

The demo application automatically generates various types of traces in the background:

- **Simple Traces**: Basic single-span traces
- **Nested Traces**: Traces with parent-child relationships
- **Error Traces**: Traces containing errors
- **High Latency Traces**: Traces with execution times over 5 seconds
- **Delayed Chain Traces**: Service chains with Service D consistently having high latency (3-4 seconds)

You can also manually trigger trace generation using the web UI. The application will continuously generate a mix of these trace types in the background at random intervals.

## Processing Pipeline

This example demonstrates a more complex trace processing pipeline with the following components:

> Note: In the case of tail sampling, this ensures that trace spans are presented to the tail sampler as early as possible, to ensure that a decision period includes all relevant spans for a trace. Batch processing potentially prevents spans from arriving at the sampler before a sampling decision is made once the first span for a trace has been seen. This can lead to incorrect decisions being made, and starts to rely on a cache being enabled for future sampling decisions.

1. **OTLP Receiver**: Receives traces from the application via gRPC or HTTP
2. **Tail Sampling Processor**: Applies sampling policies based on trace properties
3. **Batch Processor**: Groups spans for efficient processing
4. **OTLP Exporter**: Sends sampled traces to Tempo

## Tail Sampling Configuration

This example uses Alloy's `otelcol.processor.tail_sampling` processor, which makes sampling decisions based on the entire trace, not just individual spans. This allows for more intelligent sampling based on trace-wide properties.

> Note: Tempo indexes upon TraceID's and SpanID's not resource attributes.  Make sure you only send When requesting trace IDs or carrying out TraceQL queries, this will mean that returned traces will in fact consist of whichever duplicate span is encountered first. This will mean that subsequent queries will potentially not yield the same result, and that the service names for spans in the same trace could be comprised of both raw-traces and trace-demo-tail-sampled in the same trace, or appear to be from a sampled trace when it was in fact unsampled, or vice versa. To ensure consistency, only one set of spans with a unique ID and traceID should be emitted to Tempo. 

The tail sampling configuration includes the following policies:

1. **Attribute-Based Sampling**: Samples traces with a specific attribute value
   ```
   policy {
     name = "test-attribute-policy"
     type = "string_attribute"
     
     string_attribute {
       key    = "test_attr_key_1"
       values = ["test_attr_val_1"]
     }
   }
   ```

2. **Error Sampling**: Always samples traces with ERROR status
   ```
   policy {
     name = "error-policy"
     type = "status_code"
     
     status_code {
       status_codes = ["ERROR"]
     }
   }
   ```

3. **Latency-Based Sampling**: Samples traces that exceed a latency threshold
   ```
   policy {
     name = "latency-policy"
     type = "latency"
     
     latency {
       threshold_ms = 5000  // 5 seconds
     }
   }
   ```

4. **Numerical Range Sampling**: Samples traces with a numeric attribute in a specific range
   ```
   policy {
     name = "numeric-policy"
     type = "numeric_attribute"
     
     numeric_attribute {
       key       = "key1"
       min_value = 70
       max_value = 100
     }
   }
   ```

5. **URL-Based Filtering**: Excludes health check and metrics endpoints
   ```
   policy {
     name = "url-filter-policy"
     type = "string_attribute"
     
     string_attribute {
       key             = "http.url"
       values          = ["/health", "/metrics"]
       invert_match    = true
     }
   }
   ```

6. **Probabilistic Sampling**: Samples a percentage of remaining traces
   ```
   policy {
     name = "probabilistic-policy"
     type = "probabilistic"
     
     probabilistic {
       sampling_percentage = 10
     }
   }
   ```

## Live Debugging

This example enables Alloy's live debugging feature, which provides real-time insights into the sampling process:

```
livedebugging {
  enabled = true
}
```

Access the live debugging interface at http://localhost:12345 to see:

- Current processing pipeline state
- Trace sampling decisions in real-time
- Policy hit counts and performance metrics
- Throughput statistics

## Sampling Implications

With tail sampling enabled in this example:

- All error traces are preserved for troubleshooting
- High latency traces (>5s) are kept for performance analysis
- Traces with specific attribute values used for monitoring are retained
- Health check and metrics endpoints are filtered out to reduce noise
- A small percentage of other traces are kept for baseline monitoring
- Traces not matching any criteria are dropped, reducing storage needs
- Raw traces are stored with a different service name for comparison

## Viewing Traces in Grafana

To view the sampled traces:

1. Open Grafana (http://localhost:3000)
2. Navigate to Explore
3. Select the Tempo data source
4. Use the Search tab to find traces based on various criteria

## Sample Queries

Try these queries in Grafana's Tempo Explorer:

- Find all traces for the sampled service:
  ```
  {resource.service.name="trace-demo-tail-sampled"}
  ```

- Find error traces:
  ```
  {status=error}
  ```

- Find high latency traces:
  ```
  {duration>5s}
  ```

- Find traces with a specific attribute:
  ```
  {span.test_attr_key_1="test_attr_val_1"}
  ```
  
- Find traces with Service D bottleneck:
  ```
  {span.service.latency="high" && span.latency.category="bottleneck"}
  ```

## Customizing

You can modify the `config.alloy` file to adjust the sampling policies:

- Change the decision wait time to balance memory usage vs. complete trace visibility
- Adjust the sampling thresholds to capture more or fewer traces
- Add additional sampling policies based on your specific needs
- Modify the existing policies to match your application's attributes
- Update the transform processor to add or modify different attributes

## Further Resources

- [Grafana Alloy Tail Sampling Documentation](https://grafana.com/docs/alloy/latest/reference/components/otelcol.processor.tail_sampling/)
- [Grafana Alloy Transform Processor Documentation](https://grafana.com/docs/alloy/latest/reference/components/otelcol.processor.transform/)
- [OpenTelemetry Tail Sampling Processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/tailsamplingprocessor)
- [Live Debugging in Grafana Alloy](https://grafana.com/docs/alloy/latest/debug-alloy-flow/) 