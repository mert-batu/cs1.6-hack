import pygame
import pymem
import pymem.process
import pymem.memory
from pymem.process import module_from_name
import win32api
import win32con
import win32gui
from time import sleep
from math import sqrt

# RGB colors
GREEN = (0, 255, 0)

def Get_cs_window_coords():
    window_handle = win32gui.FindWindow(None, "Counter-Strike")
    window_rect = win32gui.GetWindowRect(window_handle)
    return window_rect

def set_transparent_window(window_handle):
    ex_style = win32gui.GetWindowLong(window_handle, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(window_handle, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE)
    win32gui.SetLayeredWindowAttributes(window_handle, win32api.RGB(0, 0, 0), 0, win32con.LWA_COLORKEY)
    win32gui.SetWindowPos(window_handle, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)

def DrawBox(display, color, x, y, width, height, thickness):
    lefttopX = x - width / 2
    lefttopY = y - height / 2
    pygame.draw.rect(display, color, pygame.Rect(lefttopX, lefttopY, width, height), thickness)
    
def set_window_gui(w, h):
    pygame.init()
    DISPLAY = pygame.display.set_mode((w, h), pygame.NOFRAME | pygame.SRCALPHA)
    window_handle = pygame.display.get_wm_info()["window"]
    set_transparent_window(window_handle)
    wincoord = Get_cs_window_coords()
    win32gui.SetWindowPos(window_handle, win32con.HWND_TOPMOST, 
                          wincoord[0], wincoord[1], w, h, 
                          win32con.SWP_NOSIZE | win32con.SWP_NOMOVE | win32con.SWP_NOACTIVATE)
    pygame.mouse.set_visible(False)
    
    return DISPLAY

HWview_matrix = (0xEC9780)
HWEntity = (0x120461C)
HWVec3 = (0x658840)
HWResolution = (0xAB779C)
CLMyTeamNumber = (0x100DF4)
CLHealth = (0x121738)

# Initialize Pymem
pm = pymem.Pymem(process_name="hl.exe")
hw = module_from_name(pm.process_handle, "hw.dll").lpBaseOfDll
client = module_from_name(pm.process_handle, "client.dll").lpBaseOfDll

def read_resolution():
    w = pm.read_int(hw + HWResolution)
    h = pm.read_int(hw + HWResolution + 4)
    return w, h

def parse_matrix(matrix_resolution):
    matrix = []
    for i in range(matrix_resolution):
        mat0 = pm.read_float(hw + HWview_matrix + 4 * i)
        matrix.append(mat0)
    return matrix

def w2s(x, y, z, w, h):
    matrix = parse_matrix(4 * 4)
    fovx = matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12]
    fovy = matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13]
    fovz = matrix[3] * x + matrix[7] * y + matrix[11] * z + matrix[15]
    if fovz < 0.01:
        return False
    nx = fovx / fovz
    ny = fovy / fovz
    screenx = (w / 2 * nx) + (w / 2 + nx)
    screeny = -((h / 2 * ny) - (h / 2 + ny))
    if 0 <= screenx <= w and 0 <= screeny <= h:  # Ensure the coordinates are within screen bounds
        return screenx, screeny
    return False

def read_players():
    players = []
    for i in range(32):
        vec3 = []
        x = pm.read_float(hw + HWEntity + 388 + 592 * i)
        y = pm.read_float(hw + HWEntity + 392 + 592 * i)
        z = pm.read_float(hw + HWEntity + 396 + 592 * i)
        vec3.append(x)
        vec3.append(y)
        vec3.append(z)
        players.append(vec3)
    return players

def players_team():
    teams = []
    for i in range(32):
        m = pm.read_string(hw + HWEntity + 300 + 592 * i)
        if m in ['leet', 'terror', 'guerilla', 'arctic']:
            teams.append(1)
        elif m in ['gign', 'sas', 'urban', 'gsg9', 'vip']:
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

def calc_dist(enemy_x, enemy_y, enemy_z):
    my_x = pm.read_float(hw + HWVec3)
    my_y = pm.read_float(hw + HWVec3 + 4)
    my_z = pm.read_float(hw + HWVec3 + 8)
    delta_x = enemy_x - my_x
    delta_y = enemy_y - my_y
    delta_z = enemy_z - my_z
    return sqrt(delta_x * delta_x + delta_y * delta_y + delta_z * delta_z)

def calc_scalling(w, h, distance, factor):
    try:
        return w / distance * factor, h / distance * factor
    except (ZeroDivisionError, TypeError):
        return False

def get_targets():
    targets = []
    players = read_players()
    teams = players_team()
    val = read_val()
    my_team = pm.read_int(client + CLMyTeamNumber)
    for i in range(len(players)):
        if teams[i] != my_team and val[i] != 0:
            targets.append(players[i])
    return targets

def ESP():
    msTime = input("Kac ms aktarsın görüntüyü?\n 0.01 --> Oyun içinde ne yaşanıyorsa direk aktarır fakat sistemi kastırır\n 0.05 --> Oyun içinde ne yaşınıyorsa birazcik gecilmeli aktarır fakat sistemi kastırmaz. \n")
    pygame.init()
    resolution = read_resolution()
    display = set_window_gui(resolution[0], resolution[1])
    while True:
        Health = pm.read_float(client + CLHealth)
        if (Health <= 1):
            display.fill((0, 0, 0, 0))
        sleep(msTime)
        resolution = read_resolution()
        display.fill((0, 0, 0, 0))
        targets = get_targets()
        for target in targets:
            screen = w2s(target[0], target[1], target[2] + 18, resolution[0], resolution[1])
            dist = calc_dist(target[0], target[1], target[2])
            scalling = calc_scalling(15, 25, dist, resolution[0])
            if screen and scalling:
                width, height = scalling
                DrawBox(display, GREEN, screen[0], screen[1], width, height, 2)
        pygame.display.update()
        sleep(msTime)

while True:
    ESP()