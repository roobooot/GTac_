# Python Interface for GTac Sensor

## Installation

Assuming your current directory is `GTac_/gtac/`, simply run
``` python
pip install .
```

To install for development, using `-e` option: `pip install -e .[dev]`

## Getting started

The main interface is `GtacInterface`. 
``` python
import gtac 

gtac_sensor = gtac.GtacInterface(serial_port="/dev/ttyACM0", data_index=6)
gtac_sensor.start()  # start the sensor
print(gtac_sensor.force)  # return a 3-dimensional numpy array 
print(gtac_sensor.pressure)  # return a 4-by-4 numpy array 
gtac_sensor.stop()  # stop the sensor
```

