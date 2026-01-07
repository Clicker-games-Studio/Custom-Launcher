import tkinter as tk
from tkinter import ttk, messagebox
import threading, os, zipfile, subprocess, urllib.request, webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse as urlparse
import requests
import time

# ================= CONFIG =================
CLIENT_ID = "5f704963-9f2c-45bc-9fc5-7686ad673437"
CLIENT_SECRET = "hZV8Q~cr1SE4lEWK722JVkt3b3L2sbIYbqWqtc6Q"
TENANT_ID = "c1f3d605-6bc9-4209-b37f-e93e9c0a3aae"
REDIRECT_URI = "http://localhost:5000"
AUTH_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
SCOPES = ["User.Read"]

DOWNLOAD_URL = "https://github.com/Clicker-games-Studio/Minecraft-Offline/releases/download/MC1.12/Mc1.12.zip"
BASE_DIR = os.getcwd()
MC_DIR = os.path.join(BASE_DIR, "minecraft")
VERSION_DIR = os.path.join(MC_DIR, "version", "1.12")
ZIP_PATH = os.path.join(MC_DIR, "Mc1.12.zip")

# ================= COLORS =================
BG = "#0f1115"
SIDEBAR_BG = "#1c1f29"
SIDEBAR_GRADIENT = ["#1c1f29", "#272b36"]
CARD_BG = "#1e2028"
ACCENT = "#22c55e"
ACCENT_HOVER = "#16a34a"
TEXT = "#ffffff"
SUBTEXT = "#9ca3af"
DISABLED = "#374151"

# ================= TK ROOT =================
root = tk.Tk()
root.title("Minecraft Launcher")
root.geometry("1100x600")
root.configure(bg=BG)
root.resizable(False, False)

status_text = tk.StringVar(value="Please login to continue")

# ================= LOCAL SERVER =================
auth_code = None
user_info = None

