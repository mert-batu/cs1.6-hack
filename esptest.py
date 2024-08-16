import pymem
import pymem.process
import win32api
import win32con
import win32gui
from time import sleep
from math import sqrt
import keyboard
from PIL import Image, ImageDraw
import numpy as np
from io import BytesIO

# Initialize pymem and game modules
pm = pymem.Pymem("hl.exe")
hw = pymem.process.module_from_name(pm.process_handle, "hw.dll").lpBaseOfDll
client = pymem.process.module_from_name(pm.process_handle, "client.dll").lpBaseOfDll

# Offsets
HWview_matrix = (0xEC9780)
HWEntity = (0x120461C)
HWVec3 = (0x658840)
HWResolution = (0xAB779C)
CLMyTeamNumber = (0x100DF4)
hwZOOMING = (0xEC9E20)

# Overlay window class
class ESPWindow:
    def __init__(self):
        self.hwnd = None
        self.hdc = None
        self.width = 800
        self.height = 600

        # Register window class
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.window_proc
        wc.lpszClassName = 'ESPOverlay'
        wc.hInstance = win32api.GetModuleHandle(None)
        wc.hCursor = win32api.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.hIcon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        class_atom = win32gui.RegisterClass(wc)

        # Create window
        self.hwnd = win32gui.CreateWindow(class_atom, 'ESP Overlay', win32con.WS_POPUP, 0, 0, self.width, self.height, 0, 0, 0, None)
        self.set_transparent()
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)

    def set_transparent(self):
        # Set window style to transparent
        ex_style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TOPMOST)
        win32gui.UpdateWindow(self.hwnd)
        win32gui.SetLayeredWindowAttributes(self.hwnd, win32api.RGB(0, 0, 0), 0, win32con.LWA_COLORKEY)

    def window_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_PAINT:
            self.paint()
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def paint(self):
        hdc = win32gui.GetDC(self.hwnd)
        mem_dc = win32gui.CreateCompatibleDC(hdc)
        bmp = win32gui.CreateCompatibleBitmap(hdc, self.width, self.height)
        old_bmp = win32gui.SelectObject(mem_dc, bmp)
        win32gui.BitBlt(hdc, 0, 0, self.width, self.height, mem_dc, 0, 0, win32con.SRCCOPY)
        win32gui.SelectObject(mem_dc, old_bmp)
        win32gui.DeleteDC(mem_dc)
        win32gui.ReleaseDC(self.hwnd, hdc)

# Utility functions
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
    return screenx, screeny

def read_players():
    players = []
    for i in range(32):
        x = pm.read_float(hw + HWEntity + 388 + 592 * i)
        y = pm.read_float(hw + HWEntity + 392 + 592 * i)
        z = pm.read_float(hw + HWEntity + 396 + 592 * i)
        players.append((x, y, z))
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
    aspect = pm.read_float(hw + hwZOOMING)
    if aspect > 1:
        w *= aspect
        h *= aspect
    try:
        return w / distance * factor, h / distance * factor
    except (ZeroDivisionError, TypeError):
        return False

def get_distance(screen, w, h):
    crosshairX, crosshairY = w / 2, h / 2
    distx = screen[0] - crosshairX
    disty = screen[1] - crosshairY
    return distx, disty

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

def find_best_target(targets, w, h):
    nearest_index = -1
    min_dist = 99999
    for i in range(len(targets)):
        screen = w2s(targets[i][0], targets[i][1], targets[i][2] + 18, w, h)
        if screen:
            distx, disty = get_distance(screen, w, h)
            dist = sqrt(distx * distx + disty * disty)
            if dist < min_dist:
                min_dist = dist
                nearest_index = i
    return nearest_index

def AIMBOT():
    while True:
        sleep(0.01)
        w, h = read_resolution()
        targets = get_targets()
        nearest_index = find_best_target(targets, w, h)

        fov = 2
        smooth = 8
        rcs = 0
        SCALEFACTOR = 360
        recoil_y = pm.read_float(hw + 0x108AED0)
        recoil_x = pm.read_float(hw + 0x108AED0 + 4)

        if nearest_index != -1:
            dist = calc_dist(targets[nearest_index][0], targets[nearest_index][1], targets[nearest_index][2] + 18)
            screen = w2s(targets[nearest_index][0], targets[nearest_index][1], targets[nearest_index][2] + 18, w, h)

            scalling = calc_scalling(fov, fov, dist, SCALEFACTOR)
            if screen and scalling:
                REC = (screen[0] + recoil_x * rcs, screen[1] + abs(recoil_y) * rcs)
                distx, disty = get_distance(REC, w, h)
                distx /= smooth
                disty /= smooth
                if abs(distx) <= scalling[0] and abs(disty) <= scalling[1]:
                    win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(distx), int(disty), 0, 0)
                    print(f"distx: {distx} | disty: {disty}")

def draw_esp():
    esp_window = ESPWindow()
    while True:
        sleep(0.1)
        w, h = read_resolution()
        players = read_players()

        # Clear previous drawing
        image = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw ESP for each player
        for player in players:
            screen = w2s(player[0], player[1], player[2] + 18, w, h)
            if screen:
                sx, sy = screen
                draw.ellipse((sx - 5, sy - 5, sx + 5, sy + 5), outline='red', width=2)

        # Convert image to bytes
        buffer = BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = buffer.getvalue()

        # Update window with the image (this part needs to be adapted to your specific requirements)
        # Example of updating the window might be required based on your implementation

# Run the AIMBOT and ESP drawing functions
from threading import Thread
Thread(target=AIMBOT).start()
Thread(target=draw_esp).start()
