import threading
import time
import requests
import customtkinter as ctk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, NoSuchElementException, StaleElementReferenceException
import re
import phonenumbers
from phonenumbers import geocoder, carrier
import os
import subprocess
from datetime import datetime
import json
from flask import Flask, request
import logging
from werkzeug.serving import make_server

# ================ Telegram Config ================
TELEGRAM_BOT_TOKEN = "5166999201:AAHj6OhVNN5kDlqLWaYXGhw"
TELEGRAM_CHAT_ID = "-10075120"
CHECK_INTERVAL = 1

# ================ URL Configuration ================
TARGET_URL = "http://54.37.83.141/ints/login"

# ================ All Countries with Flags ================
COUNTRIES = {
    'AFGHANISTAN': '🇦🇫', 'ALBANIA': '🇦🇱', 'ALGERIA': '🇩🇿', 'ANDORRA': '🇦🇩', 'ANGOLA': '🇦🇴',
    'ARGENTINA': '🇦🇷', 'ARMENIA': '🇦🇲', 'AUSTRALIA': '🇦🇺', 'AUSTRIA': '🇦🇹', 'AZERBAIJAN': '🇦🇿',
    'BAHAMAS': '🇧🇸', 'BAHRAIN': '🇧🇭', 'BANGLADESH': '🇧🇩', 'BARBADOS': '🇧🇧', 'BELARUS': '🇧🇾',
    'BELGIUM': '🇧🇪', 'BELIZE': '🇧🇿', 'BENIN': '🇧🇯', 'BHUTAN': '🇧🇹', 'BOLIVIA': '🇧🇴',
    'BOSNIA': '🇧🇦', 'BOTSWANA': '🇧🇼', 'BRAZIL': '🇧🇷', 'BRUNEI': '🇧🇳', 'BULGARIA': '🇧🇬',
    'BURKINA': '🇧🇫', 'BURUNDI': '🇧🇮', 'CAMBODIA': '🇰🇭', 'CAMEROON': '🇨🇲', 'CANADA': '🇨🇦',
    'CAPE VERDE': '🇨🇻', 'CHAD': '🇹🇩', 'CHILE': '🇨🇱', 'CHINA': '🇨🇳', 'COLOMBIA': '🇨🇴',
    'COMOROS': '🇰🇲', 'CONGO': '🇨🇩', 'COSTA RICA': '🇨🇷', 'CROATIA': '🇭🇷', 'CUBA': '🇨🇺',
    'CYPRUS': '🇨🇾', 'CZECHIA': '🇨🇿', 'DENMARK': '🇩🇰', 'DJIBOUTI': '🇩🇯', 'DOMINICA': '🇩🇲',
    'DOMINICAN REPUBLIC': '🇩🇴', 'ECUADOR': '🇪🇨', 'EGYPT': '🇪🇬', 'EL SALVADOR': '🇸🇻',
    'EQUATORIAL GUINEA': '🇬🇶', 'ERITREA': '🇪🇷', 'ESTONIA': '🇪🇪', 'ESWATINI': '🇸🇿',
    'ETHIOPIA': '🇪🇹', 'FIJI': '🇫🇯', 'FINLAND': '🇫🇮', 'FRANCE': '🇫🇷', 'GABON': '🇬🇦',
    'GAMBIA': '🇬🇲', 'GEORGIA': '🇬🇪', 'GERMANY': '🇩🇪', 'GHANA': '🇬🇭', 'GREECE': '🇬🇷',
    'GRENADA': '🇬🇩', 'GUATEMALA': '🇬🇹', 'GUINEA': '🇬🇳', 'GUYANA': '🇬🇾', 'HAITI': '🇭🇹',
    'HONDURAS': '🇭🇳', 'HUNGARY': '🇭🇺', 'ICELAND': '🇮🇸', 'INDIA': '🇮🇳', 'INDONESIA': '🇮🇩',
    'IRAN': '🇮🇷', 'IRAQ': '🇮🇶', 'IRELAND': '🇮🇪', 'ISRAEL': '🇮🇱', 'ITALY': '🇮🇹',
    'IVORY COAST': '🇨🇮', 'JAMAICA': '🇯🇲', 'JAPAN': '🇯🇵', 'JORDAN': '🇯🇴', 'KAZAKHSTAN': '🇰🇿',
    'KENYA': '🇰🇪', 'KIRIBATI': '🇰🇮', 'KOREA': '🇰🇷', 'KUWAIT': '🇰🇼', 'KYRGYZSTAN': '🇰🇬',
    'LAOS': '🇱🇦', 'LATVIA': '🇱🇻', 'LEBANON': '🇱🇧', 'LESOTHO': '🇱🇸', 'LIBERIA': '🇱🇷',
    'LIBYA': '🇱🇾', 'LIECHTENSTEIN': '🇱🇮', 'LITHUANIA': '🇱🇹', 'LUXEMBOURG': '🇱🇺',
    'MADAGASCAR': '🇲🇬', 'MALAWI': '🇲🇼', 'MALAYSIA': '🇲🇾', 'MALDIVES': '🇲🇻', 'MALI': '🇲🇱',
    'MALTA': '🇲🇹', 'MARSHALL ISLANDS': '🇲🇭', 'MAURITANIA': '🇲🇷', 'MAURITIUS': '🇲🇺',
    'MEXICO': '🇲🇽', 'MICRONESIA': '🇫🇲', 'MOLDOVA': '🇲🇩', 'MONACO': '🇲🇨', 'MONGOLIA': '🇲🇳',
    'MONTENEGRO': '🇲🇪', 'MOROCCO': '🇲🇦', 'MOZAMBIQUE': '🇲🇿', 'MYANMAR': '🇲🇲',
    'NAMIBIA': '🇳🇦', 'NAURU': '🇳🇷', 'NEPAL': '🇳🇵', 'NETHERLANDS': '🇳🇱', 'NEW ZEALAND': '🇳🇿',
    'NICARAGUA': '🇳🇮', 'NIGER': '🇳🇪', 'NIGERIA': '🇳🇬', 'NORTH MACEDONIA': '🇲🇰',
    'NORWAY': '🇳🇴', 'OMAN': '🇴🇲', 'PAKISTAN': '🇵🇰', 'PALAU': '🇵🇼', 'PANAMA': '🇵🇦',
    'PAPUA NEW GUINEA': '🇵🇬', 'PARAGUAY': '🇵🇾', 'PERU': '🇵🇪', 'PHILIPPINES': '🇵🇭',
    'POLAND': '🇵🇱', 'PORTUGAL': '🇵🇹', 'QATAR': '🇶🇦', 'ROMANIA': '🇷🇴', 'RUSSIA': '🇷🇺',
    'RWANDA': '🇷🇼', 'SAINT LUCIA': '🇱🇨', 'SAMOA': '🇼🇸', 'SAN MARINO': '🇸🇲',
    'SAUDI ARABIA': '🇸🇦', 'SENEGAL': '🇸🇳', 'SERBIA': '🇷🇸', 'SEYCHELLES': '🇸🇨',
    'SIERRA LEONE': '🇸🇱', 'SINGAPORE': '🇸🇬', 'SLOVAKIA': '🇸🇰', 'SLOVENIA': '🇸🇮',
    'SOLOMON ISLANDS': '🇸🇧', 'SOMALIA': '🇸🇴', 'SOUTH AFRICA': '🇿🇦', 'SOUTH SUDAN': '🇸🇸',
    'SPAIN': '🇪🇸', 'SRI LANKA': '🇱🇰', 'SUDAN': '🇸🇩', 'SURINAME': '🇸🇷', 'SWEDEN': '🇸🇪',
    'SWITZERLAND': '🇨🇭', 'SYRIA': '🇸🇾', 'TAIWAN': '🇹🇼', 'TAJIKISTAN': '🇹🇯',
    'TANZANIA': '🇹🇿', 'THAILAND': '🇹🇭', 'TOGO': '🇹🇬', 'TONGA': '🇹🇴',
    'TRINIDAD AND TOBAGO': '🇹🇹', 'TUNISIA': '🇹🇳', 'TURKEY': '🇹🇷', 'TURKMENISTAN': '🇹🇲',
    'TUVALU': '🇹🇻', 'UGANDA': '🇺🇬', 'UKRAINE': '🇺🇦', 'UNITED ARAB EMIRATES': '🇦🇪',
    'UNITED KINGDOM': '🇬🇧', 'UNITED STATES': '🇺🇸', 'URUGUAY': '🇺🇾', 'UZBEKISTAN': '🇺🇿',
    'VANUATU': '🇻🇺', 'VATICAN CITY': '🇻🇦', 'VENEZUELA': '🇻🇪', 'VIETNAM': '🇻🇳',
    'YEMEN': '🇾🇪', 'ZAMBIA': '🇿🇲', 'ZIMBABWE': '🇿🇼'
}