class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(parsed.query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type","text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h2>You can close this window now.</h2></body></html>")
        else:
            self.send_response(400)
            self.end_headers()

def get_token_from_code(code):
    data = {
        "client_id": CLIENT_ID,
        "scope": " ".join(SCOPES),
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
        "client_secret": CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=data)
    return response.json()

def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

# ================= DOWNLOAD / UNZIP ==================
def download_minecraft():
    os.makedirs(MC_DIR, exist_ok=True)
    status_text.set("Downloading Minecraft 1.12...")
    root.update_idletasks()
    urllib.request.urlretrieve(DOWNLOAD_URL, ZIP_PATH)

def unzip_minecraft():
    status_text.set("Extracting to version/1.12...")
    root.update_idletasks()
    os.makedirs(VERSION_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        zip_ref.extractall(VERSION_DIR)

def find_jar():
    for root_dir, _, files in os.walk(VERSION_DIR):
        for file in files:
            if file.endswith(".jar"):
                return os.path.join(root_dir, file)
    return None

def launch_minecraft():
    jar_path = find_jar()
    if not jar_path:
        messagebox.showerror("Error", "Minecraft JAR not found!")
        return
    status_text.set("Launching Minecraft...")
    root.update_idletasks()
    time.sleep(1)
    subprocess.Popen(["java", f"-Xmx{ram_gb.get()}G", "-jar", jar_path])
    status_text.set("Minecraft running")

# ================= LOGIN FLOW ==================
def login_flow():
    global auth_code, user_info
    auth_code = None
    status_text.set("Opening browser for login...")
    root.update_idletasks()
    
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "response_mode": "query",
        "scope": " ".join(SCOPES)
    }
    url = AUTH_URL + "?" + "&".join([f"{k}={v}" for k,v in params.items()])
    webbrowser.open(url)

    server = HTTPServer(("localhost", 5000), AuthHandler)
    status_text.set("Waiting for login...")
    while auth_code is None:
        server.handle_request()

    token_data = get_token_from_code(auth_code)
    access_token = token_data.get("access_token")
    if access_token:
        user_info = get_user_info(access_token)
        if user_info:
            # Update account card
            name_label.config(text=f"{user_info.get('displayName')}")
            email_label.config(text=f"{user_info.get('userPrincipalName')}")
            status_text.set("Login successful! PLAY is now enabled.")
            play_btn.config(state="normal", bg=ACCENT)
            main_area.pack(expand=True, fill="both")  # Reveal main area after login
            login_btn.place_forget()  # Remove login button
        else:
            messagebox.showerror("Error", "Failed to get user info")
            status_text.set("Login failed")
    else:
        messagebox.showerror("Login Failed", str(token_data))
        status_text.set("Login failed")

# ================= PREPARE MINECRAFT ==================
def prepare_minecraft():
    play_btn.config(state="disabled", bg=DISABLED)
    if not find_jar():
        try:
            download_minecraft()
            unzip_minecraft()
        except Exception as e:
            messagebox.showerror("Error", str(e))
            play_btn.config(state="normal", bg=ACCENT)
            return
    play_btn.config(state="normal", bg=ACCENT)
    launch_minecraft()

# ================= UI ==================
# Sidebar
sidebar = tk.Frame(root, bg=SIDEBAR_BG, width=300)
sidebar.pack(side="left", fill="y")

tk.Label(sidebar, text="MINECRAFT", bg=SIDEBAR_BG, fg=TEXT,
         font=("Segoe UI", 28, "bold")).pack(pady=(40,10))
tk.Label(sidebar, text="Java Edition", bg=SIDEBAR_BG, fg=SUBTEXT,
         font=("Segoe UI", 12)).pack(pady=(0,40))

play_btn = tk.Button(sidebar, text="PLAY", bg=DISABLED, fg="#000000",
                     font=("Segoe UI", 20, "bold"), bd=0, height=2,
                     state="disabled",
                     command=lambda: threading.Thread(target=prepare_minecraft, daemon=True).start())
play_btn.pack(side="bottom", padx=25, pady=40, fill="x")
play_btn.bind("<Enter>", lambda e: play_btn.config(bg=ACCENT_HOVER) if play_btn['state']=='normal' else None)
play_btn.bind("<Leave>", lambda e: play_btn.config(bg=ACCENT) if play_btn['state']=='normal' else None)

options_frame = tk.Frame(sidebar, bg=SIDEBAR_BG)
options_frame.pack(side="bottom", pady=(0,140), fill="x")

tk.Label(options_frame, text="Version", bg=SIDEBAR_BG, fg=SUBTEXT,
         font=("Segoe UI", 12)).pack(anchor="w", padx=20)
selected_version = tk.StringVar(value="1.12")
version_box = ttk.Combobox(options_frame, textvariable=selected_version,
                           values=["1.12"], state="readonly", width=20)
version_box.pack(anchor="w", padx=20, pady=(0,20))

tk.Label(options_frame, text="Max RAM (GB)", bg=SIDEBAR_BG, fg=SUBTEXT,
         font=("Segoe UI", 12)).pack(anchor="w", padx=20)
ram_gb = tk.IntVar(value=4)
ram_slider = ttk.Scale(options_frame, from_=1, to=16, orient="horizontal",
                       length=220, variable=ram_gb)
ram_slider.pack(anchor="w", padx=20)
ram_label = tk.Label(options_frame, text=f"{ram_gb.get()} GB",
                     bg=SIDEBAR_BG, fg=TEXT, font=("Segoe UI", 12))
ram_label.pack(anchor="w", padx=20, pady=(5,10))
ram_slider.config(command=lambda e: ram_label.config(text=f"{ram_gb.get()} GB"))

# Main area (hidden until login)
main_area = tk.Frame(root, bg=BG)

tk.Label(main_area, text="Welcome!", bg=BG, fg=TEXT,
         font=("Segoe UI", 36, "bold")).pack(anchor="w", padx=40, pady=(60,10))
tk.Label(main_area, text="Ready to play Minecraft 1.12", bg=BG, fg=SUBTEXT,
         font=("Segoe UI", 16)).pack(anchor="w", padx=40)

# Account card
account_card = tk.Frame(main_area, bg=CARD_BG, width=400, height=100)
account_card.pack(anchor="w", padx=40, pady=(20,10))
account_card.pack_propagate(False)
name_label = tk.Label(account_card, text="Not logged in", bg=CARD_BG, fg=TEXT, font=("Segoe UI", 14, "bold"))
name_label.pack(anchor="w", padx=20, pady=(20,0))
email_label = tk.Label(account_card, text="", bg=CARD_BG, fg=SUBTEXT, font=("Segoe UI", 12))
email_label.pack(anchor="w", padx=20)

# Version card
version_card = tk.Frame(main_area, bg=CARD_BG, width=500, height=200)
version_card.pack(padx=40, pady=30, anchor="w")
version_card.pack_propagate(False)
tk.Label(version_card, text="Classic Offline 1.12", bg=CARD_BG, fg=TEXT,
         font=("Segoe UI", 22, "bold")).pack(anchor="w", padx=20, pady=(30,5))
tk.Label(version_card, text="Automatic download and launch", bg=CARD_BG, fg=SUBTEXT,
         font=("Segoe UI", 12)).pack(anchor="w", padx=20)

# Status bar
status_bar = tk.Frame(root, bg=SIDEBAR_BG, height=36)
status_bar.pack(side="bottom", fill="x")
tk.Label(status_bar, textvariable=status_text, bg=SIDEBAR_BG, fg=SUBTEXT,
         font=("Segoe UI", 10), padx=20).pack(side="left")

# Login button (force login first)
login_btn = ttk.Button(root, text="Login with Microsoft",
                       command=lambda: threading.Thread(target=login_flow, daemon=True).start())
login_btn.place(x=400, y=250)  # Centered

root.mainloop()
