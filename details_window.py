import gi
import os
import requests

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from datetime import datetime
from dateutil.relativedelta import relativedelta
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


class TeamDetailWindow(Gtk.Window):
    def __init__(self, team_instance, session_cookie, app):
        super().__init__(title=team_instance.name)
        self.team_instance = team_instance
        self.session_cookie = session_cookie
        self.app = app
        self.team_id = team_instance.team_id
        self.init_ui()
        self.process_coming_matches()

    def init_ui(self):
        # Create a vertical box to contain the widgets
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_start(10)
        vbox.set_margin_end(10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)

        # Add team details
        if self.team_instance.division_name:
            division_label = Gtk.Label(
                label=f"Division: {self.team_instance.division_name}"
            )
            vbox.append(division_label)

            table_data = self.fetch_table_data(self.team_instance.division_id)
            if table_data:
                predefined_headers = [
                    "#",
                    "Team",
                    "M",
                    "V",
                    "O",
                    "F",
                    "+",
                    "-",
                    "±",
                    "P",
                ]
                # Create the table
                grid = Gtk.Grid()
                grid.set_column_homogeneous(True)
                grid.set_row_homogeneous(True)

                for i, header in enumerate(predefined_headers):
                    header_label = Gtk.Label(label=header)
                    header_label.set_markup(f"<b>{header}</b>")
                    grid.attach(header_label, i, 0, 1, 1)

                rows = table_data.get("rows", [])
                for row_index, row in enumerate(rows):
                    for col_index, cell in enumerate(row):
                        cell_label = Gtk.Label(label=str(cell))
                        grid.attach(cell_label, col_index, row_index + 1, 1, 1)

                grid.set_column_spacing(1)
                grid.set_row_spacing(5)

                vbox.append(grid)

        # Add coming matches
        # TODO: the list should not show matches already booked
        if self.team_instance.division_name:
            self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            self.set_child(self.vbox)
            # Add coming matches label
            self.bookings_label = Gtk.Label(label="COMING MATCHES")
            vbox.append(self.bookings_label)
            self.booking_list_box = Gtk.ListBox()
            self.booking_list_box.connect("row-activated", self.on_match_clicked)
            vbox.append(self.booking_list_box)

        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self.on_close_clicked)
        vbox.append(close_button)

        # Set the vertical box as the main child of the window
        self.set_child(vbox)

    def on_close_clicked(self, button):
        if self.app and hasattr(self.app, "main_window"):
            self.app.main_window.refresh_bookings()
        self.destroy()

    def fetch_table_data(self, division_id):
        table_url = f"https://korpenmalmoidrottsforening.zoezi.se/api/memberapi/teamsport/result/for_division?division_id={division_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.session_cookie}",
        }

        try:
            response = requests.get(table_url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f"Failed to fetch table: {response.status_code} - {response.text}"
                )
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def fetch_coming_matches(self):
        today = datetime.now().strftime("%Y-%m-%d")
        one_month_ahead = (datetime.now() + relativedelta(months=1)).strftime(
            "%Y-%m-%d"
        )
        coming_matches_url = f"https://korpenmalmoidrottsforening.zoezi.se/api/memberapi/workout/get_for_group?group_id={self.team_id}&fromDate={today}&toDate={one_month_ahead}"
        cookies = {"session": self.session_cookie}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.session_cookie}",
        }
        try:
            response = requests.get(
                coming_matches_url, headers=headers, cookies=cookies
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f"Failed to fetch coming matches: {response.status_code} - {response.text}"
                )
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def process_coming_matches(self):
        coming_matches_data = self.fetch_coming_matches()

        if coming_matches_data:
            for workout in coming_matches_data:
                workout_id = workout.get("id", "No ID")
                extra_title = workout.get("extra_title", "No title")
                start_time_str = workout.get("startTime", "No start time")
                try:
                    start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
                    formatted_start_time = start_time.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    formatted_start_time = "Invalid date"

                match_label = Gtk.Label()
                match_label.set_markup(
                    f"<b>{extra_title}</b>\nStart Time: {formatted_start_time}"
                )
                match_label.set_wrap(True)
                match_label.set_justify(Gtk.Justification.CENTER)

                row = Gtk.ListBoxRow()
                row.set_child(match_label)
                row.match_title = extra_title
                row.start_time = formatted_start_time
                row.workout_id = workout_id

                self.booking_list_box.append(row)

    def on_match_clicked(self, listbox, row):
        match_title = getattr(row, "match_title", None)
        start_time = getattr(row, "start_time", None)
        match_id = getattr(row, "match_id", None)
        team_id = getattr(row, "team_id", None)
        location = getattr(row, "location", None)
        workout_id = getattr(row, "workout_id", None)
        match_status = False

        if match_title and workout_id:
            match_window = MatchDetailWindow(
                match_title=match_title,
                match_time=start_time,
                match_id=match_id,
                team_id=team_id,
                location=location,
                workout_id=workout_id,
                match_status=match_status,
                session_cookie=self.session_cookie,
                app=self,
            )
            match_window.present()


