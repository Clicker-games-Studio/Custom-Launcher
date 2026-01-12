import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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

# ================= GLOBALS =================
auth_code = None
user_info = None
java_path = None

# ================= AUTH SERVER =================
class AuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urlparse.urlparse(self.path)
        params = urlparse.parse_qs(parsed.query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>You can close this window.</h2>")
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
    return requests.post(TOKEN_URL, data=data).json()

def get_user_info(token):
    r = requests.get(
        "https://graph.microsoft.com/v1.0/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    return r.json() if r.status_code == 200 else None

# ================= JAVA SELECT =================
def select_java():
    global java_path
    path = filedialog.askopenfilename(
        title="Select java.exe",
        filetypes=[("Java Executable", "java.exe"), ("All files", "*.*")]
    )
    if path:
        java_path = path
        java_label.config(text=os.path.basename(path))
        status_text.set("Java selected")

# ================= DOWNLOAD =================
def download_minecraft():
    os.makedirs(MC_DIR, exist_ok=True)
    status_text.set("Downloading Minecraft...")
    urllib.request.urlretrieve(DOWNLOAD_URL, ZIP_PATH)

def unzip_minecraft():
    os.makedirs(VERSION_DIR, exist_ok=True)
    status_text.set("Extracting files...")
    with zipfile.ZipFile(ZIP_PATH, "r") as z:
        z.extractall(VERSION_DIR)

# ================= CLASSPATH =================
def build_classpath():
    jars = []
    for file in os.listdir(VERSION_DIR):
        if file.endswith(".jar"):
            jars.append(file)   # RELATIVE (IMPORTANT)
    return ";".join(jars)

# ================= LAUNCH =================
def launch_minecraft():
    if not java_path:
        messagebox.showerror("Error", "Select Java first")
        return

    classpath = build_classpath()
    if not classpath:
        messagebox.showerror("Error", "No JARs found")
        return

    email = user_info.get("userPrincipalName", "Player")
    username = email.split("@")[0]

    status_text.set("Launching Minecraft...")

    subprocess.Popen(
        [
            java_path,
            f"-Xmx{ram_gb.get()}G",
            "-Djava.library.path=natives",
            "-cp", classpath,
            "net.minecraft.client.main.Main",
            "--username", username,
            "--version", "1.12",
            "--gameDir", ".",          # EXACTLY LIKE CMD
            "--assetsDir", "assets",   # EXACTLY LIKE CMD
            "--assetIndex", "1.12",
            "--accessToken", "offlineToken123",
            "--userProperties", "{}",
            "--userType", "legacy"
        ],
        cwd=VERSION_DIR               # RUNS INSIDE FOLDER
    )

    status_text.set("Minecraft running")

def prepare_minecraft():
    play_btn.config(state="disabled", bg=DISABLED)
    if not os.path.exists(VERSION_DIR):
        download_minecraft()
        unzip_minecraft()
    play_btn.config(state="normal", bg=ACCENT)
    launch_minecraft()

# ================= LOGIN =================
def login_flow():
    global auth_code, user_info
    auth_code = None

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES)
    }

    webbrowser.open(AUTH_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items()))

    server = HTTPServer(("localhost", 5000), AuthHandler)
    while auth_code is None:
        server.handle_request()

    token = get_token_from_code(auth_code).get("access_token")
    user_info = get_user_info(token)

    name_label.config(text=user_info["displayName"])
    email_label.config(text=user_info["userPrincipalName"])
    main_area.pack(expand=True, fill="both")
    login_btn.place_forget()
    play_btn.config(state="normal", bg=ACCENT)
    status_text.set("Login successful")

# ================= UI =================
sidebar = tk.Frame(root, bg=SIDEBAR_BG, width=300)
sidebar.pack(side="left", fill="y")

tk.Label(sidebar, text="MINECRAFT", bg=SIDEBAR_BG, fg=TEXT,
         font=("Segoe UI", 28, "bold")).pack(pady=40)

play_btn = tk.Button(
    sidebar, text="PLAY", bg=DISABLED, fg="#000",
    font=("Segoe UI", 20, "bold"), bd=0,
    state="disabled",
    command=lambda: threading.Thread(target=prepare_minecraft, daemon=True).start()
)
play_btn.pack(side="bottom", padx=25, pady=40, fill="x")

options = tk.Frame(sidebar, bg=SIDEBAR_BG)
options.pack(side="bottom", pady=100)

tk.Label(options, text="Max RAM (GB)", bg=SIDEBAR_BG, fg=SUBTEXT).pack(anchor="w")
ram_gb = tk.IntVar(value=4)
ttk.Scale(options, from_=1, to=16, variable=ram_gb, length=220).pack()

tk.Label(options, text="Java", bg=SIDEBAR_BG, fg=SUBTEXT).pack(anchor="w", pady=(10,0))
ttk.Button(options, text="Select Java", command=select_java).pack(anchor="w")
java_label = tk.Label(options, text="Not selected", bg=SIDEBAR_BG, fg=TEXT)
java_label.pack(anchor="w")

# ================= MAIN =================
main_area = tk.Frame(root, bg=BG)

tk.Label(main_area, text="Welcome", bg=BG, fg=TEXT,
         font=("Segoe UI", 36, "bold")).pack(anchor="w", padx=40, pady=40)

account = tk.Frame(main_area, bg=CARD_BG, width=400, height=100)
account.pack(padx=40)
account.pack_propagate(False)

name_label = tk.Label(account, text="", bg=CARD_BG, fg=TEXT, font=("Segoe UI", 14, "bold"))
name_label.pack(anchor="w", padx=20, pady=10)

email_label = tk.Label(account, text="", bg=CARD_BG, fg=SUBTEXT)
email_label.pack(anchor="w", padx=20)

# ================= STATUS =================
status = tk.Frame(root, bg=SIDEBAR_BG, height=36)
status.pack(side="bottom", fill="x")
tk.Label(status, textvariable=status_text, bg=SIDEBAR_BG, fg=SUBTEXT).pack(side="left", padx=20)

login_btn = ttk.Button(
    root, text="Login with Microsoft",
    command=lambda: threading.Thread(target=login_flow, daemon=True).start()
)
login_btn.place(x=420, y=260)

root.mainloop()
