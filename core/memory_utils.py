# core/memory_utils.py

import win32api
import win32con
import win32security
import ctypes as c
import pymem
import core.Addresses as Addresses

print("Carregando memory_utils.py...")
# Reads value from memory
def read_memory_address(address_read, offsets, option):
    try:
        address = c.c_void_p(Addresses.base_address + address_read + offsets)
        buffer_size = 8
        buffer = c.create_string_buffer(buffer_size)
        result = c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, address, buffer, buffer_size, c.byref(c.c_size_t()))
        if not result:
            return
        match option:
            case 1:
                return c.cast(buffer, c.POINTER(c.c_int)).contents.value
            case 2:
                return c.cast(buffer, c.POINTER(c.c_ulonglong)).contents.value
            case 3:
                return c.cast(buffer, c.POINTER(c.c_double)).contents.value
            case 4:
                return c.cast(buffer, c.POINTER(c.c_short)).contents.value
            case 5:
                try:
                    decoded_value = buffer.value.decode('utf-8')
                except UnicodeDecodeError:
                    decoded_value = "*"
                return decoded_value
            case 7:
                return c.cast(buffer, c.POINTER(c.c_byte)).contents.value
            case _:
                return bytes(buffer)
    except Exception as e:
        print('Memory Exception:', e)

