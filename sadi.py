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

# ================ Telegram Config ================
TELEGRAM_BOT_TOKEN = "5166999201:AAHj51-M28JBWVN6OhVNN5kDlqLWaYXGhw"
TELEGRAM_CHAT_ID = "-10042425120"
CHECK_INTERVAL = 1

# ================ URL Configuration ================
TARGET_URL = "https://www.ivasms.com/portal/live/my_sms"

# ================ All Countries with Flags ================
COUNTRIES = {
    'TANZANIA': '🇹🇿', 'BANGLADESH': '🇧🇩', 'INDIA': '🇮🇳', 'PAKISTAN': '🇵🇰',
    'NIGERIA': '🇳🇬', 'GHANA': '🇬🇭', 'KENYA': '🇰🇪', 'UGANDA': '🇺🇬',
    'SOUTH AFRICA': '🇿🇦', 'EGYPT': '🇪🇬', 'ZAMBIA': '🇿🇲', 'BENIN': '🇧🇯',
    'PHILIPPINES': '🇵🇭', 'CAMBODIA': '🇰🇭', 'VIETNAM': '🇻🇳', 'INDONESIA': '🇮🇩',
    'MALAYSIA': '🇲🇾', 'SINGAPORE': '🇸🇬', 'TAIWAN': '🇹🇼', 'CHINA': '🇨🇳',
    'JAPAN': '🇯🇵', 'KOREA': '🇰🇷', 'USA': '🇺🇸', 'UK': '🇬🇧',
    'CANADA': '🇨🇦', 'AUSTRALIA': '🇦🇺', 'NEW ZEALAND': '🇳🇿', 'FRANCE': '🇫🇷',
    'GERMANY': '🇩🇪', 'ITALY': '🇮🇹', 'SPAIN': '🇪🇸', 'PORTUGAL': '🇵🇹',
    'NETHERLANDS': '🇳🇱', 'BELGIUM': '🇧🇪', 'SWITZERLAND': '🇨🇭', 'AUSTRIA': '🇦🇹',
    'SWEDEN': '🇸🇪', 'NORWAY': '🇳🇴', 'DENMARK': '🇩🇰', 'FINLAND': '🇫🇮',
    'RUSSIA': '🇷🇺', 'UKRAINE': '🇺🇦', 'POLAND': '🇵🇱', 'TURKEY': '🇹🇷'
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

# ================ Helpers ================
def get_flag(country_code_alpha2):
    if not country_code_alpha2:
        return ""
    OFFSET = 127397
    return ''.join([chr(ord(char.upper()) + OFFSET) for char in country_code_alpha2])


def mask_phone_number(number):
    if not number or len(number) <= 8:
        return number if number else ""
    return f"{number[:4]}****{number[-4:]}"


# ================ File Operations ================
def save_sms_to_file(otp_code, number):
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
    try:
        if os.path.exists(SMS_FILE):
            os.remove(SMS_FILE)
            return True
        return False
    except Exception as e:
        print(f"File Delete Error: {e}")
        return False


# ================ Telegram Functions ================
def send_telegram_message(text):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "disable_web_page_preview": True
        }
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print(f"✅ Telegram sent successfully!")
            return True
        else:
            print(f"❌ Telegram error: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Telegram send error: {e}")
        return False


