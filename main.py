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
from pathlib import Path

# Kullanıcı dizinini alma
home_dir = Path.home()

# Kullanıcı adını içeren bir dosya yolu oluşturma
print(f"pyXternal - CS 1.6\n")

selectPath = int(input(f"(System) Select Path Location: \n (1) {home_dir}/Documents/Adobe/Adobe_DATA \n (2) Custom Path \n"))
if(selectPath == 1):
    path = f'{home_dir}/Documents/Adobe/Adobe_DATA'
elif(selectPath == 2):
    path_str = input(f"(System) Folder path location: \n")
    path = Path(path_str)
else:
    path = f'{home_dir}/Documents/Adobe/Adobe_DATA'
selectName = int(input(f"(System) Select File Name: \n (1) log_1401202414458947 \n (2) Custom File Name \n"))
if(selectName == 1):
    filename = f'{path}/log_1401202414458947.txt'
elif(selectName == 2):
    filename_str = input(f"(System) File name without txt: \n")
    filename = f'{path}/{filename_str}.txt'
else:
    filename = f'{path}/log_1401202414458947.txt'

#Ayarları Okuma
def read_key_value(filename, key):
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith(key):
                # Anahtarı bulduğumuzda, eşittir işaretinden sonraki kısmı alıyoruz
                return line.split('=')[1].strip().strip('"')
    return None
def read_boollean_value(filename, key):
    with open(filename, 'r') as file:
        for line in file:
            if line.startswith(key):
                # Anahtarı bulduğumuzda, eşittir işaretinden sonraki kısmı alıyoruz
                value = line.split('=')[1].strip().strip('"')
                if value == 'true':
                    return True
                elif value == 'false':
                    return False
    return None

def get_status_message(triggerbotv1, triggerbotv2, bunnyhop, ducking, lang):
    if lang == "tr":
        return (f"Triggerbotv1(inCross) {'Acik' if triggerbotv1 else 'Kapali':<10} | "
                f"Triggerbotv2(inCross&position) {'Acik' if triggerbotv2 else 'Kapali':<10} | "
                f"Bunnyhop  {'Acik' if bunnyhop else 'Kapali':<10} | "
                f"Ducking  {'Acik' if ducking else 'Kapali':<10}")
    elif lang == "en":
        return (f"Triggerbotv1(inCross) {'Enabled' if triggerbotv1 else 'Disabled':<10} | "
                f"Triggerbotv2(inCross&position) {'Enabled' if triggerbotv2 else 'Disabled':<10} | "
                f"Bunnyhop  {'Enabled' if bunnyhop else 'Disabled':<10} | "
                f"Ducking  {'Enabled' if ducking else 'Disabled':<10}")
    else:
        return (f"Triggerbotv1(inCross) {'Acik' if triggerbotv1 else 'Kapali':<10} | "
                f"Triggerbotv2(inCross&position) {'Acik' if triggerbotv2 else 'Kapali':<10} | "
                f"Bunnyhop  {'Acik' if bunnyhop else 'Kapali':<10} | "
                f"Ducking  {'Acik' if ducking else 'Kapali':<10}")

def update_console(triggerbotv1, triggerbotv2, bunnyhop, ducking, lang):
    global last_status_message
    current_message = get_status_message(triggerbotv1, triggerbotv2, bunnyhop, ducking, lang)
    if current_message != last_status_message:
        print(f"{current_message: <80}", end='\r')
        last_status_message = current_message

# CS 1.6'nın işleminin adı
process_name = "hl.exe"

# Pymem ile işlemi aç
pymem = Pymem(process_name)

# Modülleri bul
client_module = module_from_name(pymem.process_handle, "client.dll")
hw_module = module_from_name(pymem.process_handle, "hw.dll")
engine_module = module_from_name(pymem.process_handle, "engine.dll")

# Offsetlar
offset_client = client_module.lpBaseOfDll
offset_hw = hw_module.lpBaseOfDll
offset_inChat = 0x64429C
offset_inMenu = 0x6c3ab0
offset_forceJump = 0x131434
offset_forceDuck = 0x1313B0
offset_onGround = 0x122E2D4
offset_ForceAttack = 0x131370  
offset_localHeal = 0x121738 
offset_localTeam = 0x100DF4 
offset_crossTeam = 0x125314 
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

