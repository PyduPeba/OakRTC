#Addresses.py
import ctypes as c
import os
import threading
import win32gui
import win32process
import win32con
import win32security

# from Functions.MemoryFunctions import enable_debug_privilege_pywin32, targets_around_me
# from core.memory_utils import enable_debug_privilege_pywin32, targets_around_me

# enable_debug_privilege_pywin32()
# Keystrokes codes
lParam = [
    0X00480001, 0x00500001, 0X004D0001,  # 8, 2, 6
    0X004B0001, 0X00490001, 0X00470001,  # 4, 9, 7
    0X00510001, 0X004F0001  # 3, 1
]
rParam = [
    0X26, 0x28, 0X27,  # 8, 2, 6
    0x25, 0x21, 0x24,  # 4, 9, 7
    0x22, 0x23  # 3, 1
]

# Game HWND
game_hwnd = None

# Locks
walker_Lock = threading.Lock()
debug_mode_Lock = True
# Debug Mode
debug_mode = True # <-- ADICIONE ESTA LINHA AQUI. Mude para True para ver o debug.

# Static addresses
# Character Addresses
my_x_address = None
my_x_address_offset = None
my_y_address = None
my_y_address_offset = None
my_z_address = None
my_z_address_offset = None
my_stats_address = None
my_hp_offset = None
my_hp_max_offset = None
my_mp_offset = None
my_mp_max_offset = None
my_cap_offset = None
backpack_address = None
backpack_offset = None
target_count = None
target_count_offset = None
target_list = None
target_list_offset = None

# Target Addresses
attack_address = None
attack_address_offset = None
target_x_offset = None
target_y_offset = None
target_z_offset = None
target_hp_offset = None
target_name_offset = None

# Other Addresses
enter_address = None

# Game Variables
game_name = None
game = None
base_address = None
process_handle = None
proc_id = None
client_name = None

# Coordinates
screen_x = [0] * 1
screen_y = [0] * 1
battle_x = [0] * 1
battle_y = [0] * 1
screen_width = [0] * 1
screen_height = [0] * 1
coordinates_x = [0] * 12
coordinates_y = [0] * 12

# Other Variables
item_link = ""
item_list = {}

