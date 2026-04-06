# pyright: reportMissingImports=false, reportMissingModuleSource=false

from __future__ import annotations

import platform
import threading
import time
from dataclasses import dataclass
from math import sqrt
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import keyboard
import mouse
import win32api
import win32con
import win32gui
from pymem import Pymem
from pymem.memory import read_float, read_int, read_string, read_uchar, write_int
from pymem.process import module_from_name

try:
    import pygame

    PYGAME_AVAILABLE = True
except ImportError:
    pygame = None
    PYGAME_AVAILABLE = False

DEFAULT_CONFIG_TEMPLATE = """[SETTINGS]
language = "tr"
debug = "false"
loop_delay = "0.005"
keybind_delay = "0.20"
overlay_refresh = "0.02"

[tb0t SETTINGS]
tb0tv1_delay = "0.244"
tb0tv2_incrossbutnotdetectedlimit = "8"

[KEYBINDS]
tb0tv1_enabled = "false"
tb0tv1_key = "h"
tb0tv2_enabled = "false"
tb0tv2_key = "j"
bh0p_enabled = "false"
bh0p_key = "k"
bh0p_jmp_key = "space"
dck_enabled = "false"
dck_key = "l"
dcking_key = "c"
aim_enabled = "false"
aim_key = "u"
aim_hold_key = ""
esp_enabled = "false"
esp_key = "i"
crosshair_enabled = "true"
crosshair_key = "o"

[AIMBOT]
aim_fov = "2"
aim_smooth = "8"
aim_rcs = "0"
aim_scalefactor = "360"

[DUCK]
duck_spam_interval = "0.025"

[OVERLAY]
crosshair_size = "24"
crosshair_thickness = "1"
esp_box_width = "15"
esp_box_height = "25"
"""