def send_telegram_file(file_path):
    """Send file to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
        with open(file_path, 'rb') as f:
            files = {'document': f}
            data = {'chat_id': TELEGRAM_CHAT_ID, 'caption': '📊 Full SMS Database (Number | OTP)'}
            response = requests.post(url, files=files, data=data, timeout=30)
            return response.status_code == 200
    except Exception as e:
        print(f"❌ File send error: {e}")
        return False


# ================ Telegram Bot ================
class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
        self.last_update_id = 0
        self.running = True
        
    def get_updates(self, offset=None):
        try:
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            params = {'timeout': 10, 'allowed_updates': ['message']}
            if offset:
                params['offset'] = offset
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 200:
                return r.json().get('result', [])
            return []
        except Exception as e:
            print(f"Get Updates Error: {e}")
            return []
    
    def process_updates(self):
        while self.running:
            try:
                updates = self.get_updates(self.last_update_id + 1 if self.last_update_id else None)
                
                for update in updates:
                    self.last_update_id = update.get('update_id', 0)
                    
                    if 'message' in update:
                        message = update['message']
                        chat_id = message.get('chat', {}).get('id')
                        text = message.get('text', '')
                        
                        if chat_id != self.chat_id:
                            continue
                        
                        print(f"📨 Received: {text}")
                        
                        if text == '/list':
                            sms_list = get_all_sms_data()
                            if sms_list:
                                output = "📊 SMS Database\n"
                                output += f"📝 Total: {len(sms_list)} SMS\n\n"
                                output += "Number | OTP\n"
                                output += "-" * 30 + "\n"
                                for line in sms_list[:50]:
                                    output += line + "\n"
                                if len(sms_list) > 50:
                                    output += f"\n... and {len(sms_list) - 50} more"
                                
                                send_telegram_message(output)
                                
                                if os.path.exists(SMS_FILE):
                                    send_telegram_file(SMS_FILE)
                            else:
                                send_telegram_message("📭 No SMS found in the database.")
                        
                        elif text == '/delete':
                            if delete_sms_file():
                                send_telegram_message("🗑️ SMS database deleted successfully!")
                            else:
                                send_telegram_message("❌ No SMS file found to delete.")
                        
                        elif text == '/help':
                            help_text = """🤖 SMS Bot Commands

/list - Get all SMS data (Number | OTP)
/delete - Delete the SMS database
/help - Show this help message

File Format: Number | OTP
Example: 255774660006 | 85835

File Location: ~/sadi/IrysNode/all_sms_data.txt"""
                            send_telegram_message(help_text)
                        
                        elif text.startswith('/'):
                            send_telegram_message(f"❌ Unknown command: {text}\nUse /help for available commands.")
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Process Updates Error: {e}")
                time.sleep(5)
    
    def start(self):
        def run():
            print("🤖 Telegram Bot started")
            self.process_updates()
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def stop(self):
        self.running = False


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
        
        # Start Telegram Bot
        self.bot = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.bot.start()
        time.sleep(1)
        send_telegram_message("🤖 SMS Bot Started!\n\nBot is running.\nUse /help for commands.")

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
                "📱 Bot will send OTPs to Telegram\n"
                "📊 Format: Number | OTP\n\n"
                "Commands: /list, /delete, /help")
            
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

    # ========== Extract OTP from Text ==========
    def extract_otp_from_text(self, text):
        """Extract OTP from any text"""
        if not text:
            return None
        
        # First, remove "COUNTRY NUMBER" patterns like "TANZANIA 9486"
        cleaned_text = re.sub(r'\b[A-Z]+\s+\d{4,8}\b', '', text)
        
        # Search for OTP patterns
        patterns = [
            r'<#>?\s*(\d{4,8})',
            r'is your (\d{4,8})',
            r'code[:\s]+(\d{4,8})',
            r'otp[:\s]+(\d{4,8})',
            r'verification[:\s]+(\d{4,8})',
            r'security[:\s]+(\d{4,8})',
            r'Facebook code (\d{4,8})',
            r'Discord code (\d{4,8})',
            r'Google code (\d{4,8})',
            r'(?<!\d)(\d{4,8})(?!\d)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, cleaned_text, re.IGNORECASE)
            if match:
                otp = match.group(1)
                if len(otp) >= 4 and len(otp) <= 8:
                    # Make sure this is not a phone number
                    if not re.match(r'^2557\d{6}$', otp) and not re.match(r'^01\d{8,10}$', otp):
                        return otp
        
        return None

    # ========== Extract Service from Text ==========
    def extract_service(self, text):
        if not text:
            return "Other"
        
        text_upper = text.upper()
        
        service_keywords = {
            'FACEBOOK': 'FACEBOOK', 'INSTAGRAM': 'INSTAGRAM', 'WHATSAPP': 'WHATSAPP',
            'TELEGRAM': 'TELEGRAM', 'DISCORD': 'DISCORD', 'TIKTOK': 'TIKTOK',
            'SNAPCHAT': 'SNAPCHAT', 'TWITTER': 'TWITTER', 'LINKEDIN': 'LINKEDIN',
            'GOOGLE': 'GOOGLE', 'MICROSOFT': 'MICROSOFT', 'AMAZON': 'AMAZON',
            'PAYPAL': 'PAYPAL', 'BINANCE': 'BINANCE', 'COINBASE': 'COINBASE',
            'VERIFY': 'VERIFY', 'VERIFICATION': 'VERIFICATION', 'SECURITY': 'SECURITY'
        }
        
        for key, value in service_keywords.items():
            if key in text_upper:
                return value
        
        return "Other"

    # ========== Extract Phone Number ==========
    def extract_number(self, text):
        """Extract phone number from text"""
        if not text:
            return "Unknown"
        
        # Look for Tanzania phone number format
        tz_pattern = r'\b2557\d{6}\b'
        match = re.search(tz_pattern, text)
        if match:
            return match.group(0)
        
        # General phone number patterns
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

    # ========== Get Country from Text ==========
    def get_country_from_text(self, text):
        if not text:
            return "Unknown", ""
        
        for country in COUNTRIES:
            if country in text.upper():
                return country.title(), COUNTRIES[country]
        
        return "Unknown", ""

    # ========== Create Beautiful Message ==========
    def create_beautiful_message(self, otp_code, number, country_name, country_flag, service, full_text, date):
        service_emoji = SERVICE_EMOJIS.get(service.upper(), '📱')
        
        if not country_flag:
            country_flag = '🌍'
        
        clean_text = full_text[:150] + ("..." if len(full_text) > 150 else "")
        
        formatted = f"""🎯 {service} {service_emoji}  •  {country_flag} {country_name}