# Rubinot Game
def load_rubinot() -> None:
    global my_x_address, my_y_address, my_z_address, my_x_address_offset, my_y_address_offset, my_z_address_offset, \
        my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, my_cap_offset, \
        backpack_address, backpack_offset, item_link, attack_address_offset, \
        attack_address, target_name_offset, target_x_offset, target_y_offset, target_z_offset, target_hp_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        target_count, target_count_offset, target_list, target_list_offset

    item_link = 'https://wiki.mediviastats.info/File:'
    # Static Addresses
    # Character Addresses
    base_char_pointer = 0x019C6628 # Esta é a base do ponteiro principal dos dados do personagem
    offsets_char_base = [0xBA0, 0x0, 0x28, 0x10, 0x290, 0x100]

    my_x_address = base_char_pointer
    my_x_address_offset = offsets_char_base + [0x98]
    my_y_address = base_char_pointer
    my_y_address_offset = offsets_char_base + [0x9C]
    my_z_address = base_char_pointer
    my_z_address_offset = offsets_char_base + [0xA0]
    my_stats_address = base_char_pointer
    my_hp_offset = [0x78, 0x8, 0x60, 0x8, 0x180, 0x28, 0x78]
    my_hp_max_offset = [0x78, 0x8, 0x60, 0x8, 0x180, 0x28, 0x7C]
    my_mp_offset = [0x78, 0x8, 0x60, 0x8, 0x180, 0x28, 0X80]
    my_mp_max_offset = [0x78, 0x8, 0x60, 0x8, 0x180, 0x28, 0X84]
    backpack_address = None
    backpack_offset = None

    # Target Addresses
    attack_address = 0x019852A8
    attack_address_offset = [0x2C0, 0x28]
    target_name_offset = 0x3C
    target_x_offset = 0x0C
    target_y_offset = 0x10
    target_z_offset = 0x14
    target_hp_offset = 0x54

    # Game 'n' Client names
    client_name = "Tibia - "
    os.makedirs("Images/" + client_name, exist_ok=True)

    # Adicionar a verificação se a janela foi encontrada (recomendado da resposta anterior)
    game_name = fin_window_name(client_name)
    if game_name is None:
        print(f"[ERRO] Janela do jogo com título contendo '{client_name}' não encontrada.")
        print("Por favor, certifique-se de que o cliente do jogo está rodando antes de iniciar o bot.")
        global game, proc_id, process_handle, base_address
        game = None
        proc_id = None
        process_handle = None
        base_address = None # Defina a base como None também
        return # Pare a função de carregamento

    # Loading Addresses (Só executa se game_name não for None)
    game = win32gui.FindWindow(None, game_name)
    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    try:
        # Use win32con.PROCESS_ALL_ACCESS (0x1F0FFF) para garantir permissão total
        # process_handle = c.windll.kernel32.OpenProcess(win32con.PROCESS_ALL_ACCESS, False, proc_id) # Alternativa mais legível
        process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
        if not process_handle:
             print(f"[ERRO] Não foi possível abrir o processo com ID {proc_id}. GetLastError: {c.windll.kernel32.GetLastError()}")
             print("Certifique-se de que o bot tem permissões suficientes (Executar como Administrador).")
             game = None
             proc_id = None
             process_handle = None
             base_address = None
             return
    except Exception as e:
        print(f"[ERRO] Exceção ao tentar abrir o processo: {e}")
        game = None
        proc_id = None
        process_handle = None
        base_address = None
        return
    
    modules = win32process.EnumProcessModulesEx(process_handle, win32process.LIST_MODULES_ALL) # Usar EnumProcessModulesEx para 64-bit
    # Encontre o módulo base correto pelo nome
    exe_name = "client.exe"
    base_address = None
    for mod in modules:
        try:
            # GetModuleFileNameEx pode falhar para alguns módulos, use try-except
            mod_name = win32process.GetModuleFileNameEx(process_handle, mod)
            # Comparar o nome do arquivo (convertido para minúsculas)
            if exe_name in os.path.basename(mod_name).lower():
                 base_address = mod
                 print(f"[DEBUG] Base Address ({exe_name}): 0x{base_address:X}")
                 break # Sai do loop assim que encontrar o módulo base
        except Exception as e:
            # Opcional: printar um aviso se GetModuleFileNameEx falhar para um módulo
            # print(f"Aviso: Falha ao obter nome do módulo {mod}: {e}")
            pass # Ignora módulos que falham ao obter o nome

    if base_address is None:
        print(f"[ERRO] Não foi possível encontrar o módulo base '{exe_name}'.")
        # Lidar com este erro (sair, etc.)
        game = None
        proc_id = None
        process_handle = None
        # base_address já é None
        return


# Medivia Game
def load_medivia() -> None:
    global my_x_address, my_y_address, my_z_address, \
        my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, my_cap_offset, \
        backpack_address, backpack_offset, item_link, \
        attack_address, target_name_offset, target_x_offset, target_y_offset, target_z_offset, target_hp_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        target_count, target_count_offset, target_list, target_list_offset

    item_link = 'https://wiki.mediviastats.info/File:'
    # Static Addresses
    # Character Addresses
    my_x_address = 0XBEE560
    my_y_address = 0XBEE564
    my_z_address = 0XBEE568
    my_stats_address = 0x00BED4E0
    my_hp_offset = [0X558]
    my_hp_max_offset = [0X560]
    my_cap_offset = [0x568]
    my_mp_offset = [0x590]
    my_mp_max_offset = [0x598]
    backpack_address = 0x00BED640
    backpack_offset = [0xDF8, 0X40, 0X68, 0X10, 0X20]

    # Target Addresses
    attack_address = 0xBED4E8
    target_name_offset = 0xA8
    target_x_offset = 0x38
    target_y_offset = 0x3C
    target_z_offset = 0x40
    target_hp_offset = 0xE8

    target_list = 0x00BEDA98
    target_list_offset = [0x0, 0xC8]

    target_count = None
    target_count_offset = None

    # Game 'n' Client names
    client_name = "Medivia"
    os.makedirs("Images/" + client_name, exist_ok=True)
    game_name = fin_window_name(client_name)

    # Loading Addresses
    game = win32gui.FindWindow(None, game_name)
    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    modules = win32process.EnumProcessModules(process_handle)
    base_address = modules[0]


