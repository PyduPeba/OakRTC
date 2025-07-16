# test_position.py
from core.memory_utils import read_my_wpt, enable_debug_privilege_pywin32, targets_around_me
from core.memory_reader import MemoryReader

enable_debug_privilege_pywin32()

def main():
    print("Iniciando leitura de posição...")

    # Garanta que as variáveis estejam carregadas
    reader = MemoryReader()
    reader.load_client()

    x, y, z = read_my_wpt()

    if x is not None and y is not None and z is not None:
        print(f"✅ Posição atual do personagem: x={x}, y={y}, z={z}")
    else:
        print("❌ Falha ao obter a posição do personagem.")

if __name__ == "__main__":
    main()
