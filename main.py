from pymem import Pymem
from pymem.process import module_from_name
from pymem.memory import read_int, read_uchar, write_int, read_float, read_string
import time
import keyboard
import ctypes
import mouse
import win32api,win32con,win32gui
import os
from math import sqrt
#import esp
# CS 1.6'nın işleminin adı1"
process_name = "hl.exe"

# Pymem ile işlemi aç
pymem = Pymem(process_name)

# Modülleri bul
client_module = module_from_name(pymem.process_handle, "client.dll")
hw_module = module_from_name(pymem.process_handle, "hw.dll")
engine_module = module_from_name(pymem.process_handle, "engine.dll")

# Modülün baz adresini yazdır
print(f"client.dll Baz Adresi: {hex(client_module.lpBaseOfDll)}")
print(f"hw.dll Baz Adresi: {hex(hw_module.lpBaseOfDll)}")

# Offsetlar
offset_client = client_module.lpBaseOfDll
offset_hw = hw_module.lpBaseOfDll

offset_inChat = 0x64429C
offset_inMenu = 0x6c3ab0

offset_forceJump = 0x131434
offset_forceDuck = 0x1313B0
offset_onGround = 0x122E2D4
offset_ForceAttack = 0x131370  # client.dll
offset_localHeal = 0x121738 #client.dll
offset_localTeam = 0x100DF4 #client.dll 1=t 2=ct 0=spec
offset_crossTeam = 0x125314 #client.dll 512=ct 256=t 0=spec 2=t 1=ct
offset_viewMatrix = 0xEC9780
offset_Entity = 0x120461C
offset_Vec3 = 0x658840
offset_Resolution = 0xAB779C
offset_Zoom = 0xEC9E20

#Address's 
inChat_address = offset_hw + offset_inChat
inMenu_address = offset_hw + offset_inMenu
onGround_address = offset_hw + offset_onGround
forceJump_address = offset_client + offset_forceJump
forceDuck_address = offset_client + offset_forceDuck
ForceAttack_address = offset_client + offset_ForceAttack
localHeal_address = offset_client + offset_localHeal
localTeam_address = offset_client + offset_localTeam
crossTeam_address = offset_client + offset_crossTeam


viewMatrix_address = offset_hw + offset_viewMatrix
Entity_address = offset_hw + offset_Entity
Vec3_address = offset_hw + offset_Vec3
Resolution_address = offset_hw + offset_Resolution
Zoom_address = offset_hw + offset_Zoom


# Enum class for _IN_CROSS_OBJECT
class _IN_CROSS_OBJECT(ctypes.c_ubyte):
    INC_CROSS_CLEAR = 0
    INC_TERRORIST = 1
    INC_CT = 2
    INC_HOSTAGE = 3

#Aimbot Functions
'''
def read_resolution():
    w = read_int(pymem.process_handle,Resolution_address)
    h = read_int(pymem.process_handle,Resolution_address + 4)
    return w,h

def updateent():
    while True:
        sleep(0.5)
        for i in range(32):
            write_int(pymem.process_handle, Entity_address + 376 + 592 * i,0)

def parse_matrix(matrix_resolution):
    matrix = []
    for i in range(matrix_resolution):
        mat0 = read_float(pymem.process_handle, viewMatrix_address + 4 * i)
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
        x=read_float(pymem.process_handle, Entity_address + 388+ 592 * i) 
        y=read_float(pymem.process_handle, Entity_address + 392+ 592 * i)
        z=read_float(pymem.process_handle, Entity_address + 396+ 592 * i)
        vec3.append(x)
        vec3.append(y)
        vec3.append(z)
        players.append(vec3)
    return players


def players_team():
    teams = []
    for i in range(32):
        m =read_string(pymem.process_handle, Entity_address + 300 + 592 * i)
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
        val = read_float(pymem.process_handle,Entity_address + 376 + 592 * i)
        values.append(val)
    return values



def calc_dist(enemy_x,enemy_y,enemy_z):
    my_x = read_float(pymem.process_handle,Vec3_address)
    my_y = read_float(pymem.process_handle,Vec3_address + 4)
    my_z = read_float(pymem.process_handle,Vec3_address + 8)
    delta_x = enemy_x - my_x
    delta_y = enemy_y - my_y
    delta_z = enemy_z - my_z
    return sqrt(delta_x*delta_x + delta_y * delta_y + delta_z * delta_z)

def calc_scalling(w,h,distance,factor):
    aspect =read_float(pymem.process_handle,Zoom_address)
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
        my_team = read_int(pymem.process_handle,localTeam_address)
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
'''

# Ayarlar

#esp setting
espv1 = False
espv1_key = "ş"

#bunnyhop Settings
bunnyhop = False
bunnyhop_key = "space"

#ducking Settings
ducking = False
ducking_key = "c"

#aimbot settings
aimbot = False
aimbotfov = 10
aimbotsmooth = 1
aimbotrcs = 0
aimbotscalefactor = 360

#triggerbot Settings
triggerbot = False
triggerbotdelay = 0.206 # Her sıkma arası 200 ms bekleme
triggerbotfix = 0
last_trigger_time = time.time()

