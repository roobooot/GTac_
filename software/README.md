
## Minimum Requirement

### Environment Requirement
```
-Python3.6

-seaborn

-pandas

-tensorflow

-sklearn
```
### System Requirement
```
-Linus (Ubuntu 18.04 tested)
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
go to
```
software/GTac_Hand/
```
For instance, if the serial port is ```/dev/ttyACM0```, the GTac signals can be visualized by the following command
```ruby
python draw_line3.py -f 0 -s 0 -sp /dev/ttyACM0
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
### Save GTac data
go to
```
software/GTac_Hand/
```
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
### Use the saved GTac data
The saved GTac data has 293 columns. 
```
[285 + 6 + 1 + 1]
[GTac data + Serve motor angles * 6 + readout frequency + timeframe (ms)]
```
From left to the right, there are 285 GTac data signals when using the readout board that can produce digital signals for up to 15 GTac sensors. If less than 15 GTac sensors are used, only the related columns are with effective signals. 
#### GTac ID
Each used GTac sensor has a ID which is related to the hardware connection, which are 'finger' and 'sec'. 'finger' is [0,1,2,3,4] corresponding to the ports (thumb, index, middle, ring, little) that the sensors are connected to on the readout borad. Up to three GTac sensors can be serially connected to the each port of the readout board. Therefore, 'sec' is [0,1,2] which depends on the GTac sensors connected serially in each port, e.g., 'sec' is 0 if only one GTac sensor is used. 
#### GTac API 
##### Finding the signals in the 285 columns of GTac data
There are 19 signals for each GTac sensor which consists of 16 FA-I signals (4x4 arrayed normal force sensing) and 3 SA-II signals (global 3D contact forces in x, y, and z axis). Use the following functions to find the signals in demand.

###### Find the GTac signals:
FA-I:
https://github.com/roobooot/GTac_/blob/88ff11a90103c957f8382d993401048128073cff/software/GTac_Hand/GTac_Data.py#L290
SA-II:
https://github.com/roobooot/GTac_/blob/88ff11a90103c957f8382d993401048128073cff/software/GTac_Hand/GTac_Data.py#L343

###### Find the index in 285 GTac data:
FA-I:
https://github.com/roobooot/GTac_/blob/88ff11a90103c957f8382d993401048128073cff/software/GTac_Hand/GTac_Data.py#L295
SA-II:
https://github.com/roobooot/GTac_/blob/88ff11a90103c957f8382d993401048128073cff/software/GTac_Hand/GTac_Data.py#L354
SA-II:
All the 19 index for each GTac:
https://github.com/roobooot/GTac_/blob/88ff11a90103c957f8382d993401048128073cff/software/GTac_Hand/GTac_Data.py#L275
