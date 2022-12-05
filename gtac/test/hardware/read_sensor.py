#!/usr/bin/env python
import time
import sys
from gtac import GtacInterface
import logging

logging.basicConfig(
    format="%(asctime)s | %(levelname)s : %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)

sensor = GtacInterface("/dev/ttyACM0", data_index=6)
sensor.start()

t0 = time.time()

while time.time() - t0 < 10:
    print(sensor.forces)
    print(sensor.pressures)
    time.sleep(0.1)

sensor.stop()