def read_pointer_address(address_read, offsets, option):
    try:
        # 1. Calcula o endereço inicial do primeiro ponteiro (Base do módulo + Offset inicial fixo)
        current_address = Addresses.base_address + address_read
        pointer_size = 8 # <-- Tamanho do ponteiro para 64-bit
        pointer_type = c.c_ulonglong # <-- Tipo do ponteiro para 64-bit unsigned

        # Buffer para ler o valor de um ponteiro
        pointer_buffer = c.create_string_buffer(pointer_size)

        # Debug: Mostrar o endereço inicial do ponteiro
        if Addresses.debug_mode:
            print(f"Pointer Debug: Starting from base 0x{Addresses.base_address:X} + offset 0x{address_read:X} -> Initial pointer address 0x{current_address:X}")


        # Percorre a cadeia de offsets lendo cada ponteiro
        # O último offset na lista é o deslocamento final para o valor desejado
        # A leitura do último ponteiro é feita antes de adicionar o último offset
        if not offsets: # Tratar caso de lista de offsets vazia (não aplicável para multi-nível, mas boa prática)
            print("Pointer Exception: Offset list is empty.")
            return None

        num_pointer_levels = len(offsets) - 1 # Número de ponteiros a seguir = número de offsets - 1
        final_offset = offsets[-1] # O último item na lista de offsets é o offset final para o valor

        # Debug: Mostrar a lista de offsets e o offset final
        if Addresses.debug_mode:
            print(f"Pointer Debug: Offsets to follow ({num_pointer_levels}): {[f'0x{o:X}' for o in offsets[:-1]]}")
            print(f"Pointer Debug: Final offset to value: 0x{final_offset:X}")


        for i in range(num_pointer_levels):
            offset = offsets[i]
            # Lê o valor (que é outro endereço) no current_address
            result = c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, c.c_void_p(current_address), pointer_buffer, pointer_size, c.byref(c.c_size_t()))

            if not result:
                # Debug: Melhorar mensagem de erro para mostrar qual ponteiro falhou
                print(f"Pointer Exception: Failed to read pointer value at 0x{current_address:X} (Offset chain level {i}, offset applied *after* this pointer: 0x{offset:X}) - GetLastError: {c.windll.kernel32.GetLastError()}")
                return None # Falha na leitura de um ponteiro intermediário

            # Interpreta o valor lido como um endereço (ponteiro de 64-bit)
            pointer_value = c.cast(pointer_buffer, c.POINTER(pointer_type)).contents.value
            # Debug: Mostrar o valor do ponteiro lido e o próximo endereço
            if Addresses.debug_mode:
                print(f"Pointer Debug: Level {i} (offset 0x{offset:X}): Read pointer 0x{pointer_value:X} at 0x{current_address:X}. Next address = 0x{pointer_value:X} + 0x{offset:X} = 0x{pointer_value + offset:X}")

            # O endereço para a próxima leitura é o valor do ponteiro + o offset atual da cadeia
            current_address = pointer_value + offset


        # 3. Depois de seguir todos os níveis de ponteiro, current_address é o endereço
        # onde o *último ponteiro* na cadeia (antes do offset final) foi lido.
        # Debug: Mostrar o endereço do último ponteiro lido
        print(f"Pointer Debug: After following pointer chain, address before final offset: 0x{current_address:X}")

        # Agora, lê o valor do *último ponteiro* neste endereço `current_address`
        result = c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, c.c_void_p(current_address), pointer_buffer, pointer_size, c.byref(c.c_size_t()))
        if not result:
             # Debug: Mensagem de erro para a leitura do último ponteiro
             print(f"Pointer Exception: Failed to read final pointer value at 0x{current_address:X} - GetLastError: {c.windll.kernel32.GetLastError()}")
             return None

        # Pega o valor do último ponteiro
        last_pointer_value = c.cast(pointer_buffer, c.POINTER(pointer_type)).contents.value
        # Debug: Mostrar o valor do último ponteiro lido
        if Addresses.debug_mode:
            print(f"Pointer Debug: Final pointer value read at 0x{current_address:X} is 0x{last_pointer_value:X}")


        # Calcula o endereço FINAL do dado = valor do último ponteiro + offset final
        final_data_address = last_pointer_value + final_offset
        # Debug: Mostrar o endereço final calculado
        if Addresses.debug_mode:    
            print(f"Pointer Debug: Calculated final data address = 0x{last_pointer_value:X} + 0x{final_offset:X} = 0x{final_data_address:X}")


        # 4. Agora, lê o valor final no final_data_address com o tamanho correto ('option').

        final_value_size = 0
        read_type = None # Definir read_type aqui
        match option:
            case 1: # c.c_int (int, 4 bytes) - Usado para X, Y (suspeito)
                final_value_size = 4
                read_type = c.c_int
                # Debug: Mostrar o tipo de leitura final
                print(f"Pointer Debug: Final value type: c.c_int (4 bytes)")
            case 2: # c.c_ulonglong (unsigned long long, 8 bytes)
                final_value_size = 8
                read_type = c.c_ulonglong
                print(f"Pointer Debug: Final value type: c.c_ulonglong (8 bytes)")
            case 3: # c.c_double (double, 8 bytes) - Testar para X, Y?
                final_value_size = 8
                read_type = c.c_double
                print(f"Pointer Debug: Final value type: c.c_double (8 bytes)")
            case 4: # c.c_short (short, 2 bytes)
                final_value_size = 2
                read_type = c.c_short
                print(f"Pointer Debug: Final value type: c.c_short (2 bytes)")
            case 5: # string (tamanho variável)
                final_value_size = 64 # Ajuste se necessário
                read_type = c.c_char * final_value_size
                print(f"Pointer Debug: Final value type: string (buffer {final_value_size} bytes)")
            case 7: # c.c_byte (byte, 1 byte) - Usado para Z (suspeito)
                final_value_size = 1
                read_type = c.c_byte
                print(f"Pointer Debug: Final value type: c.c_byte (1 byte)")
            case _:
                print(f"Pointer Exception: Unknown final read option: {option}")
                return None

        if final_value_size <= 0:
             print(f"Pointer Exception: Invalid final read size for option {option}.")
             return None

        # Buffer para ler o valor final
        final_value_buffer = c.create_string_buffer(final_value_size)

        # Lê o valor final no final_data_address
        result = c.windll.kernel32.ReadProcessMemory(Addresses.process_handle, c.c_void_p(final_data_address), final_value_buffer, final_value_size, c.byref(c.c_size_t()))

        if not result:
             # Debug: Mensagem de erro para a leitura final
             print(f"Pointer Exception: Failed to read final value at 0x{final_data_address:X} (Option {option}, Size {final_value_size}) - GetLastError: {c.windll.kernel32.GetLastError()}")
             return None

        # 5. Interpreta o valor final baseado na option
        match option:
            case 5: # String decoding
                try:
                    decoded_value = final_value_buffer.raw.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
                    # Debug: Mostrar a string lida
                    print(f"Pointer Debug: Final value read (string): '{decoded_value}'")
                except Exception as e:
                    print(f"Pointer Exception: Failed to decode string: {e}")
                    decoded_value = "*"
                return decoded_value
            case _: # Outros tipos numéricos
                # Cria um ponteiro para o buffer com o tipo de leitura correto e pega o valor
                value = c.cast(final_value_buffer, c.POINTER(read_type)).contents.value
                # Debug: Mostrar o valor numérico lido
                print(f"Pointer Debug: Final value read (numeric): {value}")
                return value

    except Exception as e:
        # Captura exceções inesperadas
        print('Pointer Exception (Outer Catch):', e)
        return None

