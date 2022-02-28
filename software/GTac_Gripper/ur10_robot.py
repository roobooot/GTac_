import copy
import time
from time import sleep
import math3d as m3d
import urx
from math import pi
import numpy as np
# from GTac_Data import gtac_data
import GTac_Data

def safty_check(robot, goal_tool, x_lim, y_lim, z_lim):
    # units: meter
    goal_tool_transform = m3d.Transform(goal_tool)
    # print('To execute goal_tool:{}'.format(goal_tool_transformed))
    estimeted_final_pose = robot.get_pose() * goal_tool_transform
    print('Safty check: Estimated final pose:{}'.format(estimeted_final_pose))
    goal_x_base = estimeted_final_pose.pos[0]
    goal_y_base = estimeted_final_pose.pos[1]
    goal_z_base = estimeted_final_pose.pos[2]
    x_result = goal_x_base > min(x_lim) and goal_x_base < max(x_lim)
    y_result = goal_y_base > min(y_lim) and goal_y_base < max(y_lim)
    z_result = goal_z_base > min(z_lim) and goal_z_base < max(z_lim)

    xyz_result = [x_result, y_result, z_result]
    final_result = x_result and y_result and z_result

    print('Safety check: {}, {}'.format(final_result, xyz_result))
    return final_result, xyz_result


def rob_movel_tool(robot, goal_tool, acc=0.02, vel=0.02, wait=True):
    if goal_tool != [0 for _ in goal_tool]:
        try:
            goal_tool_transformed = m3d.Transform(goal_tool)
            print('To execute goal_tool:{}'.format(goal_tool_transformed))
            estimeted_final_pose = robot.get_pose() * goal_tool_transformed
            print('Estimated final pose:{}'.format(estimeted_final_pose))
            # rob.movel((0, 0, 0, 0, 0 , 0), acc=0.01, vel=0.01, relative=True, wait=False)  # move relative to current pose
            robot.movel_tool(goal_tool_transformed, acc=acc, vel=vel,
                             wait=wait)  # move linear to given pose in tool coordinate
            # rob.set_pose(tool_orient_normal, acc=0.01, vel=0.01)
            # rob.translate_tool((0.02, 0, 0), wait=False)
        except:
            print("Robot could not execute move (emergency stop for example), do something")
        finally:
            print('UR 10 moved in tool base: {}'.format(goal_tool))
            trans = robot.get_pose()
            print('current pose::{}'.format(trans))
            if not wait:
                while True:
                    sleep(0.01)  #sleep first since the robot may not have processed the command yet
                    print(robot.is_program_running())
                    if robot.is_program_running():
                        break

def safe_movel_tool(robot, goal_tool, x_lim, y_lim, z_lim, acc=0.02, vel=0.02, wait=True):
    if goal_tool != [0 for _ in goal_tool]:
        safe_result, _ = safty_check(robot, goal_tool, x_lim, y_lim, z_lim)
        if safe_result:
            rob_movel_tool(robot, goal_tool, acc=acc, vel=vel, wait=wait)


def main_ur10_repeat(goal_tool=None, times=1, boundary=[[0, 0.15], [-1.08, -1.2], [-0.17, 0.1]], acc=0.02, vel=0.02, wait=True):
    print('try to connect ur10')
    rob = urx.Robot("192.168.2.100")
    rob.set_tcp((0, 0, 0.225, 0, 0, 0))
    rob.set_payload(0.5, (0, 0, 0.225))
    sleep(0.2)  # leave some time to robot to process the setup commands

    tool_orient_normal = m3d.Transform()
    print('ur10 connected')
    print(rob.is_program_running())
    i = 0
    while i < times:
        time.sleep(0.01)
        # i += 1
        ts = time.time()
        print('rob.is_program_running: {}'.format(rob.is_program_running()))
        if not rob.is_program_running():
            safe_movel_tool(robot=rob, goal_tool=goal_tool,
                            x_lim=boundary[0],
                            y_lim=boundary[1],
                            z_lim=boundary[2],
                            acc=acc,
                            vel=vel,
                            wait=wait)
            i += 1
            goal_tool = [-x for x in goal_tool]  # inverse the command to repeat
        # time.sleep(1)
        trans = rob.get_pose()
        print('{}-current pose::{}'.format(i, trans))

    rob.close()

