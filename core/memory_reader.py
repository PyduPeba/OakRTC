#core/memory_reader.py
import ctypes as c
import win32gui
import win32process
import os

print("Carregando memory_reader.py...") # Adicione esta linha no topo
from .memory_utils import read_my_wpt

def enable_debug_privilege_pywin32():
    import win32con, win32api, win32security
    hToken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_ALL_ACCESS)
    privilege_id = win32security.LookupPrivilegeValue(None, win32con.SE_DEBUG_NAME)
    win32security.AdjustTokenPrivileges(hToken, False, [(privilege_id, win32con.SE_PRIVILEGE_ENABLED)])

def fin_window_name(base_name: str) -> str:
    matching_titles = []

    def enum_window_callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if base_name in title and "RTC Bot" not in title:
            matching_titles.append(title)

    win32gui.EnumWindows(enum_window_callback, None)
    if not matching_titles:
        raise Exception("Cliente RubinOT não encontrado.")
    return matching_titles[0]

class MemoryReader:
    def __init__(self):
        enable_debug_privilege_pywin32()
        self.client_name = "RubinOT Client"
        self.base_address = None
        self.handle = None
        # self.load_client()

        self.my_x_address = 0x382AAA4
        self.my_y_address = 0x382AAA8
        self.my_z_address = 0x382AAAC

    def load_client(self):
        self.client_name = "RubinOT Client"
        game_name = fin_window_name(self.client_name)

        hwnd = win32gui.FindWindow(None, game_name)
        if hwnd == 0:
            raise Exception("Janela do cliente não encontrada.")

        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        self.handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, pid)
        if not self.handle:
            raise Exception("Handle de processo inválido.")

        modules = win32process.EnumProcessModules(self.handle)
        if not modules:
            raise Exception("Não foi possível enumerar módulos do processo.")

        self.base_address = modules[0]

        # >>> ATUALIZA Addresses.py para o restante do sistema saber <<<    
        import core.Addresses as Addresses
        Addresses.base_address = self.base_address
        Addresses.process_handle = self.handle
        Addresses.my_x_address = self.my_x_address
        Addresses.my_y_address = self.my_y_address
        Addresses.my_z_address = self.my_z_address
        Addresses.my_x_address_offset = None  # Endereços fixos, sem ponteiros
        Addresses.my_y_address_offset = None
        Addresses.my_z_address_offset = None
        Addresses.game = hwnd

    def read_int(self, address):
        buffer = c.create_string_buffer(4)
        bytesRead = c.c_size_t()
        c.windll.kernel32.ReadProcessMemory(self.handle, address, buffer, 4, c.byref(bytesRead))
        return int.from_bytes(buffer.raw, 'little')

    def get_position(self):
        try:
            x, y, z = read_my_wpt()
            if x is None or y is None or z is None:
                print("[DEBUG] Falha ao obter posição atual do personagem.")
            return x, y, z
        except Exception as e:
            print(f"[ERRO] Exceção ao obter posição: {e}")
            return None, None, None
    

