import os
import json
import threading

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock

# =======================
# Shared State (Global)
# =======================
# On Android, we save to the app's private data folder
STATE_FILE = "state.json"
CONFIG_FILE = "config.json"

state = {
    "app_enabled": True,
    "users": {}  # username: {"blocked": False}
}

def load_state():
    global state
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state.update(json.load(f))
    except Exception as e:
        print(f"Error loading state: {e}")

def save_state():
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving state: {e}")

load_state()

# =======================
# Admin Server (Port 5000)
# =======================
admin_app = FastAPI()

@admin_app.get("/", response_class=HTMLResponse)
def admin_home():
    users_rows = ""
    for u, info in state["users"].items():
        status_text = 'BLOCKED' if info.get('blocked') else 'OK'
        users_rows += f"""
        <tr>
          <td>{u}</td>
          <td>{status_text}</td>
          <td>
            <a href="/block/{u}">Block</a> |
            <a href="/unblock/{u}">Unblock</a>
          </td>
        </tr>
        """

    app_status = "ENABLED" if state["app_enabled"] else "DISABLED"
    return f"""
    <html>
    <head><title>Admin Panel</title></head>
    <body>
      <h2>LAN Voice App – Admin</h2>
      <p>App Status: <b>{app_status}</b></p>
      <a href="/app/on">Enable App</a> | <a href="/app/off">Disable App</a>
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
    return {"status": "enabled"}

@admin_app.get("/app/off")
def app_off():
    state["app_enabled"] = False
    save_state()
    return {"status": "disabled"}

@admin_app.get("/block/{{username}}")
def block_user(username: str):
    if username in state["users"]:
        state["users"][username]["blocked"] = True
        save_state()
    return {"status": "blocked"}

@admin_app.get("/unblock/{{username}}")
def unblock_user(username: str):
    if username in state["users"]:
        state["users"][username]["blocked"] = False
        save_state()
    return {"status": "unblocked"}

def run_admin():
    # Use 0.0.0.0 so other devices on the LAN can see the admin panel
    uvicorn.run(admin_app, host="0.0.0.0", port=5000)

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
        self.add_widget(Label(text=f"User: {username}", size_hint_y=0.2))
        self.add_widget(self.status)

        self.refresh_btn = Button(text="Refresh Admin Settings", size_hint_y=0.2)
        self.refresh_btn.bind(on_press=self.check_access)
        self.add_widget(self.refresh_btn)
        
        # Check every 5 seconds automatically
        Clock.schedule_interval(self.check_access, 5)

    def check_access(self, *args):
        load_state()
        if not state["app_enabled"]:
            self.status.text = "APP DISABLED BY ADMIN"
            self.status.color = (1, 0, 0, 1) # Red
        elif state["users"].get(self.username, {}).get("blocked"):
            self.status.text = "YOU ARE BLOCKED"
            self.status.color = (1, 0, 0, 1)
        else:
            self.status.text = "CONNECTED & ACTIVE"
            self.status.color = (0, 1, 0, 1) # Green

class VoiceApp(App):
    def build(self):
        self.username = load_username()
        if not self.username:
            return self.ask_name()
        self.register_user(self.username)
        return MainUI(self.username)

    def ask_name(self):
        layout = BoxLayout(orientation="vertical", padding=20)
        self.inp = TextInput(hint_text="Enter your name", multiline=False)
        btn = Button(text="Start App")
        layout.add_widget(self.inp)
        layout.add_widget(btn)
        
        self.popup = Popup(title="First Time Setup", content=layout, size_hint=(0.9, 0.5), auto_dismiss=False)
        btn.bind(on_press=self.save_and_start)
        self.popup.open()
        return BoxLayout()

    def save_and_start(self, instance):
        name = self.inp.text.strip()
        if name:
            save_username(name)
            self.register_user(name)
            self.popup.dismiss()
            # Replace the temporary layout with the real UI
            self.root_window.remove_widget(self.root)
            self.root = MainUI(name)
            self.root_window.add_widget(self.root)

    def register_user(self, username):
        if username not in state["users"]:
            state["users"][username] = {"blocked": False}
            save_state()

if __name__ == "__main__":
    threading.Thread(target=run_admin, daemon=True).start()
    VoiceApp().run()
