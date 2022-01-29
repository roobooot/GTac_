# GTac
The code for collecting data from GTac, controlling robotics with integrated GTac and learning-based algorithms.

## GTac: A Biomimetic Tactile Sensor Design
This section is to introduce GTac and its integration with robotics.
For more information, please check out our paper. 

Z. Lu et al. "GTac: A Biomimetic Tactile Sensor with Skin-like Heterogeneous Force Feedback for Robots" In Review, Jan. 2022, Available: (update later)
<!---[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/Pmd8PvLpeUA/0.jpg)](https://youtu.be/Pmd8PvLpeUA)--->
<p align="center">
<a href="https://youtu.be/Pmd8PvLpeUA">
  <img  align="center"  src="http://img.youtube.com/vi/Pmd8PvLpeUA/0.jpg" alt="video">
</a>
</p>

## Quick setup

### Requirement
-Python3

-Serial port
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
