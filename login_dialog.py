import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk


class LoginDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="Login", transient_for=parent, use_header_bar=True)

        # Set window size and margin
        self.set_default_size(300, 150)

        # Create a content box (VBox) for form fields
        content_area = self.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.set_margin_top(10)
        vbox.set_margin_bottom(10)
        content_area.append(vbox)

        # Email input field
        self.email_entry = Gtk.Entry()
        self.email_entry.set_placeholder_text("Email")
        self.email_entry.set_margin_top(10)
        self.email_entry.set_margin_start(20)
        self.email_entry.set_margin_end(20)
        self.email_entry.connect(
            "activate", self.on_enter_pressed
        )  # Handle pressing 'Enter'
        vbox.append(self.email_entry)

        # Password input field
        self.password_entry = Gtk.Entry()
        self.password_entry.set_placeholder_text("Password")
        self.password_entry.set_visibility(False)  # Hide password input
        self.password_entry.set_margin_start(20)
        self.password_entry.set_margin_end(20)
        self.password_entry.connect(
            "activate", self.on_enter_pressed
        )  # Handle pressing 'Enter'
        vbox.append(self.password_entry)

        # Add OK and Cancel buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_margin_top(10)
        button_box.set_margin_start(20)
        button_box.set_margin_end(20)
        vbox.append(button_box)

        ok_button = Gtk.Button(label="OK")
        ok_button.connect("clicked", lambda btn: self.response(Gtk.ResponseType.OK))
        button_box.append(ok_button)

        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect(
            "clicked", lambda btn: self.response(Gtk.ResponseType.CANCEL)
        )
        button_box.append(cancel_button)

        # Set focus to email entry field on dialog show
        self.connect("map", self.on_dialog_mapped)

    def on_enter_pressed(self, entry):
        # Emulate the "OK" button being pressed when 'Enter' is hit
        self.response(Gtk.ResponseType.OK)

    def get_email(self):
        return self.email_entry.get_text()

    def get_password(self):
        return self.password_entry.get_text()

    def on_dialog_mapped(self, dialog):
        # Focus the email entry field when the dialog is displayed
        self.email_entry.grab_focus()