# ================ Service Emojis ================
SERVICE_EMOJIS = {
    'FACEBOOK': '📘', 'INSTAGRAM': '📸', 'WHATSAPP': '💬', 'TELEGRAM': '✈️',
    'DISCORD': '🎮', 'TIKTOK': '🎵', 'SNAPCHAT': '👻', 'TWITTER': '🐦',
    'LINKEDIN': '💼', 'YOUTUBE': '▶️', 'REDDIT': '🤖', 'PINTEREST': '📌',
    'GOOGLE': '🔍', 'MICROSOFT': '💻', 'AMAZON': '🛒', 'PAYPAL': '💰',
    'BINANCE': '📊', 'COINBASE': '🪙', 'BANK': '🏦', 'VERIFY': '✅',
    'VERIFICATION': '✅', 'SECURITY': '🔒', 'AUTH': '🔐', 'OTP': '🔑',
    'OTHER': '📱', 'DEFAULT': '📱'
}

# ================ File Paths ================
BASE_DIR = os.path.expanduser('~/sadi/IrysNode')
SMS_FILE = os.path.join(BASE_DIR, 'all_sms_data.txt')
os.makedirs(BASE_DIR, exist_ok=True)

# ================ Flask App for Telegram Webhook ================
app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# ================ Helpers ================
def get_flag(country_code_alpha2):
    if not country_code_alpha2:
        return ""
    OFFSET = 127397
    return ''.join([chr(ord(char.upper()) + OFFSET) for char in country_code_alpha2])


