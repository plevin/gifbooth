import pygame
import time
import os
import shutil
from picamera import PiCamera
import config

# Initialize Pygame and create a window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((config.screen_width, config.screen_height), pygame.FULLSCREEN)
pygame.display.set_caption('Photobooth')

# Load sounds
print("Loading sounds...")
snap_sound = pygame.mixer.Sound(config.snap_path)

def clear_screen():
    screen.fill((0, 0, 0))
    pygame.display.flip()

def show_image_for_duration(image_path, duration):
    try:
        image = pygame.image.load(image_path)
        image = pygame.transform.scale(image, (config.screen_width, config.screen_height))
        screen.blit(image, (0, 0))
        pygame.display.flip()

        start_time = time.time()
        while time.time() - start_time < duration:
            if check_for_exit():
                return
            time.sleep(0.1)  # Check for exit every 0.1 seconds
    except pygame.error as e:
        print(f"Error displaying image: {e}")

def simulate_flash():
    white = (255, 255, 255)
    screen.fill(white)
    pygame.display.flip()
    time.sleep(config.flash_time)
    # clear_screen()

def capture_current_photos():
    with PiCamera() as camera:
        camera.resolution = config.camera_resolution
        camera.iso = config.camera_iso

        for photo_number in range(1, config.num_images + 1):
            try:
                clear_screen()
                camera.hflip = True
                camera.start_preview()
                time.sleep(config.camera_warmup_time)
                camera.stop_preview()
                # camera.hflip = False

                simulate_flash()
                snap_sound.play()

                photo_path = os.path.join(config.current_photos_path, f"photo{photo_number}.jpg")
                camera.capture(photo_path)
                print(f"Photo {photo_number} captured and saved to {photo_path}")

                show_image_for_duration(photo_path, config.image_display_time)
                clear_screen()

                if photo_number < config.num_images:
                    time.sleep(config.photo_interval)
            except Exception as e:
                print(f"An error occurred during photo {photo_number}: {e}")
                break
            finally:
                time.sleep(config.post_capture_delay)

def manage_photo_sets():
    for i in range(config.num_photo_sets, 0, -1):
        old_set_path = os.path.join(config.recent_sets_path, f"set{i}")
        new_set_path = os.path.join(config.recent_sets_path, f"set{i + 1}")

        if os.path.exists(old_set_path):
            if i == config.num_photo_sets:
                shutil.rmtree(old_set_path)
            else:
                os.rename(old_set_path, new_set_path)

    new_set_path = os.path.join(config.recent_sets_path, "set1")
    os.makedirs(new_set_path, exist_ok=True)

    for photo_number in range(1, config.num_images + 1):
        current_photo_path = os.path.join(config.current_photos_path, f"photo{photo_number}.jpg")
        new_photo_path = os.path.join(new_set_path, f"photo{photo_number}.jpg")
        shutil.copy(current_photo_path, new_photo_path)

def display_current_set():
    for _ in range(config.num_loops_per_set):  # Looping through the current set
        for photo_number in range(1, config.num_images + 1):
            current_photo_path = os.path.join(config.current_photos_path, f"photo{photo_number}.jpg")
            if os.path.exists(current_photo_path):
                show_image_for_duration(current_photo_path, config.photo_display_duration)
            else:
                print(f"Photo not found: {current_photo_path}")

            if check_for_exit():
                return  # Exit the function if ESC is pressed

def display_photo_sets():
    for set_number in range(1, config.num_photo_sets + 1):
        set_path = os.path.join(config.recent_sets_path, f"set{set_number}")
        if os.path.exists(set_path):
            for _ in range(config.num_loops_per_set):
                for photo_number in range(1, config.num_images + 1):
                    photo_path = os.path.join(set_path, f"photo{photo_number}.jpg")
                    if os.path.exists(photo_path):
                        show_image_for_duration(photo_path, config.photo_display_duration)
                    if check_for_exit():
                        return  # Exit the function if ESC is pressed

def check_for_exit():
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            return True
    return False

# Main execution
try:
    print("Starting photo capture")
    capture_current_photos()

    print("Showing processing image")
    show_image_for_duration(config.processing_image_path, 3)

    print("Managing photo sets")
    manage_photo_sets()
    
    print("Showing current photo set") # Displays the current images as a simulated GIF
    display_current_set()

    # print("Displaying photo sets") # Displays the recent sets of photos
    # display_photo_sets() 

    print("Waiting for exit")
    while True:
        if check_for_exit():
            break
        time.sleep(0.1)  # Check for exit every 0.1 seconds

except KeyboardInterrupt:
    print("Program interrupted by user")
except Exception as e:
    print(f"An error occurred: {e}")

pygame.quit()