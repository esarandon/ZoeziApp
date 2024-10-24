import gi
import requests
from datetime import datetime
from details_window import TeamDetailWindow, MatchDetailWindow

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class ZoeziApp(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(title="Korpen App", application=app)
        self.set_default_size(400, 500)

        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.vbox.set_margin_start(10)
        self.vbox.set_margin_end(10)
        self.vbox.set_margin_top(10)
        self.vbox.set_margin_bottom(10)
        self.set_child(self.vbox)

        self.status_button = Gtk.Label(label="")
        self.vbox.append(self.status_button)

        self.teams_label = Gtk.Label(label="TEAMS")
        self.vbox.append(self.teams_label)

        self.team_list_box = Gtk.ListBox()
        self.team_list_box.connect("row-activated", self.on_team_clicked)
        self.vbox.append(self.team_list_box)

        self.bookings_label = Gtk.Label(label="COMING MATCHES")
        self.vbox.append(self.bookings_label)

        self.booking_list_box = Gtk.ListBox()
        self.booking_list_box.connect("row-activated", self.on_match_clicked)
        self.vbox.append(self.booking_list_box)

    def update_status(self, status_message):
        self.status_button.set_label(status_message)

    def update_teams(self, groups):
        self.group_list_box.remove_all()
        for group in groups:
            group_label = Gtk.Label(label=group["name"])
            row = Gtk.ListBoxRow()
            row.set_child(group_label)
            row.set_data("team_name", group["name"])
            self.group_list_box.append(row)

    def fetch_user_data(self):
        today = datetime.now().strftime("%Y-%m-%d")
        booking_url = f"https://korpenmalmoidrottsforening.zoezi.se/api/memberapi/bookings/get?startTime={today} 00:00"

        cookies = {"session": self.get_application().session_cookie}

        try:
            response = requests.get(booking_url, cookies=cookies)
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f"Failed to fetch bookings: {response.status_code} - {response.text}"
                )
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def fetch_and_display_teams(self, teams_dict):
        data = self.fetch_user_data()
        teamsportbookings = data.get("teamsportbookings", [])
        latest_divisions = {}

        for entry in teamsportbookings:
            team_name = entry.get("name")
            team_id = entry.get("group_id")
            divisions = entry.get("divisions", [])

            if divisions:
                last_division = divisions[-1]
                division_name = last_division.get("name")
                division_id = last_division.get("id")

                latest_divisions[team_name] = (team_id, division_name, division_id)
        
        for team_name, team in teams_dict.items():
            if team_name in latest_divisions:
                team_id, division_name, division_id = latest_divisions[team_name]
                team.update_team_data(team_id, division_name, division_id)

        self.team_list_box.remove_all()
        for team_name, team in teams_dict.items():
            team_label = Gtk.Label(label=team.name)
        
            row = Gtk.ListBoxRow()
            row.set_child(team_label)
            row.team_instance = team

            self.team_list_box.append(row)

    def on_team_clicked(self, listbox, row):
        team_instance = getattr(row, "team_instance", None)

        if team_instance:
            team_window = TeamDetailWindow(
                team_instance=team_instance,
                session_cookie=self.get_application().session_cookie,
                app=self.get_application(),
            )
            team_window.present()

    def fetch_and_display_bookings(self):
        data = self.fetch_user_data()

        if data:
            workouts = data.get("workouts", [])
            self.booking_list_box.remove_all()

            for workout in workouts:
                if isinstance(workout, dict):
                    extra_title = workout.get("extra_title", "No title")
                    start_time_str = workout.get("startTime", "No start time")
                    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                    formatted_start_time = start_time.strftime("%Y-%m-%d %H:%M")
                    location = "No location"

                    match_activity = workout.get("match_activity", {})
                    resources = match_activity.get("resources", [])
                    if resources:
                        location = resources[0].get("lastname", "No location")

                    booking_info = Gtk.Label()
                    booking_info.set_markup(
                        f"<b>{extra_title}</b>\nStart Time: {formatted_start_time}, Location: {location}"
                    )
                    booking_info.set_wrap(True)
                    booking_info.set_justify(Gtk.Justification.CENTER)

                    row = Gtk.ListBoxRow()
                    row.set_child(booking_info)
                    row.match_title = extra_title
                    row.start_time = start_time
                    row.location = location
                    row.match_id = workout.get("id", "No ID")

                    self.booking_list_box.append(row)

    def on_match_clicked(self, listbox, row):
        match_title = getattr(row, "match_title", None)
        start_time = getattr(row, "start_time", None)
        location = getattr(row, "location", None)
        match_id = getattr(row, "match_id", None)
        team_id = getattr(row, "team_id", None)
        workout_id = getattr(row, "workout_id", None)
        match_status = True

        if match_title and match_id:
            match_window = MatchDetailWindow(
                match_title=match_title,
                match_time=start_time,
                location=location,
                match_id=match_id,
                team_id=team_id,
                workout_id=workout_id,
                session_cookie=self.get_application().session_cookie,
                app=self,
                match_status=match_status,
            )
            match_window.present()

    def refresh_bookings(self):
        self.booking_list_box.remove_all()
        self.fetch_and_display_bookings()
