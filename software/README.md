
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
```ruby
//First check if you are a member of that group:
groups ${USER}
```
This will list all the groups you belong to. If you don't belong to the dialout grup then add yourself to it, for example:
```ruby
sudo gpasswd --add ${USER} dialout
```
or
```ruby
sudo chmod 666 /dev/ttys0 (serial port ID in Windows)
```
### Real-time GTac feedback display
```ruby
python draw_line3.py f 0 s 0
```
