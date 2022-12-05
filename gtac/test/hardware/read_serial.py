import time
from gtac.serial_reader import GtacSerialReader
import logging
import sys

logging.basicConfig(
    format="%(asctime)s | %(levelname)s : %(message)s",
    level=logging.DEBUG,
    stream=sys.stdout,
)

reader = GtacSerialReader("/dev/ttyACM0", 115200, 200)
reader.start()
time.sleep(1)
print(reader.reading)
reader.stop()
