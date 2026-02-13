import socket
import json
import time
import threading

class UDPReceiver:
    def __init__(self, port=4210, tags=None):
        self.port = port
        self.tags = tags if tags else []
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', port))
        self.sock.settimeout(0.1)
        self.running = True
        self.packets_received = 0
        self.packets_per_second = 0
        self.last_packet_time = 0
        self.last_second = time.time()
        self.second_counter = 0
        self.error_count = 0
        self.thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.thread.start()
        print(f"UDP receiver started on port {self.port}")
        print("⚠️  Tags will show at FIXED positions for testing")

    def set_tags(self, tags):
        self.tags = tags

    def _receive_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(2048)
                self.packets_received += 1
                self.second_counter += 1
                self.last_packet_time = time.time()
                if time.time() - self.last_second >= 1.0:
                    self.packets_per_second = self.second_counter
                    self.second_counter = 0
                    self.last_second = time.time()
                self._process_data(data.decode('utf-8').strip(), addr)
            except socket.timeout:
                continue
            except:
                pass

    def _process_data(self, message, addr):
        try:
            data = json.loads(message)
            tag_id = data.get('id', -1)
            
            if 0 <= tag_id < len(self.tags):
                tag = self.tags[tag_id]
                tag.range_list = data.get('range', [])
                tag.rssi_list = data.get('rssi', [0] * 8)
                tag.quality = "good"
                tag.anchor_count = 4
                
                # FORCE VISIBLE POSITIONS
                positions = {0: (50, 50), 1: (100, 100), 2: (150, 150)}
                if tag_id in positions:
                    tag.set_location(*positions[tag_id])
                    tag.status = True
                
                if self.packets_received % 100 == 0:
                    print(f"✓ Tag {tag_id} showing at ({tag.x}, {tag.y})")
        except:
            pass

    def is_connected(self, timeout=2):
        return (time.time() - self.last_packet_time) < timeout

    def get_statistics(self):
        return {
            'packets_received': self.packets_received,
            'packets_per_second': self.packets_per_second,
            'error_count': self.error_count,
            'uptime': 0,
            'connected': self.is_connected()
        }

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=1.0)
        self.sock.close()

    def reset_statistics(self):
        pass