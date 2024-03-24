import sys

import pygame

play_times = int(sys.argv[1])

# Initialize pygame
pygame.init()

# Provide the path to your MP3 file
mp3_file_path = "/Users/I550652/Downloads/iphone_alarm.mp3"

# Load the MP3 file
pygame.mixer.music.load(mp3_file_path)

# Play the MP3 file n times
for _ in range(play_times):
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue

# Quit pygame when done
pygame.quit()
