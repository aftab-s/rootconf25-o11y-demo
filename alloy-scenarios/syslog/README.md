# Syslog Scenario

This scenario demonstrates how to use ryslog and Alloy to monitor non RFC5424 compliant syslog messages. Alloy by itself does not support non RFC5424 compliant syslog messages. However, we can use rsyslog to convert non RFC5424 compliant syslog messages to RFC5424 compliant syslog messages. 

## Running the Demo

### Step 1: Clone the repository
```bash
git clone https://github.com/grafana/alloy-scenarios.git
```

### Step 2: Deploy the monitoring stack
```bash
cd alloy-scenarios/syslog
docker-compose up -d
```

### Step 3: Access Grafana Alloy UI
Open your browser and go to `http://localhost:12345`. 

### Step 4: Access Grafana UI
Open your browser and go to `http://localhost:3000`.