🔐 OTP: {otp_code}

📱 Number: {mask_phone_number(number)}
⏰ Time: {date}

💬 {clean_text}

💾 Saved: {number} | {otp_code}

━━━━━━━━━━━━━━
🔥 Join Channel: https://t.me/Earnpoint10"""
        
        return formatted

    # ========== Monitor SMS - Full Row Text Method ==========
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
                        # Get the complete row text
                        row_text = row.text.strip()
                        if not row_text or len(row_text) < 10:
                            continue
                        
                        print(f"📝 Full Row Text: {row_text[:200]}...")
                        
                        # Create unique ID for this row
                        row_id = f"{row_text}_{hash(row_text)}"
                        
                        if row_id in self.prev_sms:
                            print(f"⏭️ Row already processed")
                            continue
                        
                        # Extract OTP from the full row text
                        otp_code = self.extract_otp_from_text(row_text)
                        
                        if otp_code:
                            print(f"✅ New OTP Found: {otp_code}")
                            
                            self.prev_sms.add(row_id)
                            self.sms_count += 1
                            
                            # Extract other details from row text
                            service = self.extract_service(row_text)
                            number = self.extract_number(row_text)
                            country_name, country_flag = self.get_country_from_text(row_text)
                            
                            date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            print(f"📤 Sending: {otp_code} | Service: {service} | Number: {number} | Country: {country_name}")
                            
                            self.root.after(0, self.update_status, f"📱 New SMS! OTP: {otp_code}", "green")
                            self.root.after(0, self.update_counter)
                            self.root.after(0, self.update_debug, f"✅ OTP: {otp_code} | {service}")
                            
                            # Save to file
                            save_sms_to_file(otp_code, number)
                            
                            # Create and send message
                            formatted_message = self.create_beautiful_message(
                                otp_code, number, country_name, country_flag, service, row_text, date
                            )
                            
                            send_telegram_message(formatted_message)
                        else:
                            print(f"⏭️ No OTP found in row")
                        
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
        if self.bot:
            self.bot.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = ctk.CTk()
    app = SMSCheckerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
