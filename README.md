# GTac
The code for collecting data from GTac, controlling robotics with integrated GTac and learning-based algorithms.

## GTac: A Biomimetic Tactile Sensor Design
This section is to introduce GTac and its integration with robotics.
For more information, please check out our paper.


Z. Lu, X. Gao, and H. Yu, “GTac: A Biomimetic Tactile Sensor with Skin-like Heterogeneous Force Feedback for Robots,” arXiv:2201.12005 [cs], Jan. 2022. [Online]. Available: http://arxiv.org/abs/2201.12005

<!---[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/Pmd8PvLpeUA/0.jpg)](https://youtu.be/Pmd8PvLpeUA)--->
<p align="center">
<a href="https://youtu.be/Pmd8PvLpeUA">
  <img  align="center"  src="http://img.youtube.com/vi/Pmd8PvLpeUA/0.jpg" alt="video">
</a>
</p>

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
## Contact Information
If you have any queries, do not hesitate to contact <a href="https://roobooot.github.io/">Zeyu Lu</a> (email: zeyu.lu@u.nus.edu).

## Acknowledge
This project is supervised by <a href="https://www.eng.nus.edu.sg/bme/staff/dr-yuhy/">Prof. Haoyong Yu</a> in <a href="https://wiki.nus.edu.sg/display/biorobotics/Biorobotics+Lab">Biorobotics Lab</a> @NUS.
