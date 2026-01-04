import os
import json
import threading
import time

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput

# =======================
# Shared State (Global)
# =======================
STATE_FILE = "state.json"
CONFIG_FILE = "config.json"

state = {
    "app_enabled": True,
    "users": {}  # username: {"blocked": False}
}

def load_state():
    global state
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = json.load(f)

def save_state():
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

load_state()

# =======================
# Admin Server (Port 5000)
# =======================
admin_app = FastAPI()

@admin_app.get("/", response_class=HTMLResponse)
def admin_home():
    users_rows = ""
    for u, info in state["users"].items():
        users_rows += f"""
        <tr>
          <td>{u}</td>
          <td>{'BLOCKED' if info.get('blocked') else 'OK'}</td>
          <td>
            <a href="/block/{u}">Block</a> |
            <a href="/unblock/{u}">Unblock</a>
          </td>
        </tr>
        """

    return f"""
    <html>
    <head><title>Admin Panel</title></head>
    <body>
      <h2>LAN Voice App – Admin</h2>

      <p>App Status:
        <b>{"ENABLED" if state["app_enabled"] else "DISABLED"}</b>
      </p>

      <a href="/app/on">Enable App</a> |
      <a href="/app/off">Disable App</a>

      <h3>Users</h3>
      <table border="1" cellpadding="5">
        <tr><th>User</th><th>Status</th><th>Action</th></tr>
        {users_rows}
      </table>
    </body>
    </html>
    """

@admin_app.get("/app/on")
def app_on():
    state["app_enabled"] = True
    save_state()
    return JSONResponse({"status": "app enabled"})

@admin_app.get("/app/off")
def app_off():
    state["app_enabled"] = False
    save_state()
    return JSONResponse({"status": "app disabled"})

@admin_app.get("/block/{username}")
def block_user(username: str):
    if username in state["users"]:
        state["users"][username]["blocked"] = True
        save_state()
    return JSONResponse({"status": f"{username} blocked"})

@admin_app.get("/unblock/{username}")
def unblock_user(username: str):
    if username in state["users"]:
        state["users"][username]["blocked"] = False
        save_state()
    return JSONResponse({"status": f"{username} unblocked"})

def run_admin():
    uvicorn.run(admin_app, host="0.0.0.0", port=5000, log_level="error")

# =======================
# Client (Kivy)
# =======================
def load_username():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("username")
    return None

def save_username(name):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"username": name}, f, ensure_ascii=False)

class MainUI(BoxLayout):
    def __init__(self, username, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        self.username = username

        self.status = Label(text="Checking permissions...")
        self.add_widget(Label(text=f"Welcome: {username}"))
        self.add_widget(self.status)

        self.refresh_btn = Button(text="Re-check Status")
        self.refresh_btn.bind(on_press=self.check_access)
        self.add_widget(self.refresh_btn)

        self.check_access()

    def check_access(self, *args):
        load_state()

        if not state["app_enabled"]:
            self.status.text = "APP DISABLED BY ADMIN"
            return

        info = state["users"].get(self.username)
        if info and info.get("blocked"):
            self.status.text = "YOU ARE BLOCKED BY ADMIN"
            return

        self.status.text = "READY (Voice coming next stage)"

class VoiceApp(App):
    def build(self):
        username = load_username()
        if not username:
            return self.ask_name()
        self.register_user(username)
        return MainUI(username)

    def ask_name(self):
        layout = BoxLayout(orientation="vertical")
        inp = TextInput(hint_text="Enter your name")
        btn = Button(text="Save")

        layout.add_widget(inp)
        layout.add_widget(btn)

        popup = Popup(title="First Run", content=layout, size_hint=(0.8, 0.4))

        def save_name(instance):
            name = inp.text.strip()
            if name:
                save_username(name)
                self.register_user(name)
                popup.dismiss()
                self.root = MainUI(name)

        btn.bind(on_press=save_name)
        popup.open()
        return BoxLayout()

    def register_user(self, username):
        if username not in state["users"]:
            state["users"][username] = {"blocked": False}
            save_state()

# =======================
# MAIN
# =======================
if __name__ == "__main__":
    threading.Thread(target=run_admin, daemon=True).start()
    VoiceApp().run()
