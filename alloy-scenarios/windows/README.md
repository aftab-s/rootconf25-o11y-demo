# Monitoring Windows with Alloy

Grafana Alloy can be used to monitor Windows servers and desktops. In this guide we will show you how to install Grafana Alloy on a Windows machine and how to configure it to monitor the following system attributes:
* Windows Performance Metrics
* Windows Event Logs

## Prerequisites

* Git - You will need Git to clone the repository.
* Docker - In this tutorial we assume you are using Docker desktop for Windows. This is where we host Grafana, Loki and Prometheus. Note that you can also install native Windows versions of Grafana, Loki and Prometheus if you prefer or host them on a Linux server.
* Windows Server or Desktop - We will be monitoring a Windows machine, so you will need a Windows server or desktop to monitor.
* Admin access to the Windows machine - You will need admin access to the Windows machine to install the Grafana Alloy and configure it to collect metrics and logs.

## Step 1: Clone the Repository

Clone the repository to your Windows machine.

```bash
git clone https://github.com/grafana/alloy-scenarios.git
```

## Step 2: Deploy Grafana, Loki and Prometheus

First, you need to deploy Grafana, Loki and Prometheus on your Windows machine. Within this tutorial, we have included a docker-compose file that will deploy Grafana, Loki and Prometheus on your Windows machine.

```bash
cd alloy-scenarios/windows
docker-compose up -d
```

You can check the status of the containers by running the following command:

```bash
docker ps
```
Grafana should be running on [http://localhost:3000](http://localhost:3000).

## Step 3: Install Grafana Alloy

Follow the instructions in the [Grafana Alloy documentation](https://grafana.com/docs/alloy/latest/set-up/install/windows/) to install Grafana Alloy on your Windows machine.

Recommended steps:
* Install Grafana Alloy as a Windows service.
* Use Windows Installer to install Grafana Alloy.

Make sure to also checkout the [Grafana Alloy configuration](https://grafana.com/docs/alloy/latest/set-up/configuration/) documentation.

Personal recommendation: If you would like to see the Alloy UI from a remote machine you need to change the run arguments of the Grafana Alloy service. To do this:

1. Open Registery Editor.
2. Navigate to `HKEY_LOCAL_MACHINE\SOFTWARE\GrafanaLabs\Alloy`.
3. Double click on `Arguments`
4. Change the contents to the following:
```
run
C:\Program Files\GrafanaLabs\Alloy\config.alloy
--storage.path=C:\ProgramData\GrafanaLabs\Alloy\data
--server.http.listen-addr=0.0.0.0:12345
```
5. Restart the Grafana Alloy service. (Search for `Services` in the start menu, find `Grafana Alloy`, right click and restart)

You should now be able to access the Alloy UI from a remote machine by going to `http://<windows-machine-ip>:12345`.

## Step 4: Configure Grafana Alloy to Monitor Windows

Now that you have Grafana Alloy installed, you need to configure it to monitor your Windows machine. Grafana Alloy will currently be running a default configuration file. This needs to be replaced with the `config.alloy` file that is included in the `alloy-scenarios/windows` directory. To do this: 
1. Stop the Grafana Alloy service.
2. Replace the `config.alloy` file in `C:\Program Files\GrafanaLabs\Alloy` with the `config.alloy` file from the `alloy-scenarios/windows` directory.
3. Start the Grafana Alloy service.
4. Open your browser and go to `http://localhost:12345` to access the Alloy UI.

## Step 5: Viewing the Windows Performance Metrics and Event Logs

You will now be able to view the Windows Performance Metrics and Event Logs in Grafana:

* Open your browser and go to [http://localhost:3000/explore/metrics](http://localhost:3000/explore/metrics). This will take you to the metrics explorer in Grafana.

* Open your browser and go to [http://localhost:3000/a/grafana-lokiexplore-app](http://localhost:3000/a/grafana-lokiexplore-app). This will take you to the Loki explorer in Grafana.