def escape_markdown_v2(text):
    if not text:
        return ""
    escape_chars = r"\_*\[\]()~`>#+-=|{}.!<>"
    return ''.join(['\\' + c if c in escape_chars else c for c in text])


def mask_phone_number(number):
    if not number or len(number) <= 8:
        return escape_markdown_v2(number) if number else ""
    return escape_markdown_v2(f"{number[:4]}****{number[-4:]}")


# ================ File Operations ============
def save_sms_to_file(otp_code, number):
    """Save SMS data to file - Only Number and OTP"""
    try:
        entry = f"{number} | {otp_code}\n"
        
        with open(SMS_FILE, 'a', encoding='utf-8') as f:
            f.write(entry)
        
        print(f"💾 Saved to file: {number} | {otp_code}")
        return True
    except Exception as e:
        print(f"File Save Error: {e}")
        return False


def get_all_sms_data():
    """Read all SMS data from file"""
    if not os.path.exists(SMS_FILE):
        return []
    
    try:
        with open(SMS_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return [line.strip() for line in lines if line.strip()]
    except Exception as e:
        print(f"File Read Error: {e}")
        return []


def delete_sms_file():
    """Delete the SMS file"""
    try:
        if os.path.exists(SMS_FILE):
            os.remove(SMS_FILE)
            return True
        return False
    except Exception as e:
        print(f"File Delete Error: {e}")
        return False


def format_sms_data_for_list(sms_list):
    """Format SMS data for Telegram list - Only Number | OTP"""
    if not sms_list:
        return "📭 No SMS found in the database."
    
    output = []
    output.append("📊 *SMS Database*")
    output.append(f"📝 Total: {len(sms_list)} SMS")
    output.append("")
    output.append("```")
    output.append("📱 Number | 🔐 OTP")
    output.append("-" * 30)
    
    for line in sms_list:
        output.append(line)
    
    output.append("```")
    
    return "\n".join(output)


# ================ Flask Routes for Telegram Bot ================
@app.route('/', methods=['GET', 'POST'])
def webhook():
    try:
        if request.method == 'POST':
            data = request.get_json()
            if data and 'message' in data:
                chat_id = data['message']['chat']['id']
                text = data['message'].get('text', '')
                
                print(f"📨 Received: {text}")
                
                if text == '/list':
                    sms_list = get_all_sms_data()
                    
                    if sms_list:
                        formatted_list = format_sms_data_for_list(sms_list)
                        
                        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                        data = {
                            "chat_id": chat_id,
                            "text": formatted_list,
                            "parse_mode": "MarkdownV2"
                        }
                        requests.post(url, json=data)
                        
                        if os.path.exists(SMS_FILE):
                            with open(SMS_FILE, 'rb') as f:
                                files = {'document': f}
                                data = {'chat_id': chat_id, 'caption': '📊 Full SMS Database (Number | OTP)'}
                                requests.post(
                                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                                    files=files,
                                    data=data
                                )
                    else:
                        send_message(chat_id, "📭 No SMS found in the database.")
                
                elif text == '/delete':
                    if delete_sms_file():
                        send_message(chat_id, "🗑️ SMS database has been deleted successfully!")
                    else:
                        send_message(chat_id, "❌ No SMS file found to delete.")
                
                elif text == '/help':
                    help_text = """
🤖 *SMS Bot Commands*

/list - Get all SMS data (Number | OTP)
/delete - Delete the SMS database
/help - Show this help message

📊 *File Format:*
`Number | OTP`

📝 *Example:*
`255774660006 | 85835`

💾 *File Location:*
`~/sadi/IrysNode/all_sms_data.txt`
"""
                    send_message(chat_id, help_text)
                
                elif text.startswith('/'):
                    send_message(chat_id, f"❌ Unknown command: {text}\nUse /help for available commands.")
    
    except Exception as e:
        print(f"Webhook Error: {e}")
    
    return "OK", 200


def send_message(chat_id, text):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "MarkdownV2"
        }
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"Send Message Error: {e}")


