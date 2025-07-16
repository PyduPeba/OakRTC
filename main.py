from core.memory_reader import MemoryReader
from core.walker import Walker
from core.recorder import AutoRecorder
import time

def main():
    reader = MemoryReader()
    walker = Walker(reader)
    recorder = AutoRecorder(reader)

    print("Gravando caminho... (Ctrl+C para parar)")
    try:
        while True:
            recorder.record_step()
            time.sleep(1)
    except KeyboardInterrupt:
        recorder.save()
        print("Caminho salvo em JSON.")

if __name__ == "__main__":
    main()