# Ayarlar
#language
lang = (read_key_value(filename, "language"))
debug = (read_boollean_value(filename, "debug"))

#bunnyhop Settings
bunnyhop = (read_boollean_value(filename, "bh0p_enabled"))
bunnyhop_key = (read_key_value(filename, "bh0p_key"))
bunnyhop_jmp_key = (read_key_value(filename, "bh0p_jmp_key"))

#ducking Settings
ducking = (read_boollean_value(filename, "dck_enabled"))
duck_key = (read_key_value(filename, "dck_key"))
ducking_key = (read_key_value(filename, "dcking_key"))


#triggerbotv1 Settings
triggerbotv1 = (read_boollean_value(filename, "tb0tv1_enabled"))
triggerbotv1delay = float(read_key_value(filename, "tb0tv1_delay"))
triggerbotv1fix = 0
last_triggerv1_time = time.time()
triggerbotv1_key = (read_key_value(filename, "tb0tv1_key"))

#triggerbotv2 Settings
triggerbotv2 = (read_boollean_value(filename, "tb0tv2_enabled"))
triggerbotv2_limit = int(read_key_value(filename, "tb0tv2_incrossbutnotdetectedlimit"))
triggerbotv2_key = (read_key_value(filename, "tb0tv2_key"))

#Keybind Settings
last_triggerbotv1_time = 0
last_triggerbotv2_time = 0
last_bunnyhop_time = 0
last_ducking_time = 0
keybind_delay = 0.2  # Her tuş algılamasında 200 ms bekleme

#Fix
last_status_message = ""
crossTeam = 0
localTeam = 0
fixedCrossTeam = 0
in_cross_but_not_offset_detected = 0
#triggerv2
def read_resolution():
    w = read_int(pymem.process_handle, Resolution_address)
    h = read_int(pymem.process_handle, Resolution_address + 4)
    return w, h

def parse_matrix(matrix_resolution):
    matrix = []
    for i in range(matrix_resolution):
        mat0 = read_float(pymem.process_handle, viewMatrix_address + 4 * i)
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
        vec3 = []
        x = read_float(pymem.process_handle, Entity_address + 388 + 592 * i)
        y = read_float(pymem.process_handle, Entity_address + 392 + 592 * i)
        z = read_float(pymem.process_handle, Entity_address + 396 + 592 * i)
        vec3.append(x)
        vec3.append(y)
        vec3.append(z)
        players.append(vec3)
    return players

def players_team():
    teams = []
    for i in range(32):
        m = read_string(pymem.process_handle, Entity_address + 300 + 592 * i)
        if m == 'leet' or m == 'terror' or m == 'guerilla' or m == 'arctic':
            teams.append(1)
        elif m == 'gign' or m == 'sas' or m == 'urban' or m == 'gsg9' or m == 'vip':
            teams.append(2)
        else:
            teams.append(3)
    return teams

def read_val():
    values = []
    for i in range(32):
        val = read_float(pymem.process_handle, Entity_address + 376 + 592 * i)
        values.append(val)
    return values

def get_targets():
    targets = []
    players = read_players()
    teams = players_team()
    val = read_val()
    my_team = read_int(pymem.process_handle, localTeam_address)
    for i in range(len(players)):
        if teams[i] != my_team and val[i] != 0:
            targets.append(players[i])
    return targets

def find_target_at_crosshair(targets, w, h):
    crosshairX, crosshairY = w / 2, h / 2
    for target in targets:
        screen = w2s(target[0], target[1], target[2] + 18, w, h)
        if screen:
            distx = screen[0] - crosshairX
            disty = screen[1] - crosshairY
            if abs(distx) < 5 and abs(disty) < 5:
                return True
    return False

