import psutil
import time

def monitor_system():
    while True:
        cpu = psutil.cpu_percent()
        mem = psutil.virtual_memory().percent
        print(f"CPU Usage: {cpu}%, Memory Usage: {mem}%")
        time.sleep(10)

if __name__ == "__main__":
    monitor_system()