class MatchDetailWindow(Gtk.Window):
    def __init__(
        self,
        match_title,
        match_time,
        match_id,
        team_id,
        location,
        workout_id,
        match_status,
        session_cookie,
        app,
    ):
        super().__init__(title="Match Details")
        self.set_default_size(300, 200)

        self.session_cookie = session_cookie
        self.match_id = match_id
        self.team_id = team_id
        self.workout_id = workout_id
        self.app = app

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_child(vbox)

        title_label = Gtk.Label(label=f"<b>{match_title}</b>")
        title_label.set_markup(f"<b>{match_title}</b>")
        vbox.append(title_label)

        time_label = Gtk.Label(label=f"Time: {match_time}")
        vbox.append(time_label)

        location_label = Gtk.Label(label=f"Location: {location}")
        vbox.append(location_label)

        if match_status == True:
            decline_button = Gtk.Button(label="Decline")
            decline_button.set_margin_top(10)
            decline_button.set_margin_bottom(10)
            decline_button.set_margin_start(20)
            decline_button.set_margin_end(20)
            decline_button.set_hexpand(True)
            decline_button.set_size_request(150, -1)
            decline_button.connect("clicked", self.decline_clicked)
            vbox.append(decline_button)

        if match_status == False:
            attend_button = Gtk.Button(label="Attend")
            attend_button.set_margin_top(10)
            attend_button.set_margin_bottom(10)
            attend_button.set_margin_start(20)
            attend_button.set_margin_end(20)
            attend_button.set_hexpand(True)
            attend_button.set_size_request(150, -1)
            attend_button.connect("clicked", self.attend_clicked)
            vbox.append(attend_button)

    def decline_clicked(self, button):
        decline_url = f"https://korpenmalmoidrottsforening.zoezi.se/api/memberapi/workoutBooking/remove?workout={self.match_id}"
        payload = {"workout": self.match_id}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.session_cookie}",
        }
        cookies = {"session": self.session_cookie}

        try:
            response = requests.post(
                decline_url, json=payload, headers=headers, cookies=cookies
            )
            if response.status_code == 200:
                self.destroy()
                if self.app:
                    print(f"self.app is set: {self.app}")
                    # TODO: booking in main_window is not refreshing after match has been declained
                    if self.app and hasattr(self.app, "main_window"):
                        print(f"self.app.main_window is set: {self.app.main_window}")
                        GLib.idle_add(self.app.main_window.refresh_bookings())
                        # self.app.main_window.refresh_bookings()
                        print("bookings should be refreshed")
            else:
                print("Failed to decline:", response.text)
        except requests.RequestException as e:
            print(f"Request failed: {e}")

    def attend_clicked(self, button):
        attend_url = f"https://korpenmalmoidrottsforening.zoezi.se/api/memberapi/workoutBooking/add?workout={self.workout_id}&method=trainingcard"
        payload = {"workout": self.workout_id, "method": "trainingcard"}
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.session_cookie}",
        }
        cookies = {"session": self.session_cookie}

        try:
            response = requests.post(
                attend_url, json=payload, headers=headers, cookies=cookies
            )
            if response.status_code == 200:
                self.destroy()
                self.add_event_to_calendar()
                self.destroy()
                if self.app and hasattr(self.app, "main_window"):
                    self.app.main_window.refresh_bookings()
            elif response.status_code == 400:
                # TODO: show message in red
                print("Match is not bookable")
                self.destroy()
            else:
                print("Failed to attend:", response.text)
        except requests.RequestException as e:
            print(f"Request failed: {e}")