# TibiaScape Game
def load_tibiaScape() -> None:
    global my_x_address, my_y_address, my_z_address, \
        my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, \
        backpack_address, backpack_offset, item_link, \
        attack_address, target_name_offset, target_x_offset, target_y_offset, target_z_offset, target_hp_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        target_count, target_count_offset, target_list, target_list_offset

    item_link = 'https://www.tibia-wiki.net/wiki/Plik:'
    # Static Addresses
    # Character Addresses
    my_x_address = 0xD22490
    my_y_address = 0XD22494
    my_z_address = 0XD22498
    my_stats_address = 0x00D21D90
    my_hp_offset = [0X6C0]
    my_hp_max_offset = [0X6C8]
    my_mp_offset = [0x6F8]
    my_mp_max_offset = [0x700]
    backpack_address = 0x00D2AE78
    backpack_offset = [0X240, 0X30, 0X20, 0XA8, 0XA8, 0XA8, 0X130]

    # Target Addresses
    attack_address = 0XD21DA0
    target_name_offset = 0x48
    target_x_offset = 0x20
    target_y_offset = 0x24
    target_z_offset = 0x28
    target_hp_offset = 0x68

    # Game 'n' Client names
    client_name = "TibiaScape"
    os.makedirs("Images/" + client_name, exist_ok=True)
    game_name = fin_window_name(client_name)
    # Loading Addresses
    game = win32gui.FindWindow(None, game_name)
    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    modules = win32process.EnumProcessModules(process_handle)
    base_address = modules[0]


def load_miracle() -> None:
    global my_x_address, my_y_address, my_z_address, \
        my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, \
        backpack_address, backpack_offset, item_link, \
        attack_address, target_name_offset, target_x_offset, target_y_offset, target_z_offset, target_hp_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        target_count, target_count_offset, target_list, target_list_offset

    item_link = 'https://www.tibia-wiki.net/wiki/Plik:'
    # Static Addresses
    # Character Addresses
    my_x_address = 0xA316EC
    my_y_address = 0xA316F0
    my_z_address = 0xA316F4
    my_stats_address = 0x00A31310
    my_hp_offset = [0x4A8]
    my_hp_max_offset = [0x4B0]
    my_mp_offset = [0X4E0]
    my_mp_max_offset = [0X4E8]
    backpack_address = None
    backpack_offset = None

    # Target Addresses
    attack_address = 0xA31314
    target_name_offset = 0x30
    target_x_offset = 0xC
    target_y_offset = 0x10
    target_z_offset = 0x14
    target_hp_offset = 0x48

    # Game 'n' Client names
    client_name = "Miracle 7.4"
    os.makedirs("Images/" + client_name, exist_ok=True)
    game_name = fin_window_name(client_name)
    # Loading Addresses
    game = win32gui.FindWindow(None, game_name)
    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    modules = win32process.EnumProcessModules(process_handle)
    base_address = modules[0]


