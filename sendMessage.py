import subprocess
import sys

message = sys.argv[1]
def send_imessage(email_address, message):
    # AppleScript to send an iMessage to an email address
    script = f'''
    tell application "Messages"
        send "{message}" to buddy "{email_address}"
    end tell
    '''

    # Execute AppleScript using subprocess
    subprocess.run(['osascript', '-e', script])


# Example usage
send_imessage("ekjotsingh00776@gmail.com", message)
send_imessage("+16047044027", message)
