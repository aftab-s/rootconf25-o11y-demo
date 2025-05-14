# Logs Over TCP Scenario

This scenario demonstrates how to send TCP logs to Alloy within a JSON format. We then use `log.process` to parse the logs and extract the fields from the JSON logs. These fields are used to generate labels and structured metadata for the logs.

## Running the Demo

### Step 1: Clone the repository
```bash
git clone https://github.com/grafana/alloy-scenarios.git
```

### Step 2: Deploy the monitoring stack
```bash
cd alloy-scenarios/logs-tcp
docker-compose up -d
```

### Step 3: Access Grafana Alloy UI
Open your browser and go to `http://localhost:12345`. 

### Step 4: Access Grafana UI
Open your browser and go to `http://localhost:3000`.


