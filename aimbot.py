import pymem
import pymem.process
import win32api,win32con,win32gui
pm = pymem.Pymem("hl.exe")

hw = pymem.process.module_from_name(pm.process_handle, "hw.dll").lpBaseOfDll
client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll


HWview_matrix = (0xEC9780)
HWEntity = (0x120461C)
HWVec3 = (0x658840)
HWResolution = (0xAB779C)
CLMyTeamNumber = (0x100DF4)
hwZOOMING = (0xEC9E20)

from time import sleep
from math import sqrt
import keyboard

def read_resolution():
    w = pm.read_int(hw+HWResolution)
    h = pm.read_int(hw+HWResolution + 4)
    return w,h

def updateent():
    while True:
        sleep(0.5)
        for i in range(32):
            pm.write_int(hw + HWEntity + 376 + 592 * i,0)

def parse_matrix(matrix_resolution):
    matrix = []
    for i in range(matrix_resolution):
        mat0 = pm.read_float(hw + HWview_matrix + 4 * i)
        matrix.append(mat0)
    return matrix



def w2s(x,y,z,w,h):
    matrix = parse_matrix(4*4)
    fovx = matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12]
    fovy = matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13]
    fovz = matrix[3] * x + matrix[7] * y + matrix[11] * z+ matrix[15]
    if fovz < 0.01:
        return False
    nx = fovx / fovz
    ny = fovy / fovz
    screenx = (w/2 * nx) + (w/2 + nx)
    screeny = -((h/2 * ny) - (h/2 + ny)) 
    return screenx,screeny
  
        
def read_players():
    players = []
    for i in range(32):
        vec3 = []
        x=pm.read_float(hw + HWEntity + 388+ 592 * i) 
        y=pm.read_float(hw + HWEntity + 392+ 592 * i)
        z=pm.read_float(hw + HWEntity + 396+ 592 * i)
        vec3.append(x)
        vec3.append(y)
        vec3.append(z)
        players.append(vec3)
    return players


def players_team():
    teams = []
    for i in range(32):
        m =pm.read_string(hw+HWEntity + 300 + 592 * i)
        if m == 'leet' or m == 'terror' or m == 'guerilla' or m == 'arctic':
            teams.append(1) 
        elif m == 'gign' or m == 'sas' or m == 'urban' or m == 'gsg9'or m == 'vip':
            teams.append(2)
        else:
            teams.append(3)
    return teams
        
def read_val():
    values = []
    for i in range(32):
        val = pm.read_float(hw + HWEntity + 376 + 592 * i)
        values.append(val)
    return values



def calc_dist(enemy_x,enemy_y,enemy_z):
    my_x = pm.read_float(hw + HWVec3)
    my_y = pm.read_float(hw + HWVec3 + 4)
    my_z = pm.read_float(hw + HWVec3 + 8)
    delta_x = enemy_x - my_x
    delta_y = enemy_y - my_y
    delta_z = enemy_z - my_z
    return sqrt(delta_x*delta_x + delta_y * delta_y + delta_z * delta_z)

def calc_scalling(w,h,distance,factor):
    aspect =pm.read_float(hw + hwZOOMING)
    if aspect > 1:
        w *=aspect
        h *= aspect
    try:
        return w / distance * factor,h / distance * factor
    except(ZeroDivisionError,TypeError): return False


def get_distance(screen,w,h):
    crosshairX,crosshairY =w/2,h/2
    distx = screen[0] - crosshairX 
    disty = screen[1] - crosshairY
    return distx,disty
    

def get_targets():
        targets = []              
        players = read_players()
        teams = players_team()
        val = read_val()
        my_team = pm.read_int(client + CLMyTeamNumber)
        for i in range(len(players)):
            if teams[i] != my_team and val[i] !=0:
                targets.append(players[i])
        return targets

def find_best_target(targets:list,w,h):
    nearest_index = -1
    min_dist = 99999
    for i in range(len(targets)):
        screen =    (targets[i][0],targets[i][1],targets[i][2] + 18,w,h)
        if screen:
            distx,disty = get_distance(screen,w,h)
            dist = sqrt(distx * distx + disty * disty)
            if dist < min_dist:
                min_dist = dist
                nearest_index = i
    return nearest_index

def AIMBOT():
    while True:
        sleep(0.01)
        w,h = read_resolution()              
        targets = get_targets()
        nearest_index = find_best_target(targets,w,h)


        fov = 2
        smooth = 8
        rcs = 0
        SCALEFACTOR = 360
        recoil_y = pm.read_float(hw + 0x108AED0)
        recoil_x = pm.read_float(hw + 0x108AED0 + 4)

        if nearest_index != -1:
            dist = calc_dist(targets[nearest_index][0],targets[nearest_index][1],targets[nearest_index][2] + 18)
            screen = w2s(targets[nearest_index][0],targets[nearest_index][1],targets[nearest_index][2] + 18,w,h)

            scalling = calc_scalling(fov,fov,dist,SCALEFACTOR)
            if screen and scalling:
                REC = (screen[0] + recoil_x * rcs,screen[1] +abs(recoil_y) * rcs)
                distx,disty =get_distance(REC,w,h)
                distx /= smooth
                disty /=smooth
                if abs(distx) <= scalling[0] and abs(disty) <= scalling[1]:
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(distx), int(disty), 0, 0)   
                    print(f"distx: {distx} | disty: {disty}")


AIMBOT()