def robot_stop(robot, stop_time=0.3):
    robot.stopl()
    print('Stopping the robot')
    time.sleep(stop_time)  # wait a while to start the next command to avoid shock.

def main_ur10_thread(q_ur=None, dq_ur10_cmd_exc=None, data_points=5000, boundary=[[0, 0.15], [-1.08, -1.2], [-0.17, 0.1]], acc=0.05, vel=0.05, wait=False, dq_stop_sign=None):
    print('try to connect ur10')
    rob = urx.Robot("192.168.1.100")
    rob.set_tcp((0, 0, 0.225, 0, 0, 0))
    rob.set_payload(0.5, (0, 0, 0.25))
    sleep(0.2)  # leave some time to robot to process the setup commands
    tool_orient_normal = m3d.Transform()
    print('ur10 connected')
    i = 0
    preivous_time = 0
    ts = time.time()
    goal_tool = [0, 0, 0, 0, 0, 0]
    while i < data_points:
        if dq_stop_sign is not None and len(dq_stop_sign) > 0 and dq_stop_sign[-1] == True:
            break
        i += 1
        time.sleep(0.01)
        preivous_time = time.time()
        try:
            # print('rob.is_program_running: {}'.format(rob.is_program_running()))
            if not q_ur.empty():
                goal_tool = q_ur.get(timeout=0.1)
                q_ur.task_done()
                # print('{} ms: UR10 got new goal tool:{} '.format(round(preivous_time-ts, 3)*1000, goal_tool))
            if goal_tool == 'stop':
                robot_stop(robot=rob, stop_time=0.3)
            else:
                if not rob.is_program_running():
                    if goal_tool != [0 for _ in goal_tool]:
                        safe_movel_tool(robot=rob, goal_tool=goal_tool,
                                        x_lim=boundary[0],
                                        y_lim=boundary[1],
                                        z_lim=boundary[2],
                                        acc=acc,
                                        vel=vel,
                                        wait=wait)
                        exc = dq_ur10_cmd_exc[-1]
                        dq_ur10_cmd_exc.append(copy.copy(exc)+1)  # marker one more execution
                        # print('dq_ur10_cmd_exc: {}, goal_tool: {}'.format(dq_ur10_cmd_exc, goal_tool))
                        goal_tool = [0, 0, 0, 0, 0, 0]  # init the command after being sent
                else:
                    print('The previous UR command has not been completed')
        except:
            continue
        # print('{}:{}'.format(i, rob.get_pose()))
        # while True:
        #     sleep(0.1)  #sleep first since the robot may not have processed the command yet
        #     if rob.is_program_running():
        #         break
    rob.close()

def UR10_leave_admittance_mode():
    return True



# enter adnittance mode
# input: m-- apperant mess of the robot
#        k-- stiffness of the robot
#        b-- damp coefficient of the robot
#        force_sensor-- sensor indicator
# output: null

def Read_force_sensor(q_gtac=None, amp=100):
    # read data from the sensor and formate into a vector
    # input: sensor indicator
    # output: force_arr[Fx, Fy, Fz, Tx, Ty, Tz]
    data_gtac = q_gtac.get(timeout=1)
    q_gtac.task_done()
    sec_data, _ = GTac_Data.gtac_data.find_sec_data(data_frame_array=data_gtac, finger=4, sec=0)
    f_x = sec_data[-3]/amp
    f_y = sec_data[-2]/amp
    f_z = sec_data[-1]/amp
    arr = np.zeros([6, 1])
    arr[0] = f_x
    arr[1] = f_y
    arr[2] = f_z
    print('UR10 admittance got: {}'.format(arr))
    return arr