def load_dura() -> None:
    global my_x_address, my_y_address, my_z_address, \
        my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, \
        backpack_address, backpack_offset, item_link, \
        attack_address, target_name_offset, target_x_offset, target_y_offset, target_z_offset, target_hp_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        target_count, target_count_offset, target_list, target_list_offset

    item_link = 'https://www.tibia-wiki.net/wiki/Plik:'
    # Static Addresses
    # Character Addresses
    my_x_address = 0xBDD3CC
    my_y_address = 0xBDD3D0
    my_z_address = 0xBDD3D4
    my_stats_address = 0x00BDD0F4
    my_hp_offset = [0x4A0]
    my_hp_max_offset = [0x4A8]
    my_mp_offset = [0X4D8]
    my_mp_max_offset = [0X4E0]
    backpack_address = 0x00D2AE78
    backpack_offset = [0X240, 0X30, 0X20, 0XA8, 0XA8, 0XA8, 0X130]

    # Target Addresses
    attack_address = 0xBDD0F8
    target_name_offset = 0x30
    target_x_offset = 0xC
    target_y_offset = 0x10
    target_z_offset = 0x14
    target_hp_offset = 0x48

    # Game 'n' Client names
    client_name = "Dura"
    os.makedirs("Images/" + client_name, exist_ok=True)
    game_name = fin_window_name(client_name)
    # Loading Addresses
    game = win32gui.FindWindow(None, game_name)
    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    modules = win32process.EnumProcessModules(process_handle)
    base_address = modules[0]


def load_treasura() -> None:
    global my_x_address, my_y_address, my_z_address, \
        my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, \
        backpack_address, backpack_offset, item_link, \
        attack_address, target_name_offset, target_x_offset, target_y_offset, target_z_offset, target_hp_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        target_count, target_count_offset, target_list, target_list_offset

    item_link = 'https://www.tibia-wiki.net/wiki/Plik:'
    # Static Addresses
    # Character Addresses
    my_x_address = 0xB8547C
    my_y_address = 0xB85480
    my_z_address = 0xB85484
    my_stats_address = 0x00B85170
    my_hp_offset = [0x470]
    my_hp_max_offset = [0x478]
    my_mp_offset = [0X4A8]
    my_mp_max_offset = [0X4B0]
    backpack_address = 0x00D2AE78
    backpack_offset = [0X240, 0X30, 0X20, 0XA8, 0XA8, 0XA8, 0X130]

    # Target Addresses
    attack_address = 0xB85174
    target_name_offset = 0x30
    target_x_offset = 0xC
    target_y_offset = 0x10
    target_z_offset = 0x14
    target_hp_offset = 0x48

    # Game 'n' Client names
    client_name = "Treasura"
    os.makedirs("Images/" + client_name, exist_ok=True)
    game_name = fin_window_name(client_name)
    # Loading Addresses
    game = win32gui.FindWindow(None, game_name)
    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    modules = win32process.EnumProcessModules(process_handle)
    base_address = modules[0]


# Giveria Game
def load_giveria() -> None:
    global my_x_address, my_y_address, my_z_address, my_x_address_offset, my_y_address_offset, my_z_address_offset, \
        my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, \
        backpack_address, backpack_offset, item_link, \
        attack_address, attack_address_offset, target_name_offset, target_x_offset, target_y_offset, target_z_offset, target_hp_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        target_count, target_count_offset, target_list, target_list_offset

    item_link = 'https://www.tibia-wiki.net/wiki/Plik:'
    # Static Addresses
    # Character Addresses
    my_x_address = 0x00DF6B94
    my_x_address_offset = [0x250, 0x24]
    my_y_address = 0x00DF6B94
    my_y_address_offset = [0x250, 0x28]
    my_z_address = 0x00DF6B94
    my_z_address_offset = [0x250, 0x2C]
    my_stats_address = 0x00DF6B94
    my_hp_offset = [0x3C, 0X4, 0X24, 0X0, 0XB8, 0X4, 0X3C]
    my_hp_max_offset = [0x3C, 0X4, 0X24, 0X0, 0XB8, 0X4, 0X40]
    my_mp_offset = [0x3C, 0X4, 0X24, 0X0, 0XB8, 0X4, 0X44]
    my_mp_max_offset = [0x3C, 0X4, 0X24, 0X0, 0XB8, 0X4, 0X48]
    backpack_address = 0x00D2AE78
    backpack_offset = [0X240, 0X30, 0X20, 0XA8, 0XA8, 0XA8, 0X130]

    # Target Addresses
    attack_address = 0x00DF6B94
    attack_address_offset = [0x130, 0x1C]
    target_name_offset = 0x30
    target_x_offset = 0xC
    target_y_offset = 0x10
    target_z_offset = 0x14
    target_hp_offset = 0x48

    # Game 'n' Client names
    client_name = "Tibia"
    os.makedirs("Images/" + client_name, exist_ok=True)
    game_name = fin_window_name(client_name)
    # Loading Addresses
    game = win32gui.FindWindow(None, game_name)
    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    modules = win32process.EnumProcessModules(process_handle)
    base_address = modules[0]


