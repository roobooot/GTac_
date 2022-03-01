# A Biomimetic Design of HeteroGeneous Tactile Sensor (GTac) Providing Normal and Shear Force Feedback

## General Introduction

This repo includes:

<ul>
  <li>the <a href="https://github.com/roobooot/GTac_/tree/main/software">code</a> 
    <ul>
      <li><a href="https://github.com/roobooot/GTac_/tree/main/software/arduino_lib">low-level controller</a> of GTac-Hand and GTac-Gripper</li>
      <li><a href="https://github.com/roobooot/GTac_/tree/main/software/GTac_Sensor">collecting data from GTac</a></li>
      <li>algorithms used for case study in papers, for instance, learning-based ECS recognition, handover controller, force-closed grasping, etc.</li>
    </ul>
</li>
  <li>the <a href="https://github.com/roobooot/GTac_/tree/main/hardware">hardware design</a>.
    <ul>
      <li><a href="https://github.com/roobooot/GTac_/tree/main/hardware/PCB%20design">PCB design</a> of GTac, reading-out boards, and the motors driving boards.</li>
      <li><a href="https://github.com/roobooot/GTac_/tree/main/hardware/Mechanical%20design">mechenical design</a> (CAD models)</li>
    </ul>
    </li>
</ul>

## Papers in Submission

### GTac: A Biomimetic Tactile Sensor with Skin-like Heterogeneous Force Feedback for Robots

This paper is to introduce the design, fabrication methods, and force sensing principles of GTac.
For more information, please check out our paper below.

<p align="center">
  <img width="400" src="https://drive.google.com/uc?export=view&id=18ZXgVP_oYma_QvhO2UcUdRpGpyQ5F1Ca">
</p>

Z. Lu, X. Gao, and H. Yu, “**GTac: A Biomimetic Tactile Sensor with Skin-like Heterogeneous Force Feedback for Robots**,” arXiv:2201.12005 [cs], Jan. 2022. [Online]. Available: http://arxiv.org/abs/2201.12005

<!---[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/Pmd8PvLpeUA/0.jpg)](https://youtu.be/Pmd8PvLpeUA)--->
<p align="center">
<a href="https://youtu.be/Pmd8PvLpeUA">
  <img  align="center" src="http://img.youtube.com/vi/Pmd8PvLpeUA/0.jpg" alt="GTac">
</a>
</p>

### GTac-Hand: A Robotic Hand with Integrated Biomimetic Tactile Sensing and ECS Recognition Capabilities
Authors: Zeyu Lu, Haotian Guo, David Carmona, Shounak Bhattacharya, and Haoyong Yu

<img src="https://drive.google.com/uc?export=view&id=1BELUppySDUipSWb91n5G-HhWKfFflT3P">


Abstract—Human hands can effectively perform daily activities,
such as grasping and handovers of fragile objects,
utilizing the tactile sensing capabilities which simultaneously
perceive normal and shear forces via the mechanoreceptors
highly integrated into the fingers and palm; here, human
somatosensory systems leverage complex tactile feedback into
patterns and identify the extrinsic contact states (ECSs) of
objects in contact-rich tasks. Similarly, these features are still
open issues and critical for robots in acquiring such human
skills. In this letter, we integrate GTac sensors into a robotic
hand, GTac-Hand, to obtain tactile feedback from its fingers
and palm, resulting in 285 tactile measurements. Our results
show that GTac-Hand can grasp delicate objects and precisely
identify their ECSs via human-like patterning and learning
models, which can be used for robots to perform challenging
tasks, such as delicate object grasping, object handovers, and
ball-hit recognition.

### GTac-Gripper: A Four-fingered Robotic Gripper with Reconfigurable Mechanism and Biomimetic Tactile Sensing Capabilities

We present a robotic
gripper with a reconfigurable mechanism and biomimetic tactile
sensors integrated into the fingers and palm. Our gripper with
four adaptive fingers can perform 5 grasping gestures and
obtain 228 tactile feedback signals (normal and shear forces) in
150 Hz. We show that the gripper can grasp various everyday
objects and achieve in-hand manipulation including translation
and rotation with closed-loop control. This research provides a
new hardware design and could be beneficial to various

## Contact Information
If you have any queries, do not hesitate to contact <a href="https://roobooot.github.io/">Zeyu Lu</a> (email: zeyu.lu@u.nus.edu).

## Acknowledge
This project is supervised by <a href="https://www.eng.nus.edu.sg/bme/staff/dr-yuhy/">Prof. Haoyong Yu</a> in <a href="https://wiki.nus.edu.sg/display/biorobotics/Biorobotics+Lab">Biorobotics Lab</a> @NUS.
