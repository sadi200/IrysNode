import threading
import time
import requests
import customtkinter as ctk
from tkinter import messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import re
import phonenumbers
from phonenumbers import geocoder
import os

# ================ Telegram Config ================
TELEGRAM_BOT_TOKEN = "8139596618:AAFrzKY_MGKTRWqoQwTmWqDN4pYF-lJg4NE"
TELEGRAM_CHAT_ID = "-1002978005857"
CHECK_INTERVAL = 0.5 

# ================ Helpers ================
def get_flag(country_code_alpha2):
    OFFSET = 127397
    return ''.join([chr(ord(char.upper()) + OFFSET) for char in country_code_alpha2])


def escape_markdown_v2(text):
    escape_chars = r"\_*\[\]()~`>#+-=|{}.!<>"
    return ''.join(['\\' + c if c in escape_chars else c for c in text])


def mask_phone_number(number):
    """Mask the phone number to show only first 4 and last 4 digits."""
    if len(number) <= 8:
        return escape_markdown_v2(number)  # Too short to mask, return as is
    return escape_markdown_v2(f"{number[:4]}****{number[-4:]}")


# ================ Main App ================
class SMSCheckerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("📩 SMS Checker - Login First")
        self.root.geometry("500x400")
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
        self.status_label.pack(pady=20)

        self.driver = None
        self.monitoring = False
        self.prev_sms = set()

    def update_status(self, text, color="gray"):
        self.status_label.configure(text=text, text_color=color)

    # ========== Start Chrome Browser ==========
    def start_browser(self):
        try:
            self.update_status("Status: Launching browser...", "orange")
            options = Options()
            options.add_argument("--start-maximized")
            # Optional: use your Chrome profile for auto-login
            # options.add_argument(r"user-data-dir=C:\Users\Acer\AppData\Local\Google\Chrome\User Data")

            service = ChromeService(executable_path="chromedriver.exe")
            self.driver = webdriver.Chrome(service=service, options=options)

            self.driver.get("http://54.37.83.141/ints/login")
            self.update_status("✅ Login manually, then click 'Start Checking SMS'", "yellow")
            self.check_sms_button.configure(state="normal")
            self.start_button.configure(state="disabled")

        except WebDriverException as e:
            messagebox.showerror("Error", f"Could not start browser:\n{e}")
            self.update_status("❌ Failed to start browser", "red")

    # ========== Start Monitoring ==========
    def start_monitoring(self):
        if not self.driver:
            messagebox.showwarning("Warning", "Browser not started.")
            return

        self.monitoring = True
        self.update_status("✅ Monitoring started...", "green")
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
            data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "MarkdownV2"}
            r = requests.post(url, json=data)
            if r.status_code != 200:
                print(f"Telegram Error: {r.text}")
                return False
            return True
        except Exception as e:
            print("Telegram Send Error:", e)
            return False

    # ========== Save OTP Details to File ==========
    def save_to_file(self, otp_code, number, country_name, country_flag, service, sms, date):
        try:
            dir_path = r'C:\Users\Administrator\Desktop\bot\Fx telegrambot'
            os.makedirs(dir_path, exist_ok=True)
            file_path = os.path.join(dir_path, 'sms_cdr_stats.txt')

            # Check if file is writable
            if os.path.exists(file_path) and not os.access(file_path, os.W_OK):
                print(f"File Save Error: No write permission for {file_path}")
                return

            # Prepare the new entry
            new_entry = f"OTP Code: {otp_code} Number: {number} Country: {country_name} {country_flag} Service: {service} Message: {sms} Date: {date}\n"

            # Read existing content
            existing_content = ""
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()

            # Write new entry followed by existing content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_entry + existing_content)
                f.flush()  # Ensure write is committed to disk
            print(f"Saved to file: OTP Code: {otp_code}, Number: {number}, Date: {date}")
        except PermissionError:
            print(f"File Save Error: Permission denied for {file_path}")
        except Exception as e:
            print(f"File Save Error: {e}")

    # ========== Monitor SMS ==========
    def monitor_sms(self):
        while self.monitoring:
            try:
                self.driver.refresh()
                time.sleep(1)
                rows = self.driver.find_elements(By.CSS_SELECTOR, "tbody tr")
                print(f"Found {len(rows)} rows in table")  # Debug: confirm rows are found
                for row in rows:
                    columns = row.find_elements(By.TAG_NAME, "td")
                    if len(columns) >= 6:
                        date = columns[0].text.strip()
                        number = columns[2].text.strip()
                        sms = columns[5].text.strip()

                        msg_id = f"{date}-{number}-{sms}"
                        if msg_id in self.prev_sms:
                            print(f"Skipping duplicate message: {msg_id}")  # Debug: confirm skips
                            continue
                        self.prev_sms.add(msg_id)

                        otp_match = re.search(r'(?<!\d)(\d{3,10})(?!\d)', sms)
                        otp_code = otp_match.group(1) if otp_match else "N/A"

                        service = columns[3].text.strip()

                        try:
                            digits_only = re.sub(r"\D", "", number)
                            parsed_number = phonenumbers.parse("+" + digits_only)
                            country_name = geocoder.description_for_number(parsed_number, "en")
                            country_code_alpha2 = phonenumbers.region_code_for_number(parsed_number)
                            country_flag = get_flag(country_code_alpha2) if country_code_alpha2 else ""
                        except:
                            country_name = "Unknown"
                            country_flag = ""

                        # ========== Format Telegram Message ==========
                        formatted_message = (
                            f"✅ {country_flag} {escape_markdown_v2(country_name)} {escape_markdown_v2(service)} OTP Received 🎉\n\n"
                            f"🔐 OTP: `{otp_code}`\n\n"
                            f"🕐 Time: {escape_markdown_v2(date)}\n"
                            f"☎️ Number: {mask_phone_number(number)}\n"
                            f"🌍 Country: {escape_markdown_v2(country_name)} {country_flag}\n"
                            f"⚙️ Service: {escape_markdown_v2(service)}\n"
                            f"```📩 Message:\n{sms}```\n\n"
                            f"[ Join Our Channel](https://t.me/fxsentarofotp)"
                        )

                        # ========== Save to File and Send ==========
                        self.save_to_file(otp_code, number, country_name, country_flag, service, sms, date)
                        if self.send_to_telegram(formatted_message):
                            print(f"Sent to Telegram: {msg_id}")  # Debug: confirm Telegram send
                        else:
                            print(f"Failed to send to Telegram: {msg_id}")

                self.root.after(0, self.update_status, f"📶 Monitoring... {len(self.prev_sms)} messages processed",
                                "green")

            except Exception as e:
                print(f"Monitor Error: {e}")
                self.root.after(0, self.update_status, f"❗ Error occurred, retrying... ({str(e)})", "red")

            time.sleep(CHECK_INTERVAL)

    # ========== Close App ==========
    def on_close(self):
        self.monitoring = False
        if self.driver:
            self.driver.quit()
        self.root.destroy()


# ================ Launcher ================
if __name__ == "__main__":
    root = ctk.CTk()
    app = SMSCheckerApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()