def read_targeting_status():
    if Addresses.attack_address_offset is None:
        return read_memory_address(Addresses.attack_address, 0, 2)
    else:
        attack = read_pointer_address(Addresses.attack_address, Addresses.attack_address_offset, 2)
        return attack


def read_my_stats():
    current_hp = read_pointer_address(Addresses.my_stats_address, Addresses.my_hp_offset, 3)
    current_max_hp = read_pointer_address(Addresses.my_stats_address, Addresses.my_hp_max_offset, 3)
    current_mp = read_pointer_address(Addresses.my_stats_address, Addresses.my_mp_offset, 3)
    current_max_mp = read_pointer_address(Addresses.my_stats_address, Addresses.my_mp_max_offset, 3)
    if not current_hp or int(current_hp) == 0:
        current_hp = read_pointer_address(Addresses.my_stats_address, Addresses.my_hp_offset, 1)
        current_max_hp = read_pointer_address(Addresses.my_stats_address, Addresses.my_hp_max_offset, 1)
        current_mp = read_pointer_address(Addresses.my_stats_address, Addresses.my_mp_offset, 1)
        current_max_mp = read_pointer_address(Addresses.my_stats_address, Addresses.my_mp_max_offset, 1)
    return current_hp, current_max_hp, current_mp, current_max_mp

def read_my_wpt():
    # IMPORTANTE: Remova ou comente TODA a parte que usa pymem/MemoryReader aqui.
    # Foque em usar apenas as funções c.windll que você definiu.

    # Verifique se Addresses.base_address foi carregado primeiro
    if Addresses.base_address is None:
        # print("[ERRO] Endereço base não carregado. Não é possível ler a posição.") # Já printado na função de carregamento
        return None, None, None # Retorna None para X, Y, Z se a base não está pronta

    # Verifique se é um setup de ponteiro (checa se my_x_address_offset foi definido)
    if Addresses.my_x_address_offset is None:
        # --- Caso de Endereços Estáticos ---
        # Certifique-se que Addresses.my_x_address, etc., foram definidos com offsets fixos
        # (relativos à base do módulo) nas funções load_game para clientes que usam endereços estáticos.
        # E que a função load_game define my_x_address_offset como None para este caso.
        if Addresses.my_x_address is None:
             print("[ERRO] Configuração de endereço estático incompleta (my_x_address is None).")
             return None, None, None

        # Usa read_memory_address para offsets diretos da base
        # Assumindo X e Y são int (option 1) e Z é byte (option 7) para endereços estáticos também
        x = read_memory_address(Addresses.my_x_address, 0, 1) # address_read = offset, offsets = 0
        y = read_memory_address(Addresses.my_y_address, 0, 1) # address_read = offset, offsets = 0
        z = read_memory_address(Addresses.my_z_address, 0, 7) # address_read = offset, offsets = 0

        return x, y, z
    else:
        # --- Caso de Endereços com Ponteiros Multi-nível ---
        # Certifique-se que Addresses.my_x_address (offset base do ponteiro)
        # e Addresses.my_x_address_offset (lista de offsets) foram definidos
        # nas funções load_game para clientes que usam ponteiros.

        if Addresses.my_x_address is None or Addresses.my_x_address_offset is None:
             print("[ERRO] Configuração de endereço de ponteiro incompleta (my_x_address ou offsets is None).")
             return None, None, None

        # Usa read_pointer_address para seguir a cadeia de ponteiros
        # my_x_address = offset base do ponteiro (ex: 0x019C6628)
        # my_x_address_offset = lista de offsets (ex: [0xBA0, ..., 0x98])
        x = read_pointer_address(Addresses.my_x_address, Addresses.my_x_address_offset, 1) # Option 1 para int (X)
        y = read_pointer_address(Addresses.my_y_address, Addresses.my_y_address_offset, 1) # Option 1 para int (Y)
        z = read_pointer_address(Addresses.my_z_address, Addresses.my_z_address_offset, 7) # <--- Option 7 para byte (Z)

        if Addresses.debug_mode:
            print("[DEBUG-STAND MEMORY] Coleta de posição:")
        print(f"  ↪ X: {x}")
        print(f"  ↪ Y: {y}")
        print(f"  ↪ Z: {z}")

        # Se a leitura falhar, read_pointer_address retorna None, o que é tratado corretamente
        return x, y, z