# Modülün baz adresini yazdır
if(debug):
    if(lang == "tr"):
        print(f"\n\n client.dll Baz Adresi: {hex(client_module.lpBaseOfDll)}")
        print(f"hw.dll Baz Adresi: {hex(hw_module.lpBaseOfDll)}\n\n ")
    elif(lang == "en"):
        print(f"\n\n client.dll Offset Adress: {hex(client_module.lpBaseOfDll)}")
        print(f"hw.dll Offset Adress: {hex(hw_module.lpBaseOfDll)}\n\n ")
    else:
        print(f"\n\n client.dll Baz Adresi: {hex(client_module.lpBaseOfDll)}")
        print(f"hw.dll Baz Adresi: {hex(hw_module.lpBaseOfDll)}\n\n ")


while True:
    current_time = time.time()
    health = read_int(pymem.process_handle, localHeal_address)
    inChat = read_int(pymem.process_handle, inChat_address)
    inMenu = read_int(pymem.process_handle, inMenu_address)
    update_console(triggerbotv1, triggerbotv2, bunnyhop, ducking, lang)
    if(inChat == 0 and inMenu == 0):
        #Keybinds
        # Triggerbot V1 toggle
        if keyboard.is_pressed(triggerbotv1_key) and (current_time - last_triggerbotv1_time) > keybind_delay:
            triggerbotv1 = not triggerbotv1
            last_triggerbotv1_time = current_time  # Son algılama zamanını güncelle

        # Triggerbot V2 toggle
        if keyboard.is_pressed(triggerbotv2_key) and (current_time - last_triggerbotv2_time) > keybind_delay:
            triggerbotv2 = not triggerbotv2
            last_triggerbotv2_time = current_time  # Son algılama zamanını güncelle

        # Bunnyhop toggle
        if keyboard.is_pressed(bunnyhop_key) and (current_time - last_bunnyhop_time) > keybind_delay:
            bunnyhop = not bunnyhop
            last_bunnyhop_time = current_time  # Son algılama zamanını güncelle

        # Ducking toggle
        if keyboard.is_pressed(duck_key) and (current_time - last_ducking_time) > keybind_delay:
            ducking = not ducking
            last_ducking_time = current_time  # Son algılama zamanını güncelle
        
        
        #main
        if(health > 1):
            # Triggerbot v1
            in_cross = offset_client + 0x125314  # setup address

            if triggerbotv1:
                val = read_uchar(pymem.process_handle, in_cross)
                localTeam = read_int(pymem.process_handle, localTeam_address) #team 1 = t 2 = ct
                crossTeam = read_int(pymem.process_handle, crossTeam_address) # 2 == dusman
                if crossTeam != 0 and (crossTeam == 2) and (mouse.is_pressed(button='left') == False):
                    
                    if ((current_time - last_triggerv1_time) >= triggerbotv1delay):
                        crossTeam = read_int(pymem.process_handle, crossTeam_address) # 2 == dusman
                        write_int(pymem.process_handle, ForceAttack_address, 5)
                        time.sleep(0.0005)
                        write_int(pymem.process_handle, ForceAttack_address, 4)
                        triggerbotv1fix = 0
                        last_triggerv1_time = current_time  # update last trigger time
                elif crossTeam == 0:
                    if triggerbotv1fix < 1:
                        write_int(pymem.process_handle, ForceAttack_address, 4)
                        triggerbotv1fix += 2
            else:
                if triggerbotv1fix < 2:
                        write_int(pymem.process_handle, ForceAttack_address, 4)
                        triggerbotv1fix += 1

            if triggerbotv2:
                w, h = read_resolution()
                targets = get_targets()
                if find_target_at_crosshair(targets, w, h):
                    in_cross_but_not_offset_detected +=1
                    if in_cross == 2 or in_cross_but_not_offset_detected > triggerbotv2_limit:
                        write_int(pymem.process_handle, ForceAttack_address, 5)
                        time.sleep(0.03)
                        write_int(pymem.process_handle, ForceAttack_address, 4)
                        in_cross_but_not_offset_detected = 0
  

            # Bunnyhop
            if bunnyhop:
                onGround = read_int(pymem.process_handle, onGround_address)
                if keyboard.is_pressed(bunnyhop_jmp_key):
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