def parse_flat_config(file_path: Path) -> Dict[str, str]:
    data: Dict[str, str] = {}
    try:
        with file_path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()
                if not stripped or stripped.startswith(("[", "#", ";")) or "=" not in stripped:
                    continue
                key, value = stripped.split("=", 1)
                data[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        pass
    return data


def to_bool(value: Optional[str], default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in ("true", "1", "yes", "on"):
        return True
    if normalized in ("false", "0", "no", "off"):
        return False
    return default


def to_int(value: Optional[str], default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def to_float(value: Optional[str], default: float = 0.0) -> float:
    try:
        return float(str(value).strip().replace(",", "."))
    except (TypeError, ValueError):
        return default


def clamp_float(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(value, max_value))


def normalize_key(value: Optional[str], fallback: str = "") -> str:
    if isinstance(value, str):
        candidate = value.strip().lower()
        if candidate:
            return candidate
    return fallback


def safe_int_input(prompt: str, default_value: int) -> int:
    try:
        return int(input(prompt).strip())
    except (TypeError, ValueError):
        return default_value


def open_native_text_picker(default_dir: Path) -> Optional[Path]:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askopenfilename(
        title="Select configuration txt file",
        initialdir=str(default_dir),
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
    )
    root.destroy()

    if not selected:
        return None
    return Path(selected)


def open_native_folder_picker(default_dir: Path) -> Optional[Path]:
    try:
        import tkinter as tk
        from tkinter import filedialog
    except Exception:
        return None

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    selected = filedialog.askdirectory(
        title="Select configuration folder",
        initialdir=str(default_dir),
    )
    root.destroy()

    if not selected:
        return None
    return Path(selected)


def ensure_config_file(file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not file_path.exists():
        file_path.write_text(DEFAULT_CONFIG_TEMPLATE, encoding="utf-8")


@dataclass
class RuntimeSettings:
    language: str = "tr"
    debug: bool = False
    loop_delay: float = 0.005
    keybind_delay: float = 0.2
    overlay_refresh: float = 0.02

    triggerbotv1_enabled: bool = False
    triggerbotv1_key: str = "h"
    triggerbotv1_delay: float = 0.244

    triggerbotv2_enabled: bool = False
    triggerbotv2_key: str = "j"
    triggerbotv2_limit: int = 8

    bunnyhop_enabled: bool = False
    bunnyhop_key: str = "k"
    bunnyhop_jump_key: str = "space"

    ducking_enabled: bool = False
    duck_toggle_key: str = "l"
    ducking_hold_key: str = "c"
    duck_spam_interval: float = 0.025

    aimbot_enabled: bool = False
    aimbot_key: str = "u"
    aimbot_hold_key: str = ""
    aimbot_fov: float = 2.0
    aimbot_smooth: float = 8.0
    aimbot_rcs: float = 0.0
    aimbot_scalefactor: float = 360.0

    esp_enabled: bool = False
    esp_key: str = "i"

    crosshair_enabled: bool = True
    crosshair_key: str = "o"
    crosshair_size: int = 24
    crosshair_thickness: int = 1

    esp_box_width: float = 15.0
    esp_box_height: float = 25.0


def load_runtime_settings(config_path: Path) -> RuntimeSettings:
    raw = parse_flat_config(config_path)

    settings = RuntimeSettings(
        language=(raw.get("language", "tr").strip().lower() or "tr"),
        debug=to_bool(raw.get("debug"), False),
        loop_delay=clamp_float(to_float(raw.get("loop_delay"), 0.005), 0.001, 0.1),
        keybind_delay=clamp_float(to_float(raw.get("keybind_delay"), 0.2), 0.05, 1.5),
        overlay_refresh=clamp_float(to_float(raw.get("overlay_refresh"), 0.02), 0.005, 0.2),
        triggerbotv1_enabled=to_bool(raw.get("tb0tv1_enabled"), False),
        triggerbotv1_key=normalize_key(raw.get("tb0tv1_key"), "h"),
        triggerbotv1_delay=clamp_float(to_float(raw.get("tb0tv1_delay"), 0.244), 0.01, 1.0),
        triggerbotv2_enabled=to_bool(raw.get("tb0tv2_enabled"), False),
        triggerbotv2_key=normalize_key(raw.get("tb0tv2_key"), "j"),
        triggerbotv2_limit=max(1, to_int(raw.get("tb0tv2_incrossbutnotdetectedlimit"), 8)),
        bunnyhop_enabled=to_bool(raw.get("bh0p_enabled"), False),
        bunnyhop_key=normalize_key(raw.get("bh0p_key"), "k"),
        bunnyhop_jump_key=normalize_key(raw.get("bh0p_jmp_key"), "space"),
        ducking_enabled=to_bool(raw.get("dck_enabled"), False),
        duck_toggle_key=normalize_key(raw.get("dck_key"), "l"),
        ducking_hold_key=normalize_key(raw.get("dcking_key"), "c"),
        duck_spam_interval=clamp_float(to_float(raw.get("duck_spam_interval"), 0.025), 0.005, 0.2),
        aimbot_enabled=to_bool(raw.get("aim_enabled"), False),
        aimbot_key=normalize_key(raw.get("aim_key"), "u"),
        aimbot_hold_key=normalize_key(raw.get("aim_hold_key"), ""),
        aimbot_fov=clamp_float(to_float(raw.get("aim_fov"), 2.0), 0.2, 20.0),
        aimbot_smooth=clamp_float(to_float(raw.get("aim_smooth"), 8.0), 1.0, 50.0),
        aimbot_rcs=clamp_float(to_float(raw.get("aim_rcs"), 0.0), 0.0, 5.0),
        aimbot_scalefactor=clamp_float(to_float(raw.get("aim_scalefactor"), 360.0), 20.0, 1000.0),
        esp_enabled=to_bool(raw.get("esp_enabled"), False),
        esp_key=normalize_key(raw.get("esp_key"), "i"),
        crosshair_enabled=to_bool(raw.get("crosshair_enabled"), True),
        crosshair_key=normalize_key(raw.get("crosshair_key"), "o"),
        crosshair_size=max(6, to_int(raw.get("crosshair_size"), 24)),
        crosshair_thickness=max(1, to_int(raw.get("crosshair_thickness"), 1)),
        esp_box_width=clamp_float(to_float(raw.get("esp_box_width"), 15.0), 5.0, 100.0),
        esp_box_height=clamp_float(to_float(raw.get("esp_box_height"), 25.0), 5.0, 180.0),
    )

    if settings.language not in ("tr", "en"):
        settings.language = "tr"

    return settings


def select_config_file() -> Path:
    home_dir = Path.home()
    default_dir = home_dir / "Documents" / "Adobe" / "Adobe_DATA"
    default_file = default_dir / "log_1401202414458947.txt"

    os_name = platform.system()
    print("pyXternal - CS 1.6")
    print(f"(System) Detected OS: {os_name}")

    choice = safe_int_input(
        (
            "(System) Select Config Mode:\n"
            f" (1) Default ({default_file})\n"
            " (2) Native TXT picker\n"
            " (3) Native folder picker + file name\n"
        ),
        2,
    )

    if choice == 2:
        selected = open_native_text_picker(default_dir)
        if selected:
            return selected
        print("(System) Native TXT picker cancelled. Default config will be used.")
        return default_file

    if choice == 3:
        folder = open_native_folder_picker(default_dir)
        if folder:
            name = input("(System) Config file name (without .txt):\n").strip()
            if not name:
                name = "log_1401202414458947"
            if not name.lower().endswith(".txt"):
                name = f"{name}.txt"
            return folder / name

        print("(System) Native folder picker cancelled. Default config will be used.")
        return default_file

    return default_file


@dataclass(frozen=True)
class Offsets:
    in_chat: int = 0x64429C
    in_menu: int = 0x6C3AB0
    force_jump: int = 0x131434
    force_duck: int = 0x1313B0
    force_attack: int = 0x131370
    on_ground: int = 0x122E2D4

    local_health: int = 0x121738
    local_team: int = 0x100DF4
    cross_team: int = 0x125314

    view_matrix: int = 0xEC9780
    entity: int = 0x120461C
    vec3: int = 0x658840
    resolution: int = 0xAB779C
    zoom: int = 0xEC9E20
    recoil: int = 0x108AED0


class CS16Memory:
    def __init__(self) -> None:
        self.offsets = Offsets()
        self.lock = threading.Lock()

        try:
            self.pm = Pymem("hl.exe")
        except Exception as exc:
            raise RuntimeError("hl.exe process not found. Open CS 1.6 first.") from exc

        self.client_module = module_from_name(self.pm.process_handle, "client.dll")
        self.hw_module = module_from_name(self.pm.process_handle, "hw.dll")

        if not self.client_module or not self.hw_module:
            raise RuntimeError("client.dll or hw.dll could not be loaded.")

        self.offset_client = self.client_module.lpBaseOfDll
        self.offset_hw = self.hw_module.lpBaseOfDll

        self.addr = {
            "in_chat": self.offset_hw + self.offsets.in_chat,
            "in_menu": self.offset_hw + self.offsets.in_menu,
            "force_jump": self.offset_client + self.offsets.force_jump,
            "force_duck": self.offset_client + self.offsets.force_duck,
            "force_attack": self.offset_client + self.offsets.force_attack,
            "on_ground": self.offset_hw + self.offsets.on_ground,
            "local_health": self.offset_client + self.offsets.local_health,
            "local_team": self.offset_client + self.offsets.local_team,
            "cross_team": self.offset_client + self.offsets.cross_team,
            "in_cross": self.offset_client + self.offsets.cross_team,
            "view_matrix": self.offset_hw + self.offsets.view_matrix,
            "entity": self.offset_hw + self.offsets.entity,
            "vec3": self.offset_hw + self.offsets.vec3,
            "resolution": self.offset_hw + self.offsets.resolution,
            "zoom": self.offset_hw + self.offsets.zoom,
            "recoil": self.offset_hw + self.offsets.recoil,
        }

    def read_int(self, address: int, default: int = 0) -> int:
        with self.lock:
            try:
                return read_int(self.pm.process_handle, address)
            except Exception:
                return default

    def read_uchar(self, address: int, default: int = 0) -> int:
        with self.lock:
            try:
                return read_uchar(self.pm.process_handle, address)
            except Exception:
                return default

    def read_float(self, address: int, default: float = 0.0) -> float:
        with self.lock:
            try:
                return read_float(self.pm.process_handle, address)
            except Exception:
                return default

    def read_string(self, address: int, default: str = "") -> str:
        with self.lock:
            try:
                return read_string(self.pm.process_handle, address)
            except Exception:
                return default

    def write_int(self, address: int, value: int) -> None:
        with self.lock:
            try:
                write_int(self.pm.process_handle, address, value)
            except Exception:
                return

    def tap_attack(self, press_time: float) -> None:
        self.write_int(self.addr["force_attack"], 5)
        time.sleep(press_time)
        self.write_int(self.addr["force_attack"], 4)

    def read_resolution(self) -> Tuple[int, int]:
        w = self.read_int(self.addr["resolution"], 0)
        h = self.read_int(self.addr["resolution"] + 4, 0)
        if w <= 0 or h <= 0:
            w = win32api.GetSystemMetrics(0)
            h = win32api.GetSystemMetrics(1)
        return w, h

    def parse_matrix(self) -> List[float]:
        matrix: List[float] = []
        base = self.addr["view_matrix"]
        for i in range(16):
            value = self.read_float(base + 4 * i, None)  # type: ignore[arg-type]
            if value is None:
                return []
            matrix.append(value)
        return matrix

    def world_to_screen(
        self,
        x: float,
        y: float,
        z: float,
        width: int,
        height: int,
        matrix: List[float],
    ) -> Optional[Tuple[float, float]]:
        if len(matrix) != 16:
            return None

        fovx = matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12]
        fovy = matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13]
        fovz = matrix[3] * x + matrix[7] * y + matrix[11] * z + matrix[15]

        if fovz < 0.01:
            return None

        nx = fovx / fovz
        ny = fovy / fovz
        screen_x = (width / 2 * nx) + (width / 2 + nx)
        screen_y = -((height / 2 * ny) - (height / 2 + ny))
        return screen_x, screen_y

    def read_players(self) -> List[Tuple[float, float, float]]:
        players: List[Tuple[float, float, float]] = []
        base = self.addr["entity"]
        for i in range(32):
            entity_base = base + 592 * i
            x = self.read_float(entity_base + 388, 0.0)
            y = self.read_float(entity_base + 392, 0.0)
            z = self.read_float(entity_base + 396, 0.0)
            players.append((x, y, z))
        return players

    def players_team(self) -> List[int]:
        teams: List[int] = []
        base = self.addr["entity"]
        for i in range(32):
            entity_base = base + 592 * i
            model = self.read_string(entity_base + 300, "")
            if model in ("leet", "terror", "guerilla", "arctic"):
                teams.append(1)
            elif model in ("gign", "sas", "urban", "gsg9", "vip"):
                teams.append(2)
            else:
                teams.append(3)
        return teams

    def read_alive_values(self) -> List[float]:
        values: List[float] = []
        base = self.addr["entity"]
        for i in range(32):
            entity_base = base + 592 * i
            values.append(self.read_float(entity_base + 376, 0.0))
        return values

    def get_targets(self) -> List[Tuple[float, float, float]]:
        targets: List[Tuple[float, float, float]] = []
        players = self.read_players()
        teams = self.players_team()
        alive_values = self.read_alive_values()
        my_team = self.read_int(self.addr["local_team"], 0)

        for i in range(len(players)):
            if teams[i] in (1, 2) and teams[i] != my_team and alive_values[i] != 0:
                targets.append(players[i])
        return targets

    def calc_distance(self, enemy_x: float, enemy_y: float, enemy_z: float) -> float:
        my_x = self.read_float(self.addr["vec3"], 0.0)
        my_y = self.read_float(self.addr["vec3"] + 4, 0.0)
        my_z = self.read_float(self.addr["vec3"] + 8, 0.0)
        delta_x = enemy_x - my_x
        delta_y = enemy_y - my_y
        delta_z = enemy_z - my_z
        return sqrt(delta_x * delta_x + delta_y * delta_y + delta_z * delta_z)

    def calc_scaling(self, w: float, h: float, distance: float, factor: float) -> Optional[Tuple[float, float]]:
        aspect = self.read_float(self.addr["zoom"], 1.0)
        if aspect > 1:
            w *= aspect
            h *= aspect

        try:
            return w / distance * factor, h / distance * factor
        except (ZeroDivisionError, TypeError):
            return None

    def find_target_at_crosshair(
        self,
        targets: List[Tuple[float, float, float]],
        width: int,
        height: int,
        matrix: List[float],
    ) -> bool:
        crosshair_x = width / 2
        crosshair_y = height / 2

        for target in targets:
            screen = self.world_to_screen(target[0], target[1], target[2] + 18, width, height, matrix)
            if not screen:
                continue
            distx = screen[0] - crosshair_x
            disty = screen[1] - crosshair_y
            if abs(distx) < 5 and abs(disty) < 5:
                return True
        return False

    def find_best_target(
        self,
        targets: List[Tuple[float, float, float]],
        width: int,
        height: int,
        matrix: List[float],
    ) -> Tuple[int, Optional[Tuple[float, float]]]:
        nearest_index = -1
        nearest_screen: Optional[Tuple[float, float]] = None
        min_dist = 99999.0

        for i in range(len(targets)):
            screen = self.world_to_screen(targets[i][0], targets[i][1], targets[i][2] + 18, width, height, matrix)
            if not screen:
                continue
            distx = screen[0] - (width / 2)
            disty = screen[1] - (height / 2)
            dist = sqrt(distx * distx + disty * disty)
            if dist < min_dist:
                min_dist = dist
                nearest_index = i
                nearest_screen = screen

        return nearest_index, nearest_screen


class OverlayRenderer(threading.Thread):
    def __init__(
        self,
        memory: CS16Memory,
        controller: "CS16Controller",
        settings: RuntimeSettings,
        stop_event: threading.Event,
    ) -> None:
        super().__init__(daemon=True)
        self.memory = memory
        self.controller = controller
        self.settings = settings
        self.stop_event = stop_event
        self.display = None
        self.window_handle = None
        self.current_resolution = (0, 0)

    def run(self) -> None:
        if not PYGAME_AVAILABLE:
            return

        pygame.init()
        try:
            while not self.stop_event.is_set():
                self._process_events()

                if not (self.controller.is_enabled("esp") or self.controller.is_enabled("crosshair")):
                    if self.display is not None:
                        self.display.fill((0, 0, 0, 0))
                        pygame.display.update()
                    time.sleep(0.05)
                    continue

                width, height = self.memory.read_resolution()
                if width <= 0 or height <= 0:
                    time.sleep(0.05)
                    continue

                self._ensure_overlay_window(width, height)
                self._sync_to_game_window(width, height)

                if self.display is None:
                    time.sleep(0.05)
                    continue

                self.display.fill((0, 0, 0, 0))
                matrix = self.memory.parse_matrix()

                if self.controller.is_enabled("esp") and len(matrix) == 16:
                    self._draw_esp_boxes(width, height, matrix)

                if self.controller.is_enabled("crosshair"):
                    self._draw_crosshair(width, height)

                pygame.display.update()
                time.sleep(self.settings.overlay_refresh)
        finally:
            pygame.quit()

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop_event.set()

    def _ensure_overlay_window(self, width: int, height: int) -> None:
        if self.display is not None and self.current_resolution == (width, height):
            return

        self.display = pygame.display.set_mode((width, height), pygame.NOFRAME | pygame.SRCALPHA)
        self.window_handle = pygame.display.get_wm_info().get("window")
        self.current_resolution = (width, height)

        if self.window_handle:
            ex_style = win32gui.GetWindowLong(self.window_handle, win32con.GWL_EXSTYLE)
            win32gui.SetWindowLong(
                self.window_handle,
                win32con.GWL_EXSTYLE,
                ex_style | win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_NOACTIVATE,
            )
            win32gui.SetLayeredWindowAttributes(
                self.window_handle,
                win32api.RGB(0, 0, 0),
                0,
                win32con.LWA_COLORKEY,
            )

    def _sync_to_game_window(self, width: int, height: int) -> None:
        if not self.window_handle:
            return

        game_window = win32gui.FindWindow(None, "Counter-Strike")
        if game_window == 0:
            return

        left, top, _, _ = win32gui.GetWindowRect(game_window)
        win32gui.SetWindowPos(
            self.window_handle,
            win32con.HWND_TOPMOST,
            left,
            top,
            width,
            height,
            win32con.SWP_NOACTIVATE,
        )

    def _draw_esp_boxes(self, width: int, height: int, matrix: List[float]) -> None:
        targets = self.memory.get_targets()
        for target in targets:
            screen = self.memory.world_to_screen(target[0], target[1], target[2] + 18, width, height, matrix)
            if not screen:
                continue

            dist = self.memory.calc_distance(target[0], target[1], target[2])
            scaling = self.memory.calc_scaling(
                self.settings.esp_box_width,
                self.settings.esp_box_height,
                dist,
                width,
            )
            if not scaling:
                continue

            box_w, box_h = scaling
            left_top_x = screen[0] - box_w / 2
            left_top_y = screen[1] - box_h / 2
            pygame.draw.rect(self.display, (0, 255, 0), pygame.Rect(left_top_x, left_top_y, box_w, box_h), 2)

    def _draw_crosshair(self, width: int, height: int) -> None:
        center_x = width // 2
        center_y = height // 2

        size = max(6, self.settings.crosshair_size)
        half = size // 2
        gap = max(2, size // 6)
        thickness = max(1, self.settings.crosshair_thickness)
        color = (0, 255, 0)

        pygame.draw.line(self.display, color, (center_x, center_y - half), (center_x, center_y - gap), thickness)
        pygame.draw.line(self.display, color, (center_x, center_y + gap), (center_x, center_y + half), thickness)
        pygame.draw.line(self.display, color, (center_x - half, center_y), (center_x - gap, center_y), thickness)
        pygame.draw.line(self.display, color, (center_x + gap, center_y), (center_x + half, center_y), thickness)


class CS16Controller:
    def __init__(self, settings: RuntimeSettings, config_path: Path) -> None:
        self.settings = settings
        self.config_path = config_path
        self.memory = CS16Memory()

        self.feature_lock = threading.Lock()
        self.features = {
            "triggerbotv1": settings.triggerbotv1_enabled,
            "triggerbotv2": settings.triggerbotv2_enabled,
            "bunnyhop": settings.bunnyhop_enabled,
            "ducking": settings.ducking_enabled,
            "aimbot": settings.aimbot_enabled,
            "esp": settings.esp_enabled,
            "crosshair": settings.crosshair_enabled,
        }

        self.toggle_keys = {
            "triggerbotv1": settings.triggerbotv1_key,
            "triggerbotv2": settings.triggerbotv2_key,
            "bunnyhop": settings.bunnyhop_key,
            "ducking": settings.duck_toggle_key,
            "aimbot": settings.aimbot_key,
            "esp": settings.esp_key,
            "crosshair": settings.crosshair_key,
        }

        self.last_toggle_times = {key: 0.0 for key in self.toggle_keys}
        self.last_triggerv1_time = time.time()
        self.triggerbotv1fix = 0
        self.trigger_v2_counter = 0
        self.last_duck_flip = 0.0
        self.duck_flip_state = False
        self.last_status_message = ""

        self.stop_event = threading.Event()
        self.overlay: Optional[OverlayRenderer] = None
        if PYGAME_AVAILABLE:
            self.overlay = OverlayRenderer(self.memory, self, self.settings, self.stop_event)

    def is_enabled(self, feature_name: str) -> bool:
        with self.feature_lock:
            return self.features.get(feature_name, False)

    def toggle_feature(self, feature_name: str) -> None:
        with self.feature_lock:
            self.features[feature_name] = not self.features.get(feature_name, False)

    def safe_is_pressed(self, key_name: str) -> bool:
        if not key_name:
            return False
        try:
            return keyboard.is_pressed(key_name)
        except (RuntimeError, ValueError):
            return False

    def get_status_message(self) -> str:
        feature_values = {
            "triggerbotv1": self.is_enabled("triggerbotv1"),
            "triggerbotv2": self.is_enabled("triggerbotv2"),
            "bunnyhop": self.is_enabled("bunnyhop"),
            "ducking": self.is_enabled("ducking"),
            "aimbot": self.is_enabled("aimbot"),
            "esp": self.is_enabled("esp"),
            "crosshair": self.is_enabled("crosshair"),
        }

        if self.settings.language == "en":
            labels = {True: "Enabled", False: "Disabled"}
        else:
            labels = {True: "Acik", False: "Kapali"}

        return (
            f"TBv1 {labels[feature_values['triggerbotv1']]:<8} | "
            f"TBv2 {labels[feature_values['triggerbotv2']]:<8} | "
            f"BHOP {labels[feature_values['bunnyhop']]:<8} | "
            f"DUCK {labels[feature_values['ducking']]:<8} | "
            f"AIM {labels[feature_values['aimbot']]:<8} | "
            f"ESP {labels[feature_values['esp']]:<8} | "
            f"XHAIR {labels[feature_values['crosshair']]:<8}"
        )

    def update_console(self) -> None:
        current = self.get_status_message()
        if current != self.last_status_message:
            print(f"{current: <130}", end="\r")
            self.last_status_message = current

    def handle_feature_toggles(self, current_time: float) -> None:
        for feature_name, key_name in self.toggle_keys.items():
            if not key_name:
                continue
            if self.safe_is_pressed(key_name) and (current_time - self.last_toggle_times[feature_name]) > self.settings.keybind_delay:
                self.toggle_feature(feature_name)
                self.last_toggle_times[feature_name] = current_time

    def read_crosshair_state(self) -> Tuple[bool, int]:
        local_team = self.memory.read_int(self.memory.addr["local_team"], 0)
        cross_team = self.memory.read_int(self.memory.addr["cross_team"], 0)
        in_cross_value = self.memory.read_uchar(self.memory.addr["in_cross"], 0)

        enemy_in_cross = local_team in (1, 2) and cross_team in (1, 2) and local_team != cross_team
        return enemy_in_cross, in_cross_value

    def run_triggerbot_v1(self, current_time: float, enemy_in_cross: bool) -> None:
        if self.is_enabled("triggerbotv1"):
            if enemy_in_cross and not mouse.is_pressed(button="left"):
                if (current_time - self.last_triggerv1_time) >= self.settings.triggerbotv1_delay:
                    self.memory.tap_attack(0.0005)
                    self.triggerbotv1fix = 0
                    self.last_triggerv1_time = current_time
            elif self.triggerbotv1fix < 1:
                self.memory.write_int(self.memory.addr["force_attack"], 4)
                self.triggerbotv1fix += 2
        else:
            if self.triggerbotv1fix < 2:
                self.memory.write_int(self.memory.addr["force_attack"], 4)
                self.triggerbotv1fix += 1

    def run_triggerbot_v2(self, enemy_in_cross: bool, in_cross_value: int, matrix: List[float]) -> None:
        if not self.is_enabled("triggerbotv2"):
            self.trigger_v2_counter = 0
            return

        width, height = self.memory.read_resolution()
        targets = self.memory.get_targets()

        if self.memory.find_target_at_crosshair(targets, width, height, matrix):
            self.trigger_v2_counter += 1
            if (
                enemy_in_cross
                or in_cross_value == 2
                or self.trigger_v2_counter > self.settings.triggerbotv2_limit
            ) and not mouse.is_pressed(button="left"):
                self.memory.tap_attack(0.03)
                self.trigger_v2_counter = 0
        else:
            self.trigger_v2_counter = 0

    def run_bunnyhop(self) -> None:
        if not self.is_enabled("bunnyhop"):
            return

        if self.safe_is_pressed(self.settings.bunnyhop_jump_key):
            on_ground = self.memory.read_int(self.memory.addr["on_ground"], 0)
            if on_ground == 1:
                self.memory.write_int(self.memory.addr["force_jump"], 5)
            else:
                self.memory.write_int(self.memory.addr["force_jump"], 4)

    def run_ducking(self, current_time: float) -> None:
        if not self.is_enabled("ducking"):
            self.memory.write_int(self.memory.addr["force_duck"], 4)
            return

        if self.safe_is_pressed(self.settings.ducking_hold_key):
            on_ground = self.memory.read_int(self.memory.addr["on_ground"], 0)
            if on_ground == 1:
                if (current_time - self.last_duck_flip) >= self.settings.duck_spam_interval:
                    self.duck_flip_state = not self.duck_flip_state
                    self.memory.write_int(self.memory.addr["force_duck"], 5 if self.duck_flip_state else 4)
                    self.last_duck_flip = current_time
            else:
                self.memory.write_int(self.memory.addr["force_duck"], 4)
        else:
            self.memory.write_int(self.memory.addr["force_duck"], 4)

    def run_aimbot(self, matrix: List[float]) -> None:
        if not self.is_enabled("aimbot"):
            return

        if self.settings.aimbot_hold_key and not self.safe_is_pressed(self.settings.aimbot_hold_key):
            return

        width, height = self.memory.read_resolution()
        targets = self.memory.get_targets()
        if not targets:
            return

        nearest_index, nearest_screen = self.memory.find_best_target(targets, width, height, matrix)
        if nearest_index == -1 or nearest_screen is None:
            return

        dist = self.memory.calc_distance(
            targets[nearest_index][0],
            targets[nearest_index][1],
            targets[nearest_index][2] + 18,
        )
        scaling = self.memory.calc_scaling(
            self.settings.aimbot_fov,
            self.settings.aimbot_fov,
            dist,
            self.settings.aimbot_scalefactor,
        )
        if not scaling:
            return

        recoil_y = self.memory.read_float(self.memory.addr["recoil"], 0.0)
        recoil_x = self.memory.read_float(self.memory.addr["recoil"] + 4, 0.0)

        rec_x = nearest_screen[0] + recoil_x * self.settings.aimbot_rcs
        rec_y = nearest_screen[1] + abs(recoil_y) * self.settings.aimbot_rcs

        distx = (rec_x - (width / 2)) / self.settings.aimbot_smooth
        disty = (rec_y - (height / 2)) / self.settings.aimbot_smooth

        if abs(distx) <= scaling[0] and abs(disty) <= scaling[1]:
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, int(distx), int(disty), 0, 0)

    def print_debug_offsets(self) -> None:
        if not self.settings.debug:
            return

        print("\n(Debug) Module Base Addresses")
        print(f" client.dll: {hex(self.memory.client_module.lpBaseOfDll)}")
        print(f" hw.dll: {hex(self.memory.hw_module.lpBaseOfDll)}")

    def run(self) -> None:
        print(f"(System) Config file: {self.config_path}")
        self.print_debug_offsets()

        if self.overlay:
            self.overlay.start()

        try:
            while not self.stop_event.is_set():
                current_time = time.time()
                self.handle_feature_toggles(current_time)
                self.update_console()

                health = self.memory.read_int(self.memory.addr["local_health"], 0)
                in_chat = self.memory.read_int(self.memory.addr["in_chat"], 0)
                in_menu = self.memory.read_int(self.memory.addr["in_menu"], 0)

                if in_chat == 0 and in_menu == 0 and health > 1:
                    matrix = self.memory.parse_matrix()
                    if len(matrix) == 16:
                        enemy_in_cross, in_cross_value = self.read_crosshair_state()
                        self.run_triggerbot_v1(current_time, enemy_in_cross)
                        self.run_triggerbot_v2(enemy_in_cross, in_cross_value, matrix)
                        self.run_bunnyhop()
                        self.run_ducking(current_time)
                        self.run_aimbot(matrix)
                else:
                    self.memory.write_int(self.memory.addr["force_duck"], 4)

                time.sleep(self.settings.loop_delay)
        except KeyboardInterrupt:
            pass
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        self.stop_event.set()

        if self.overlay and self.overlay.is_alive():
            self.overlay.join(timeout=1.5)

        self.memory.write_int(self.memory.addr["force_attack"], 4)
        self.memory.write_int(self.memory.addr["force_jump"], 4)
        self.memory.write_int(self.memory.addr["force_duck"], 4)
        print("\n(System) Stopped cleanly.")


def main() -> None:
    config_file = select_config_file()
    ensure_config_file(config_file)
    settings = load_runtime_settings(config_file)

    if not PYGAME_AVAILABLE and (settings.esp_enabled or settings.crosshair_enabled):
        print("(Warning) pygame is not installed. ESP/Crosshair overlay will not start.")

    try:
        controller = CS16Controller(settings=settings, config_path=config_file)
    except RuntimeError as err:
        print(f"(Error) {err}")
        return

    controller.run()


if __name__ == "__main__":
    main()
