import RPi.GPIO as GPIO
import pygame
import os
from picamera import PiCamera
from time import sleep, time
from os import listdir, rename
from os.path import isfile, join
from PIL import Image
from datetime import datetime
from pathlib import Path
import shutil

# Constants
# GIFS_PATH = '/home/plevin/piBooth/photobooth_gifs/'
SNAP_SOUND_PATH = '/home/plevin/gifbooth/click.wav'
INSTRUCTION_IMAGE_PATH = '/home/plevin/gifbooth/start_images/stooges.jpg'
TEMP_IMAGES_PATH = '/home/plevin/gifbooth/gif_temp/'
RECENT_GIFS_PATH = '/home/plevin/gifbooth/gif_recent/'
ARCHIVE_PATH = '/home/plevin/gifbooth/gif_archive/'
SWITCH_PIN = 6
BUTTON_PIN = 5
DEBOUNCE_THRESHOLD = 0.5  # seconds
NUM_PHOTOS = 5
PHOTO_INTERVAL = 0.15  # seconds
GIF_DURATION = 500  # milliseconds
NUM_LOOPS_PER_GIF = 4  # You can change this to set how many times each GIF is looped


# Initialization
print("Initializing system...")
pygame.init()
pygame.mixer.init()
screen_info = pygame.display.Info()
screen_width, screen_height = screen_info.current_w, screen_info.current_h
window = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
camera = PiCamera()
camera.resolution = (screen_width, screen_height)
print("Camera initialized.")

# Load sounds and images
print("Loading sounds and images...")
snap_sound = pygame.mixer.Sound(SNAP_SOUND_PATH)
instruction_image = pygame.transform.scale(pygame.image.load(INSTRUCTION_IMAGE_PATH).convert(), (screen_width, screen_height))