# Medivia Game
def load_tibiara() -> None:
    global my_x_address, my_y_address, my_z_address, \
        my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, my_cap_offset, \
        backpack_address, backpack_offset, item_link, \
        attack_address, target_name_offset, target_x_offset, target_y_offset, target_z_offset, target_hp_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        target_count, target_count_offset, target_list, target_list_offset

    item_link = 'https://wiki.mediviastats.info/File:'
    # Static Addresses
    # Character Addresses
    my_x_address = 0x382AAA4
    my_y_address = 0x382AAA8
    my_z_address = 0x382AAAC
    my_stats_address = 0x0382A308
    my_hp_offset = [0x788]
    my_hp_max_offset = [0x790]
    my_cap_offset = [0x798]
    my_mp_offset = [0x7C8]
    my_mp_max_offset = [0x7D0]
    backpack_address = None
    backpack_offset = None

    # Target Addresses
    attack_address = 0x382A30C
    target_name_offset = 0x5C
    target_x_offset = 0x10
    target_y_offset = 0x18
    target_z_offset = 0x24
    target_hp_offset = 0x38

    # Game 'n' Client names
    client_name = "RubinOT Client"
    os.makedirs("Images/" + client_name, exist_ok=True)
    game_name = fin_window_name(client_name)

    # Loading Addresses
    game = win32gui.FindWindow(None, game_name)
    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    modules = win32process.EnumProcessModules(process_handle)
    base_address = modules[0]


def load_igla() -> None:
    global my_x_address, my_y_address, my_z_address, my_x_address_offset, my_y_address_offset, my_z_address_offset, \
        my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, my_cap_offset, \
        backpack_address, backpack_offset, item_link, attack_address_offset, \
        attack_address, target_name_offset, target_x_offset, target_y_offset, target_z_offset, target_hp_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        target_count, target_count_offset, target_list, target_list_offset

    item_link = 'https://wiki.mediviastats.info/File:'
    # Static Addresses
    # Character Addresses
    my_x_address = 0x019852A8
    my_x_address_offset = [0x290, 0x100, 0x98]
    my_y_address = 0x019852A8
    my_y_address_offset = [0x290, 0x100, 0x9C]
    my_z_address = 0x019852A8
    my_z_address_offset = [0x290, 0x100, 0xA0]
    my_stats_address = 0x019852A8
    my_hp_offset = [0x78, 0x8, 0x60, 0x8, 0x180, 0x28, 0x78]
    my_hp_max_offset = [0x78, 0x8, 0x60, 0x8, 0x180, 0x28, 0x7C]
    my_mp_offset = [0x78, 0x8, 0x60, 0x8, 0x180, 0x28, 0X80]
    my_mp_max_offset = [0x78, 0x8, 0x60, 0x8, 0x180, 0x28, 0X84]
    backpack_address = None
    backpack_offset = None

    # Target Addresses
    attack_address = 0x019852A8
    attack_address_offset = [0x2C0, 0x28]
    target_name_offset = 0x3C
    target_x_offset = 0x0C
    target_y_offset = 0x10
    target_z_offset = 0x14
    target_hp_offset = 0x54

    # Game 'n' Client names
    client_name = "Tibia - "
    os.makedirs("Images/" + client_name, exist_ok=True)
    game_name = fin_window_name(client_name)

    # Loading Addresses
    game = win32gui.FindWindow(None, game_name)
    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    modules = win32process.EnumProcessModules(process_handle)
    base_address = modules[0]




