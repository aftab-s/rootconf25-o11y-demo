# Monitoring Linux with Alloy

Grafana Alloy can be used to monitor Linux servers and containers. In this guide, we will show you how to deploy Grafana Alloy in a Docker environment to monitor Linux system metrics and logs. The setup consists of:
* Node Exporter metrics for system performance monitoring
* System logs collection with Loki

## Prerequisites

* Git - You will need Git to clone the repository.
* Docker and Docker Compose - This tutorial uses Docker to host Grafana, Loki, Prometheus, and Alloy.
* Linux environment - Either a Linux host running Docker or a Linux VM.

## About this Demo

This demo runs Alloy in a container alongside Grafana, Prometheus, and Loki, creating a self-contained monitoring stack. The Alloy container acts as a "fake Linux server" to demonstrate monitoring capabilities out of the box.

In a production environment, you would typically install Alloy directly on each Linux server you want to monitor.

## Step 1: Clone the Repository

Clone the repository to your machine:

```bash
git clone https://github.com/grafana/alloy-scenarios.git
cd alloy-scenarios/linux
```

## Step 2: Deploy the Monitoring Stack

Use Docker Compose to deploy Grafana, Loki, Prometheus, and Alloy:

```bash
docker-compose up -d
```

You can check the status of the containers:

```bash
docker ps
```

Grafana should be running on [http://localhost:3000](http://localhost:3000).

## Step 3: Explore the Monitoring Data

Once the stack is running, you can explore the collected metrics and logs:

1. Access Grafana at [http://localhost:3000](http://localhost:3000) (default credentials are admin/admin)
2. Import the Node Exporter dashboard to visualize system metrics:
   - Go to Dashboards → Import
   - Upload the JSON file from [here](https://grafana.com/api/dashboards/1860/revisions/37/download)
   - Select the Prometheus data source and click Import

This community dashboard provides comprehensive system metrics including CPU, memory, disk, and network usage.

## Step 4: Viewing Logs

Open your browser and go to [http://localhost:3000/a/grafana-lokiexplore-app](http://localhost:3000/a/grafana-lokiexplore-app). This will take you to the Loki explorer in Grafana.

## Deploying on Bare Metal

To monitor actual Linux servers in production, you would:

1. Install Alloy directly on each Linux server

2. Modify the `config.alloy` file to point to your Prometheus and Loki instances:
   ```
   prometheus.remote_write "local" {
     endpoint {
       url = "http://localhost:9090/api/v1/write"
     }
   }
   
   loki.write "local" {
     endpoint {
       url = "http://localhost:3100/loki/api/v1/push"
     }
   }
   ```

3. Run Alloy as a service:
   ```bash
   sudo alloy run /path/to/config.alloy
   ```

## Configuration Customization

The included `config.alloy` file sets up:

1. Node Exporter integration to collect system metrics
2. Log collection from system logs and journal
3. Relabeling rules to organize metrics and logs
4. Remote write endpoints for Prometheus and Loki

You can customize which collectors are enabled/disabled and adjust scrape intervals in the configuration file.

## Troubleshooting

If you encounter issues:

* Check container logs: `docker-compose logs`
* Verify Alloy is running: `docker-compose ps`
* Ensure ports are not conflicting with existing services
* Review the Alloy configuration in `config.alloy`