# GPIO setup
print("Setting up GPIO...")
GPIO.setmode(GPIO.BCM)
GPIO.setup(SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Flags and variables
running = True
capture_in_progress = False
view_mode_active = False
last_button_press_time = 0
display_instruction_flag = True

# Function definitions
def button_callback(channel):
    global capture_in_progress, last_button_press_time
    print("Button pressed. Checking if capture is already in progress...")
    current_time = time()
    if not capture_in_progress and (current_time - last_button_press_time) >= DEBOUNCE_THRESHOLD:
        print("Starting image capture sequence...")
        last_button_press_time = current_time
        capture_in_progress = True
        capture_images()
        capture_in_progress = False
        print("Image capture sequence complete.")
    else:
        print("Debounce or capture already in progress, ignoring button press.")

def switch_callback(channel):
    global view_mode_active, display_instruction_flag
    # Detect the current state of the switch
    if GPIO.input(SWITCH_PIN):
        # If the switch is UP, enter view mode
        if not view_mode_active:  # Only enter view mode if not already in it
            view_mode_active = True
            display_instruction_flag = False
            enter_view_mode()
    else:
        # If the switch is DOWN, exit view mode
        if view_mode_active:  # Only exit view mode if currently in it
            view_mode_active = False
            display_instruction_flag = True
            display_instruction_image()  # Immediately display instruction image

def display_instruction_image():
    window.blit(instruction_image, (0, 0))
    pygame.display.flip()

def enter_view_mode():
    global view_mode_active
    print("Entering view mode...")
    
    while view_mode_active:
        # Get the 5 most recent directories containing image sets
        recent_dirs = sorted(Path(TEMP_IMAGES_PATH).glob('*/'), key=os.path.getmtime, reverse=True)[:5]

        # Loop through each directory
        for image_dir in recent_dirs:
            # Make sure the directory exists and has image files
            if image_dir.is_dir():
                image_files = sorted(image_dir.glob('*.jpg'), key=os.path.getmtime)

                # Loop through each image set NUM_LOOPS_PER_GIF times
                for _ in range(NUM_LOOPS_PER_GIF):
                    # Display each image in the directory in sequence
                    for image_file in image_files:
                        if not view_mode_active:
                            print("Exiting view mode...")
                            return
                        display_image(str(image_file))  # Display the image
                        sleep(PHOTO_INTERVAL)  # Wait for the duration of each frame

                    if not view_mode_active:
                        print("Exiting view mode...")
                        return

        # Optional: Add a short delay before repeating the entire process
        sleep(0.5)

def capture_images():
    global display_instruction_flag
    print("Capturing images...")
    
    # Create a unique directory for the new set of images
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    current_set_dir = Path(TEMP_IMAGES_PATH) / timestamp
    current_set_dir.mkdir(exist_ok=True)
    
    # Save images to the new directory
    image_paths = [current_set_dir / f'image{i:02d}.jpg' for i in range(NUM_PHOTOS)]
    for image_path in image_paths:
        if not running or view_mode_active:
            print("Aborting capture_images, running: {}, view_mode_active: {}".format(running, view_mode_active))
            return
        capture_image(image_path)
        sleep(PHOTO_INTERVAL)
        check_for_quit()
        if not running:
            print("Stopping image capture due to ESC key press...")
            return
    
    # Pass the paths of the temp images to be processed into a GIF
    process_images_to_gif(image_paths)
    display_instruction_flag = True
    print("Done capturing images.")
    display_instruction_image()

def capture_image(image_path):
    print(f"Capturing image to {image_path}...")
    camera.capture(str(image_path))  # Convert PosixPath to string
    snap_sound.play()
    display_image(str(image_path), flash=True)  # Ensure display_image also accepts a string path

    
def display_image(image_path, flash=False):
    if flash:
        print("Flashing screen...")
        window.fill((255, 255, 255))
        pygame.display.flip()
        sleep(0.1)
    print(f"Displaying image {image_path}...")
    image = pygame.transform.scale(pygame.image.load(image_path).convert(), (screen_width, screen_height))
    window.blit(image, (0, 0))
    pygame.display.flip()

def process_images_to_gif(image_paths):
    print("Processing images into GIF...")
    check_for_quit()
    if not running:
        print("Aborting GIF creation due to ESC key press...")
        return
    # Create an animated GIF from the temp images and save it to RECENT_GIFS_PATH
    recent_gif_path = create_animated_gif(image_paths)
    # Pass the path of the recently created GIF for renaming and archiving
    rename_and_archive_gifs(recent_gif_path)
    simulate_gif(image_paths)
    print("Finished processing images into GIF.")
    # Manage the directories of images
    manage_image_directories()

def create_animated_gif(image_paths):
    print("Creating animated GIF...")
    images = [Image.open(str(image_path)) for image_path in image_paths]
    output_path = os.path.join(RECENT_GIFS_PATH, 'recent0.gif')
    images[0].save(output_path, save_all=True, append_images=images[1:], loop=0, duration=GIF_DURATION)
    print("Animated GIF created.")
    return output_path

def rename_and_archive_gifs(output_path):
    print("Renaming and archiving GIFs...")
    # Shift the names of existing recent GIFs
    for i in range(4, 0, -1):
        old_path = os.path.join(RECENT_GIFS_PATH, f'recent{i - 1}.gif')
        new_path = os.path.join(RECENT_GIFS_PATH, f'recent{i}.gif')
        if os.path.isfile(old_path):
            print(f"Renaming {old_path} to {new_path}...")
            shutil.move(old_path, new_path)
    
    # Copy the most recent GIF to the archive with a timestamped name
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_path = os.path.join(ARCHIVE_PATH, f'{timestamp}.gif')
    print(f"Archiving recent GIF as {archive_path}...")
    shutil.copy(output_path, archive_path)
    
def simulate_gif(image_paths):
    print("Simulating GIF...")
    start_time = time()
    while time() - start_time < NUM_PHOTOS * PHOTO_INTERVAL:
        for image_path in image_paths:
            if not running:
                print("Stopping GIF simulation due to ESC key press...")
                return
            display_image(image_path)
            sleep(PHOTO_INTERVAL)
            if time() - start_time >= NUM_PHOTOS * PHOTO_INTERVAL:
                break
    print("Finished simulating GIF.")

def manage_image_directories():
    # Get all the image set directories
    all_image_dirs = sorted(Path(TEMP_IMAGES_PATH).glob('*/'), key=os.path.getmtime)
    
    # Keep only the 5 most recent directories
    while len(all_image_dirs) > 5:
        shutil.rmtree(str(all_image_dirs.pop(0)))  # Remove oldest directory
        
def check_for_quit():
    global running, view_mode_active
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            print("ESC key pressed, setting running to False...")
            running = False
        elif event.type == pygame.QUIT:
            print("Quit event detected, setting running to False...")
            running = False

    # Check the switch state directly
    if not GPIO.input(SWITCH_PIN) and view_mode_active:
        print("Switch toggled to DOWN position, exiting view mode...")
        view_mode_active = False

def cleanup():
    print("Cleaning up and exiting...")
    try:
        # Remove temp images
        for file in listdir(TEMP_IMAGES_PATH):
            file_path = join(TEMP_IMAGES_PATH, file)
            if isfile(file_path):
                os.remove(str(file_path))
    except Exception as e:
        print(f"Error cleaning up temp images: {e}")

    camera.close()
    pygame.quit()
    GPIO.cleanup()

# Event detections
print("Setting up event detections...")
GPIO.add_event_detect(BUTTON_PIN, GPIO.FALLING, callback=button_callback, bouncetime=int(DEBOUNCE_THRESHOLD * 1000))
GPIO.add_event_detect(SWITCH_PIN, GPIO.BOTH, callback=switch_callback, bouncetime=300)

# Main Loop
try:
    if GPIO.input(SWITCH_PIN):
        print("Switch is UP at startup, entering view mode...")
        view_mode_active = True
        enter_view_mode()
    else:
        print("Switch is DOWN at startup, displaying instruction image...")
        view_mode_active = False
        display_instruction_flag = True

    while running:
        check_for_quit()
        if display_instruction_flag and not view_mode_active:
            display_instruction_image()
            display_instruction_flag = False
finally:
    cleanup()