# Medivia Game
def load_error() -> None:
    global my_x_address, my_y_address, my_z_address, \
        my_stats_address, my_hp_offset, my_hp_max_offset, my_mp_offset, my_mp_max_offset, my_cap_offset, \
        backpack_address, backpack_offset, item_link, \
        attack_address, target_name_offset, target_x_offset, target_y_offset, target_z_offset, target_hp_offset, \
        client_name, base_address, game, proc_id, process_handle, game_name, \
        target_count, target_count_offset, target_list, target_list_offset

    item_link = 'https://wiki.mediviastats.info/File:'
    # Static Addresses
    # Character Addresses
    my_x_address = 0XB5BF3C
    my_y_address = 0XB5BF40
    my_z_address = 0XB5BF44
    my_stats_address = 0x00B5BC60
    my_hp_offset = [0X470]
    my_hp_max_offset = [0X478]
    my_cap_offset = [0x4A8]
    my_mp_offset = [0x4A8]
    my_mp_max_offset = [0x4B0]
    backpack_address = 0x00BED640
    backpack_offset = [0xDF8, 0X40, 0X68, 0X10, 0X20]

    # Target Addresses
    attack_address = 0xB5BC64
    target_name_offset = 0x30
    target_x_offset = 0xC
    target_y_offset = 0x10
    target_z_offset = 0x14
    target_hp_offset = 0xE8

    target_list = 0x00BEDA98
    target_list_offset = [0x0, 0xC8]

    target_count = None
    target_count_offset = None

    # Game 'n' Client names
    client_name = "ERROR"
    os.makedirs("Images/" + client_name, exist_ok=True)
    game_name = fin_window_name(client_name)

    # Loading Addresses
    game = win32gui.FindWindow(None, game_name)
    proc_id = win32process.GetWindowThreadProcessId(game)
    proc_id = proc_id[1]
    process_handle = c.windll.kernel32.OpenProcess(0x1F0FFF, False, proc_id)
    modules = win32process.EnumProcessModules(process_handle)
    base_address = modules[0]


def fin_window_name(name) -> str:
    matching_titles = []

    def enum_window_callback(hwnd, _):
        window_text = win32gui.GetWindowText(hwnd)
        if name in window_text and "EasyBot" not in window_text:
            matching_titles.append(window_text)

    win32gui.EnumWindows(enum_window_callback, None)
    return matching_titles[0]


# User Interface
dark_theme = """
    QWidget {
        background-color: #2e2e2e;
        color: #ffffff;
    }

    QMainWindow {
        background-color: #2e2e2e;
    }

    QPushButton {
        background-color: #444444;
        border: 1px solid #5e5e5e;
        color: #ffffff;
        padding: 5px;
        border-radius: 5px;
    }

    QPushButton:hover {
        background-color: #555555;
    }

    QPushButton:pressed {
        background-color: #666666;
    }

    QLineEdit, QTextEdit {
        background-color: #3e3e3e;
        border: 1px solid #5e5e5e;
        color: #ffffff;
    }

    QLabel {
        color: #ffffff;
    }

    QMenuBar {
        background-color: #3e3e3e;
    }

    QMenuBar::item {
        background-color: #3e3e3e;
        color: #ffffff;
    }

    QMenuBar::item:selected {
        background-color: #555555;
    }

    QMenu {
        background-color: #3e3e3e;
        color: #ffffff;
    }

    QMenu::item:selected {
        background-color: #555555;
    }

    QScrollBar:vertical {
        background-color: #2e2e2e;
        width: 12px;
    }

    QScrollBar::handle:vertical {
        background-color: #666666;
        min-height: 20px;
        border-radius: 5px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #888888;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background-color: #2e2e2e;
    }
"""