def read_target_info():
    attack_address = read_memory_address(Addresses.attack_address, 0, 2) - Addresses.base_address
    target_x = read_memory_address(attack_address, Addresses.target_x_offset, 1)
    target_y = read_memory_address(attack_address, Addresses.target_y_offset, 1)
    target_z = read_memory_address(attack_address, Addresses.target_z_offset, 7)
    target_name = read_memory_address(attack_address, Addresses.target_name_offset, 5)
    target_hp = read_memory_address(attack_address, Addresses.target_hp_offset, 7)
    return target_x, target_y, target_z, target_name, target_hp


def targets_around_me(attack_type, names) -> int:
    x, y, z = read_my_wpt()
    targets_around = 0
    if Addresses.target_list:
        for i in range(0, int(read_pointer_address(Addresses.target_count, Addresses.target_count_offset, 2)/25)):
            list_pointer = read_pointer_address(Addresses.target_list, Addresses.target_list_offset, 2)
            target_address = read_memory_address(list_pointer - Addresses.base_address, 0x8*i, 2)
            target_x = read_memory_address(target_address - Addresses.base_address, Addresses.target_x_offset, 1)
            target_y = read_memory_address(target_address - Addresses.base_address, Addresses.target_y_offset, 1)
            target_z = read_memory_address(target_address - Addresses.base_address, Addresses.target_z_offset, 7)
            target_name = read_memory_address(target_address - Addresses.base_address, Addresses.target_name_offset, 5)
            if abs(target_x - x) <= attack_type and abs(target_y - y) <= attack_type and z == target_z and (target_name in names or names == '*'):
                targets_around += 1
        if names == '*':
            targets_around -= 1
        return targets_around
    else:
        return 100


def enable_debug_privilege_pywin32():
    try:
        # Otwórz token bieżącego procesu z odpowiednimi uprawnieniami
        hToken = win32security.OpenProcessToken(
            win32api.GetCurrentProcess(),
            win32con.TOKEN_ADJUST_PRIVILEGES | win32con.TOKEN_QUERY
        )
        # Pobierz identyfikator przywileju SeDebugPrivilege
        privilege_id = win32security.LookupPrivilegeValue(None, win32security.SE_DEBUG_NAME)
        # Włącz przywilej debugowania
        win32security.AdjustTokenPrivileges(hToken, False, [(privilege_id, win32con.SE_PRIVILEGE_ENABLED)])
        return True
    except Exception as e:
        print("Błąd przy włączaniu przywileju debugowania:", e)
        return False


def find_address(base_module, value_to_find, option, size=0x3000):
    for offset in range(base_module+4, base_module + size, 4):
        value = read_memory_address(offset - Addresses.base_address, 0, option)
        if value_to_find == value:
            return offset
    return None