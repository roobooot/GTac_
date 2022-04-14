
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
### Real-time GTac feedback display
For instance, if the serial port is ```/dev/ttyACM0```, the GTac signals can be visualized by the following command
```ruby
python draw_line3.py f 0 s 0 -sp /dev/ttyACM0
```
