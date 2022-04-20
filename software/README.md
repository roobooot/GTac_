
## Minimum Requirement

### Environment Requirement
```
-Python3.6

-seaborn

-pandas

-tensorflow

-sklearn
```
### Hardware Requirement
```
-Serial Port
```
## Quick setup
Set  ```/software/``` as the root path of the project to run the code inside.
### Serial port in Ubuntu
```ruby
//check serial port ID
dmesg
```
or
```ruby
sudo chmod 666 /dev/ttys0 
```
serial port ID in Windows example
```ruby
sudo chmod 666 /dev/ttyACM0 
```
serial port ID in Ubuntu example
### GTac sensor ID for readout board
```
f: 0,1,2,3,4 (thumb, index, middle, ring, little)
s: 0,1,2 (proximal, middle, distal)
```
### Real-time GTac feedback display
For instance, if the serial port is ```/dev/ttyACM0```, the GTac signals can be visualized by the following command
```ruby
python draw_line3.py f 0 s 0 -sp /dev/ttyACM0
```
or
```ruby
python draw_lines3_tosave_local.py -f 2 -s 0 -fn data/case_study/test_sensor_300_GTAC_Gripper20220420_172845.csv -l 0 -r test -sp /dev/ttyACM0
```
```
-f: sensor ID f
-s: sensor ID s
-l: 1 = local display; 0 = live display
-r: remarks for fileanmes of video to be saved
-sp: serial port ID
-fn: filename of data to be displayed
```
### Save data
```ruby
python GTac_sensor.py -s 1 -d 300 -r test_sensor -sp /dev/ttyACM0
```
```
-s: 0 = not to save data; 1 = to save data
-d: number of datapoint (cycles) to save
-r: remarks of filename of data
-sp: serial port ID
```
```
default save path: data/
go to line-49 in GTac_sensor.py to change the save path.
```
