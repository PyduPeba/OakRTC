# test_teclado.py
from core.memory_reader import enable_debug_privilege_pywin32, MemoryReader
from core.input_sender import send_arrow_key

def main():
    print("[Teste] Ativando permissões de debug...")
    enable_debug_privilege_pywin32()

    reader = MemoryReader()
    reader.load_client()

    from core.Addresses import game
    if not game:
        print("[Erro] game HWND ainda é None mesmo após load_client()!")
        return

    print(f"[Teste] HWND do jogo: {game}")
    print("[Teste] Enviando tecla UP para o cliente RubinOT via lParam/rParam...")
    send_arrow_key('up')
    print("[Teste] Tecla enviada!")

if __name__ == "__main__":
    main()
