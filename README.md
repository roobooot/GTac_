# GTac
The code for collecting data from GTac, controlling GTac-Hand and learning-based algorithms.

## GTac: A Biomimetic Tactile Sensor Design
This section is to introduce GTac and its integration with robotics.
### Z. Lu et al. "GTac: A Biomimetic Tactile Sensor with Skin-like Heterogeneous Force Feedback for Robots" In Review, Jan. 2022, Available: https://arxiv.org/submit/4129297
<!---[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/Pmd8PvLpeUA/0.jpg)](https://youtu.be/Pmd8PvLpeUA)--->
<p align="center">
<a href="https://youtu.be/Pmd8PvLpeUA">
  <img  align="center"  src="http://img.youtube.com/vi/Pmd8PvLpeUA/0.jpg" alt="video">
</a>
</p>

## Setup
serial port in Ubuntu
```ruby
//check serial port ID
dmesg
```
```ruby
//First check if you are a member of that group:
groups ${USER}
```
..this will list all the groups you belong to. If you don't belong to the dialout grup then add yourself to it, for example:
```ruby
sudo gpasswd --add ${USER} dialout
```
or
```ruby
sudo chmod 666 /dev/ttys0 (serial port ID)
```
