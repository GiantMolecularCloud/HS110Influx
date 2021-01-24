![HS110Influx](https://github.com/GiantMolecularCloud/HS110Influx/blob/main/HS110Influx.png "HS110Influx")

# HS110Influx

A simple python app to poll a TP-Link HS110 and send the power related measurements (voltage, current, power, ...) to InfluxDB.


## Docker

The image is available on [Docker Hub](https://hub.docker.com/r/giantmolecularcloud/HS110Influx).
Note that it will likely get taken down in the future under Docker's policy to take down images that are not regularly accessed.

Build it yourself:
```
docker build --tag HS110Influx:latest .
docker run --init --env-file env-sample HS110Influx
```


### Environment variables

The HS110 and InfluxDB instance can be selected through the following environment variables.
If not given, defaults are assumed.

The easiest way to specify all env vars is using an environment file (e.g. [env-sample](https://github.com/GiantMolecularCloud/HS110Influx/blob/main/env-sample)) as in the example above.

`HS110_IP`
IP address of the HS110 to poll. No Default, must be given.

`HS110_PORT`
Port used to poll the HS110. Default if not specified: 9999

`INFLUX_DB`='power monitoring'
Name given to the InfluxDB database. Default if not specified: HS110
If no such database is present, it will be created.

`INFLUX_IP`
IP address of the InfluxDB instance to connect to. Default if not specified: 127.0.0.1
Must be set since InfluxDB is not running in this container.

`INFLUX_PORT`
Port on which InfluxDB is running. Default if not specified: 8086

`INFLUX_USER` and `INFLUX_PASSWD`
Credentials for the InfluxDB database. Default if not specified: root:root

`SAMPLE_TIME`
Wait time in between queries in seconds. Default if not specified: 60


## Example dashboard

An example for a Grafana dasboard to show the most relevant FritzBox metrics could look like this.
The code for this dashboard is in ![https://github.com/GiantMolecularCloud/HS110Influx/blob/main/dashboard.json](dashboard.json)

![Grafana dashboard](https://github.com/GiantMolecularCloud/HS110Influx/blob/main/dashboard.png "Grafana dashboard")


## Logo

The logo was created in a very simple way in Pixelmator ([HS110Influx.pxd](https://github.com/GiantMolecularCloud/HS110Influx/tree/main/HS110Influx.pxd)). Feel free to make something nicer (without violating potentially protected shapes and color combinations).