# ================ Flask Server in Separate Thread ================
class FlaskServer:
    def __init__(self):
        self.server = None
        self.thread = None

    def start(self):
        def run_server():
            self.server = make_server('0.0.0.0', 5000, app)
            self.server.serve_forever()
        
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        print("🤖 Telegram Bot running on port 5000")

    def stop(self):
        if self.server:
            self.server.shutdown()


# ================ Main App ================
class SMSCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📩 SMS Checker - Login First")
        self.root.geometry("550x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title_label = ctk.CTkLabel(root, text="SMS Checker", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=20)

        self.start_button = ctk.CTkButton(root, text="🚀 Open Chrome & Login", command=self.start_browser, width=250)
        self.start_button.pack(pady=10)

        self.check_sms_button = ctk.CTkButton(root, text="📡 Start Checking SMS", command=self.start_monitoring,
                                              state="disabled", width=250)
        self.check_sms_button.pack(pady=10)

        self.stop_button = ctk.CTkButton(root, text="🛑 Stop Monitoring", command=self.stop_monitoring, state="disabled",
                                         width=250)
        self.stop_button.pack(pady=10)

        self.status_label = ctk.CTkLabel(root, text="Status: Not Started", text_color="gray")
        self.status_label.pack(pady=10)

        self.counter_label = ctk.CTkLabel(root, text="📊 SMS Found: 0", text_color="gray")
        self.counter_label.pack(pady=5)

        self.file_label = ctk.CTkLabel(root, text=f"💾 File: {os.path.basename(SMS_FILE)}", text_color="gray")
        self.file_label.pack(pady=5)

        self.debug_label = ctk.CTkLabel(root, text="", text_color="gray", font=("Arial", 10))
        self.debug_label.pack(pady=5)

        self.driver = None
        self.monitoring = False
        self.prev_sms = set()
        self.sms_count = 0
        self.page_loaded = False
        
        # Start Flask Server in separate thread
        self.flask_server = FlaskServer()
        self.flask_server.start()

    def update_status(self, text, color="gray"):
        self.status_label.configure(text=text, text_color=color)

    def update_counter(self):
        self.counter_label.configure(text=f"📊 SMS Found: {self.sms_count}")

    def update_debug(self, text):
        self.debug_label.configure(text=text)

    def find_chrome_binary(self):
        chrome_paths = [
            "/usr/bin/google-chrome-stable",
            "/usr/bin/google-chrome",
            "/opt/google/chrome/google-chrome",
            "/snap/bin/chromium",
            "/usr/bin/chromium-browser",
            "/usr/bin/chromium"
        ]
        
        for path in chrome_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                print(f"Found Chrome at: {path}")
                return path
        
        try:
            result = subprocess.run(['which', 'google-chrome-stable'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip()
                print(f"Found Chrome via which: {path}")
                return path
        except:
            pass
        
        try:
            result = subprocess.run(['which', 'chromium-browser'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                path = result.stdout.strip()
                print(f"Found Chromium via which: {path}")
                return path
        except:
            pass
        
        return None

    # ========== Start Chrome Browser ==========
    def start_browser(self):
        try:
            self.update_status("Status: Launching browser...", "orange")
            options = Options()
            
            chrome_binary = self.find_chrome_binary()
            
            if chrome_binary:
                options.binary_location = chrome_binary
                print(f"✅ Using Chrome: {chrome_binary}")
                self.update_status(f"✅ Using Chrome: {os.path.basename(chrome_binary)}", "green")
            else:
                error_msg = ("Chrome not found!\n\nPlease install Chrome:\nsudo apt install google-chrome-stable")
                messagebox.showerror("Error", error_msg)
                self.update_status("❌ Chrome not found", "red")
                return
            
            options.add_argument("--start-maximized")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            profile_dir = os.path.expanduser('~/sadi/IrysNode/chrome_profile')
            os.makedirs(profile_dir, exist_ok=True)
            options.add_argument(f"user-data-dir={profile_dir}")
            
            if "mnt/c/" in chrome_binary:
                options.add_argument("--disable-software-rasterizer")
                options.add_argument("--disable-features=VizDisplayCompositor")
            
            service = ChromeService()
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)
            
            self.driver.get(TARGET_URL)
            time.sleep(3)
            
            # Block auto-refresh
            self.driver.execute_script("""
                var metaTags = document.querySelectorAll('meta[http-equiv="refresh"]');
                metaTags.forEach(function(tag) { tag.remove(); });
                
                if (window.location && window.location.reload) {
                    window.location.reload = function() {
                        console.log('🔒 Reload blocked');
                        return false;
                    };
                }
                
                var originalSetTimeout = window.setTimeout;
                window.setTimeout = function(func, delay) {
                    try {
                        var funcStr = func.toString();
                        if (delay < 10000 && (funcStr.includes('location') || 
                            funcStr.includes('reload') || 
                            funcStr.includes('refresh'))) {
                            console.log('🔒 Refresh timeout blocked: ' + delay);
                            return null;
                        }
                    } catch(e) {}
                    return originalSetTimeout(func, delay);
                };
                
                var originalSetInterval = window.setInterval;
                window.setInterval = function(func, delay) {
                    try {
                        var funcStr = func.toString();
                        if (delay < 10000 && (funcStr.includes('location') || 
                            funcStr.includes('reload') || 
                            funcStr.includes('refresh'))) {
                            console.log('🔒 Refresh interval blocked: ' + delay);
                            return null;
                        }
                    } catch(e) {}
                    return originalSetInterval(func, delay);
                };
                
                console.log('✅ Refresh mechanisms blocked');
            """)
            
            time.sleep(2)
            
            self.update_status("🔐 Login manually and solve captcha", "orange")
            
            messagebox.showinfo("Login Required", 
                "✅ Login manually in Chrome\n"
                "✅ Complete the captcha\n"
                "✅ Click 'Start Checking SMS' after login\n\n"
                "📱 Telegram Bot is running!\n"
                "Commands: /list, /delete\n"
                "📊 Format: Number | OTP")
            
            self.update_status("✅ Login once, session will be saved", "green")
            self.check_sms_button.configure(state="normal")
            self.start_button.configure(state="disabled")
            self.page_loaded = True

        except Exception as e:
            print(f"Error: {e}")
            messagebox.showerror("Error", f"Could not start browser:\n{str(e)[:200]}")
            self.update_status("❌ Failed to start browser", "red")

    # ========== Start Monitoring ==========
    def start_monitoring(self):
        if not self.driver:
            messagebox.showwarning("Warning", "Browser not started.")
            return

        self.monitoring = True
        self.prev_sms = set()
        self.sms_count = 0
        self.update_counter()
        self.update_status("✅ Monitoring started - Waiting for SMS...", "green")
        self.check_sms_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        
        threading.Thread(target=self.monitor_sms, daemon=True).start()

    # ========== Stop Monitoring ==========
    def stop_monitoring(self):
        self.monitoring = False
        self.update_status("⏹️ Monitoring stopped", "red")
        self.stop_button.configure(state="disabled")
        self.check_sms_button.configure(state="normal")

    # ========== Send Message to Telegram ==========
    def send_to_telegram(self, message):
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": TELEGRAM_CHAT_ID, 
                "text": message, 
                "parse_mode": "MarkdownV2",
                "disable_web_page_preview": True
            }
            r = requests.post(url, json=data, timeout=10)
            if r.status_code != 200:
                print(f"Telegram Error: {r.text}")
                return False
            return True
        except Exception as e:
            print("Telegram Send Error:", e)
            return False

    # ========== Extract OTP from Message ==========
    def extract_otp_from_message(self, message):
        """Extract OTP from message content"""
        if not message:
            return None
        
        patterns = [
            r'(?<!\d)(\d{4,8})(?!\d)',
            r'<#>?\s*(\d{4,8})',
            r'is your (\d{4,8})',
            r'code[:\s]+(\d{4,8})',
            r'otp[:\s]+(\d{4,8})',
            r'pin[:\s]+(\d{4,8})',
            r'verification[:\s]+(\d{4,8})',
            r'security[:\s]+(\d{4,8})',
            r'Facebook code (\d{4,8})',
            r'Discord code (\d{4,8})',
            r'Google code (\d{4,8})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                otp = match.group(1)
                if len(otp) >= 4 and len(otp) <= 8:
                    return otp
        
        numbers = re.findall(r'\b\d{4,8}\b', message)
        for num in numbers:
            if not num.startswith(('01', '02', '03', '04', '05', '06', '07', '08', '09', '1', '2', '3')):
                return num
        
        return None

    # ========== Extract Service from Text ==========
    def extract_service(self, text):
        """Extract service name from text"""
        if not text:
            return "Other"
        
        text_upper = text.upper()
        
        service_keywords = {
            'FACEBOOK': 'FACEBOOK', 'INSTAGRAM': 'INSTAGRAM', 'WHATSAPP': 'WHATSAPP',
            'TELEGRAM': 'TELEGRAM', 'DISCORD': 'DISCORD', 'TIKTOK': 'TIKTOK',
            'SNAPCHAT': 'SNAPCHAT', 'TWITTER': 'TWITTER', 'LINKEDIN': 'LINKEDIN',
            'GOOGLE': 'GOOGLE', 'MICROSOFT': 'MICROSOFT', 'AMAZON': 'AMAZON',
            'PAYPAL': 'PAYPAL', 'BINANCE': 'BINANCE', 'COINBASE': 'COINBASE',
            'VERIFY': 'VERIFY', 'VERIFICATION': 'VERIFICATION', 'SECURITY': 'SECURITY',
            'AUTH': 'AUTH', 'BANK': 'BANK', 'OTP': 'OTP'
        }
        
        for key, value in service_keywords.items():
            if key in text_upper:
                return value
        
        sid_match = re.search(r'^([A-Z\s]+)\s+\d+', text.upper())
        if sid_match:
            service = sid_match.group(1).strip()
            if service not in ['TANZANIA', 'EGYPT', 'BENIN', 'ZAMBIA', 'PHILIPPINES', 'BANGLADESH']:
                return service
        
        return "Other"

    # ========== Extract Phone Number ==========
    def extract_number(self, text):
        """Extract phone number from text"""
        if not text:
            return "Unknown"
        
        patterns = [
            r'\b\d{8,15}\b',
            r'[\+\d\s\-\(\)]{8,15}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                number = match.group(0).strip()
                number = re.sub(r'\s+', '', number)
                if len(number) >= 8:
                    return number
        
        return "Unknown"

    # ========== Get Country from SID ==========
    def get_country_from_sid(self, sid):
        """Get country name and flag from SID"""
        if not sid:
            return "Unknown", ""
        
        for country in COUNTRIES:
            if country in sid.upper():
                return country.title(), COUNTRIES[country]
        
        return "Unknown", ""

    # ========== Create Beautiful Message ==========
    def create_beautiful_message(self, otp_code, number, country_name, country_flag, service, full_text, date):
        """Create a beautifully formatted short message"""
        
        service_emoji = SERVICE_EMOJIS.get(service.upper(), SERVICE_EMOJIS['DEFAULT'])
        
        if not country_flag:
            country_flag = '🌍'
        
        clean_message = full_text[:150] + ("..." if len(full_text) > 150 else "")
        
        formatted = f"""🎯 *{service}* {service_emoji}  •  {country_flag} *{country_name}*

🔐 *OTP:* `{otp_code}`

📱 *Number:* `{mask_phone_number(number)}`
⏰ *Time:* `{date}`

💬 `{clean_message}`

💾 *Saved: {number} | {otp_code}*

━━━━━━━━━━━━━━
🔥 [Join Channel](https://t.me/Earnpoint10)"""
        
        return formatted

    # ========== Monitor SMS ==========
    def monitor_sms(self):
        while self.monitoring:
            try:
                print("🔍 Checking for new SMS...")
                self.root.after(0, self.update_debug, "🔍 Checking for SMS...")
                
                rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")
                print(f"Found {len(rows)} rows in table")
                self.root.after(0, self.update_debug, f"Found {len(rows)} table rows")
                
                for row in rows:
                    try:
                        row_text = row.text.strip()
                        if not row_text or len(row_text) < 10:
                            continue
                        
                        print(f"Processing row: {row_text[:100]}...")
                        
                        columns = row.find_elements(By.TAG_NAME, "td")
                        
                        if len(columns) >= 4:
                            sid = columns[0].text.strip() if len(columns) > 0 else ""
                            paid = columns[1].text.strip() if len(columns) > 1 else ""
                            limit = columns[2].text.strip() if len(columns) > 2 else ""
                            message = columns[3].text.strip() if len(columns) > 3 else ""
                            
                            print(f"   SID: {sid}")
                            print(f"   Message: {message}")
                            
                            otp_code = self.extract_otp_from_message(message)
                            
                            if not otp_code:
                                otp_code = self.extract_otp_from_message(sid)
                            
                            if otp_code:
                                sms_id = f"{sid}_{message}_{hash(row_text)}"
                                
                                if sms_id in self.prev_sms:
                                    print(f"⏭️ SMS already processed")
                                    continue
                                
                                print(f"✅ New OTP Found: {otp_code}")
                                print(f"   Message: {message[:100]}...")
                                
                                self.prev_sms.add(sms_id)
                                self.sms_count += 1
                                
                                service = self.extract_service(f"{sid} {message}")
                                number = self.extract_number(f"{sid} {message}")
                                country_name, country_flag = self.get_country_from_sid(sid)
                                
                                date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                
                                print(f"✅ Sending: {otp_code} | Service: {service} | Country: {country_name}")
                                self.root.after(0, self.update_status, f"📱 New SMS! OTP: {otp_code}", "green")
                                self.root.after(0, self.update_counter)
                                self.root.after(0, self.update_debug, f"✅ OTP: {otp_code} | {service}")
                                
                                # Save to file (Only Number | OTP)
                                save_sms_to_file(otp_code, number)
                                
                                # Send to Telegram
                                formatted_message = self.create_beautiful_message(
                                    otp_code, number, country_name, country_flag, service, f"{sid} {message}", date
                                )
                                
                                if self.send_to_telegram(formatted_message):
                                    print(f"📤 Sent to Telegram: {otp_code}")
                                else:
                                    print(f"❌ Failed to send to Telegram")
                            
                    except StaleElementReferenceException:
                        continue
                    except Exception as e:
                        print(f"Error processing row: {e}")
                
                time.sleep(CHECK_INTERVAL)

            except StaleElementReferenceException:
                print("⚠️ Stale element, retrying...")
                time.sleep(0.5)
                continue
            except Exception as e:
                print(f"❌ Monitor Error: {e}")
                self.root.after(0, self.update_status, f"❗ Error: {str(e)[:50]}... retrying", "red")
                time.sleep(2)

    # ========== Close App ==========
    def on_close(self):
        self.monitoring = False
        if self.driver:
            self.driver.quit()
        if self.flask_server:
            self.flask_server.stop()
        self.root.destroy()


# ================ Launcher ================
if __name__ == "__main__":
    root = ctk.CTk()
    app = SMSCheckerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
