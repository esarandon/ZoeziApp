import gi
import json
import requests

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from team import Team
from main_window import ZoeziApp
from login_dialog import LoginDialog


class KorpenApp(Gtk.Application):
    def __init__(self):
        super().__init__()
        self.session_cookie = None
        self.main_window = None

    def do_activate(self):
        if not self.main_window:

            self.main_window = ZoeziApp(self)

            self.main_window.connect("close-request", self.on_window_close)

        self.show_login_dialog()

    def show_login_dialog(self):
        login_dialog = LoginDialog(
            parent=self.main_window if self.main_window else None
        )
        login_dialog.connect("response", self.on_dialog_response)
        login_dialog.present()

    def on_dialog_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            email = dialog.get_email()
            password = dialog.get_password()

            user_info, session_cookie = self.attempt_login(email, password)
            if user_info:
                self.main_window.status_button.set_label(
                    f"Logged in successfully! Welcome, {user_info['firstname']} {user_info['lastname']}."
                )

                self.session_cookie = session_cookie

                self.main_window.team_list_box.remove_all()

                groups = user_info.get("groups", [])                
                self.teams_dict = {}  # Dictionary to store team instances
                self.team_names_list = []  # List to store team names

                for group in groups:
                    team_name = group.get("name")
                    team_id = group.get("id")

                    team = Team(name=team_name, team_id=team_id)
                    self.teams_dict[team_name] = team  # Use team_name as key

                    self.team_names_list.append(team_name)

                    team_label = Gtk.Label(label=team_name)
                    self.main_window.team_list_box.append(team_label)

                self.main_window.fetch_and_display_teams(self.teams_dict)
                self.main_window.fetch_and_display_bookings()

                self.main_window.set_visible(True)

            else:
                self.show_login_dialog()
        elif response_id == Gtk.ResponseType.CANCEL:
            self.main_window.status_button.set_label("Login was cancelled")

        dialog.destroy()

    def attempt_login(self, email, password):
        login_url = (
            "https://korpenmalmoidrottsforening.zoezi.se/api/v8.0/memberapi/login"
        )
        payload = {"login": email, "password": password}
        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(
                login_url, data=json.dumps(payload), headers=headers, cookies=None
            )
            if response.status_code == 200:
                cookies = response.cookies.get_dict()
                session_cookie = cookies.get("session", None)
                return response.json(), session_cookie
            else:
                return None, None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None, None

    def on_window_close(self, window):
        # Exit the application when the main window is closed
        self.quit()
        return True


app = KorpenApp()
app.run(None)