def UR10_enter_admittance_thread(q_gtac=None, m = 20, k = 0, b = 50):
    # set a flag for leave the admittance thread
    # input: null
    # output: force_arr[Fx, Fy, Fz, Tx, Ty, Tz]
    print('try to connect ur10')
    rob = urx.Robot("192.168.1.100")
    rob.set_tcp((0, 0, 0.225, 0, 0, 0))
    rob.set_payload(0.5, (0, 0, 0.25))
    sleep(0.2)  # leave some time to robot to process the setup commands

    tool_orient_normal = m3d.Transform()
    print('ur10 connected')
    array_size = 5
    acc = np.zeros([array_size, 6, 1])
    vel = np.zeros([array_size, 6, 1])
    pos = np.zeros([array_size, 6, 1])
    front = 0
    rear = 0
    while True:
        begin = time.time()
        period = 0.01
        force_formated = Read_force_sensor(q_gtac=q_gtac, amp=100)
        acc[front] = (force_formated - b*vel[rear] - k*pos[rear])/m
        vel[front] = period*(acc[front] + acc[rear])/2 + vel[rear]
        pos[front] = period*(vel[front] + vel[rear])/2 + pos[rear]
        rob.speedx("speedl",vel(front),acc(front))
        rear = front
        front = front + 1
        if front > array_size:
            front = 0
        time.sleep((begin + period - time.time()) if time.time() - begin < period else 0)
        if UR10_leave_admittance_mode():
            break
    print("have leave the admittance mode")
    rob.close()

def init_ur_handover(pos, acc=0.02, vel=0.01,):
    print('try to connect ur10')
    rob = urx.Robot("192.168.1.100")
    rob.set_tcp((0, 0, 0.225, 0, 0, 0))
    rob.set_payload(0.5, (0, 0, 0.25))
    sleep(0.2)  # leave some time to robot to process the setup commands
    tool_orient_normal = m3d.Transform()
    print('ur10 connected')
    try:
        rob.set_pose(pos, acc, vel, wait=False)
    except:
        print("Robot could not execute move (emergency stop for example), do something")
    finally:
        print('UR 10 moved in tool base: {}'.format(goal_tool))
        trans = rob.get_pose()
        print('current pose::{}'.format(trans))
        # while True:
        #     sleep(0.01)  # sleep first since the robot may not have processed the command yet
        #     print('rob.is_program_running'.format(rob.is_program_running()))
        #     if rob.is_program_running():
        #         break
    rob.close()

def main_move_in_loop(loop,):
    acc_map = {0: 0.06,
               1: 0.03,
               2: 0.02,
               3: 0.06,
               }
    vel_map = {0: 0.06,
               1: 0.03,
               2: 0.02,
               3: 0.06,
               }
    for i, goal_tool in enumerate(loop):
        print('Executing {} in tool space'.format(goal_tool))
        acc = acc_map[i]
        vel = vel_map[i]
        main_ur10_repeat(goal_tool, times=1, boundary=boundary, acc=acc, vel=vel, wait=True)
        if i == 0:
            time.sleep(4)

if __name__ == '__main__':
    # main_ur10_thread()
    goal_tool1 = [-0.1, 0, 0.05, 0, 0, 0]  # move the robot in tool cord
    goal_tool2 = [0, 0.1, 0, 0, 0, 0]  # move the robot in tool cord
    goal_tool3 = [0, -0.12, 0, 0, 0, 0]  # move the robot in tool cord
    goal_tool4 = [0.1, 0.02, -0.05, 0, 0, 0]  # move the robot in tool cord
    goal_tool_adj = [0.05, 0, -0.1, 0, 0, 0]  # move the robot in tool cord
    loop_egg_gsp = [goal_tool1, goal_tool2, goal_tool3, goal_tool4]
    boundary = [[-0.05, 0.15], [-1.08, -1.4], [-0.192, 0.1]]
    init_pos = m3d.Transform()
    init_pos.orient = np.array([[0.99112324, 0.10186745, -0.08542689],
                            [-0.08254139, -0.03222018, -0.99606665],
                            [-0.10421924, 0.99427606, -0.02352589]])
    init_pos.pos = [0.13108, -1.12309, -0.07]

    acc = 0.02
    vel = 0.02

    main_move_in_loop(loop=loop_egg_gsp)
    # main_ur10_repeat(goal_tool4, times=1, boundary=boundary, acc=acc, vel=vel, wait=True)
    # init_ur_handover(init_pos)