#Keybind Settings
last_espv1_time = 0
last_aimbot_time = 0
last_triggerbot_time = 0
last_bunnyhop_time = 0
last_ducking_time = 0
keybind_delay = 0.2  # Her tuş algılamasında 200 ms bekleme

#Fix
crossTeam = 0
localTeam = 0
fixedCrossTeam = 0

while True:
    current_time = time.time()
    health = read_int(pymem.process_handle, localHeal_address)
    inChat = read_int(pymem.process_handle, inChat_address)
    inMenu = read_int(pymem.process_handle, inMenu_address)
    
    if(inChat == 0 and inMenu == 0):
        #Keybinds
        # Esp toggle
        if keyboard.is_pressed("ş") and (current_time - last_espv1_time) > keybind_delay:
            espv1 = not espv1
            last_espv1_time = current_time  # Son algılama zamanını güncelle

        # Aimbot toggle
        if keyboard.is_pressed("o") and (current_time - last_aimbot_time) > keybind_delay:
            aimbot = not aimbot
            last_aimbot_time = current_time  # Son algılama zamanını güncelle
            
        # Triggerbot toggle
        if keyboard.is_pressed("j") and (current_time - last_triggerbot_time) > keybind_delay:
            triggerbot = not triggerbot
            last_triggerbot_time = current_time  # Son algılama zamanını güncelle

        # Bunnyhop toggle
        if keyboard.is_pressed("k") and (current_time - last_bunnyhop_time) > keybind_delay:
            bunnyhop = not bunnyhop
            last_bunnyhop_time = current_time  # Son algılama zamanını güncelle

        # Ducking toggle
        if keyboard.is_pressed("l") and (current_time - last_ducking_time) > keybind_delay:
            ducking = not ducking
            last_ducking_time = current_time  # Son algılama zamanını güncelle
        
        #Console debug
        print(f"Aimbot {'Acik' if aimbot else 'Kapali'} | Triggerbot {'Acik' if triggerbot else 'Kapali'} | Bunnyhop  {'Acik' if bunnyhop else 'Kapali'} | Ducking  {'Acik' if ducking else 'Kapali'}           ", end='\r')


        #main
        if(health > 1):
            # Aimbot
            '''
            if aimbot:
                time.sleep(0.01)
                w,h = read_resolution()              
                targets = get_targets()
                nearest_index = find_best_target(targets,w,h)


                fov = aimbotfov
                smooth = aimbotsmooth
                rcs = aimbotrcs
                SCALEFACTOR = aimbotscalefactor
                recoil_y = read_float(pymem.process_handle, offset_hw + 0x108AED0)
                recoil_x = read_float(pymem.process_handle, offset_hw + 0x108AED0 + 4)

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
            '''
            # Triggerbot
            in_cross = offset_client + 0x125314  # setup address

            if triggerbot:
                val = read_uchar(pymem.process_handle, in_cross)
                localTeam = read_int(pymem.process_handle, localTeam_address) #team 1 = t 2 = ct
                crossTeam = read_int(pymem.process_handle, crossTeam_address) # 2 == dusman
                if crossTeam != 0 and (crossTeam == 2) and (mouse.is_pressed(button='left') == False):
                    
                    if ((current_time - last_trigger_time) >= triggerbotdelay):
                        # Simulate mouse click (left click)
                        #print("\n\n Adamı gördüm sıkıyorum!")
                        crossTeam = read_int(pymem.process_handle, crossTeam_address) # 2 == dusman
                        write_int(pymem.process_handle, ForceAttack_address, 5)
                        time.sleep(0.0005)
                        write_int(pymem.process_handle, ForceAttack_address, 4)
                        triggerbotfix = 0
                        last_trigger_time = current_time  # update last trigger time
                elif crossTeam == _IN_CROSS_OBJECT.INC_CROSS_CLEAR:
                    if triggerbotfix < 1:
                        write_int(pymem.process_handle, ForceAttack_address, 4)
                        triggerbotfix += 2
            else:
                if triggerbotfix < 2:
                        write_int(pymem.process_handle, ForceAttack_address, 4)
                        triggerbotfix += 1
            # Bunnyhop
            if bunnyhop:
                onGround = read_int(pymem.process_handle, onGround_address)
                if keyboard.is_pressed(bunnyhop_key):
                    if onGround == 1:
                        write_int(pymem.process_handle, forceJump_address, 5)
                    else:
                        write_int(pymem.process_handle, forceJump_address, 4)

            # Ducking
            if ducking:
                onGround = read_int(pymem.process_handle, onGround_address)
                if keyboard.is_pressed(ducking_key):
                    if onGround == 1:
                        if read_int(pymem.process_handle, forceDuck_address) == 4:
                            write_int(pymem.process_handle, forceDuck_address, 5)
                        else:
                            write_int(pymem.process_handle, forceDuck_address, 4)
                    else:
                        write_int(pymem.process_handle, forceDuck_address, 4)
            else:
                write_int(pymem.process_handle, forceDuck_address, 4)

    time.sleep(0.005)
