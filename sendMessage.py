import subprocess
import sys
import configparser

message = sys.argv[1]

# Create a configparser object
config = configparser.ConfigParser()

# Read the properties file
config.read('project.properties')
numbers = config.get('Contact', 'numbers').split(',')
emails = config.get('Contact', 'emails').split(',')


def send_imessage(email_address, message):
    # AppleScript to send an iMessage to an email address
    script = f'''
    tell application "Messages"
        send "{message}" to buddy "{email_address}"
    end tell
    '''

    # Execute AppleScript using subprocess
    subprocess.run(['osascript', '-e', script])


for number in numbers:
    send_imessage(number, message)

for email in emails:
    send_imessage(email, message)