import sys
import tkinter as tk
import subprocess
import pygame
import concurrent.futures

date_str = sys.argv[1]


def show_alert():
    # Create a top-level window for the alert
    alert_window = tk.Toplevel()
    alert_window.title("Alert")
    alert_window.configure(bg='red')

    # Display the alert message
    message = f"<<<<<<<<<<< DATE FOUND: {date_str} I tried to book it. If that did not work, BOOK QUICKLY!!!!!>>>>>>>>>"
    message_label = tk.Label(alert_window, text=message)
    message_label.pack(padx=200, pady=200)

    TIME_IN_SEC = 300

    # Schedule closing the alert window after 3 seconds (3000 milliseconds)
    alert_window.after(TIME_IN_SEC * 1000, lambda: close_alert(alert_window))

    # Start the sound notification subprocess in parallel
    subprocess.Popen(["python", "soundNotification.py", str(TIME_IN_SEC)])
    subprocess.Popen(["python", "sendMessage.py", message])


def close_alert(window):
    window.destroy()


if __name__ == "__main__":
    # Create Tkinter window
    root = tk.Tk()
    root.withdraw()  # Hide the main window

    # Show the alert
    show_alert()

    # Start the Tkinter event loop
    root.mainloop()
