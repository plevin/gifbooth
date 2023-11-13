import pygame
import time
import os
from picamera import PiCamera
import config

# Initialize Pygame and create a window
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((config.screen_width, config.screen_height), pygame.FULLSCREEN)
pygame.display.set_caption('Photobooth')

# Load sounds and images
print("Loading sounds and images...")
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
        time.sleep(duration)
    except pygame.error as e:
        print(f"Error displaying image: {e}")

def simulate_flash():
    white = (255, 255, 255)
    screen.fill(white)
    pygame.display.flip()
    time.sleep(config.flash_time)
    # clear_screen()

def manage_images_sequence():
    # Add logic for managing images here
    pass

def capture_sequence():
    with PiCamera() as camera:
        camera.resolution = config.camera_resolution
        camera.iso = config.camera_iso

        for photo_number in range(1, config.num_photos + 1):
            try:
                clear_screen()
                camera.hflip = True
                camera.start_preview()
                time.sleep(config.camera_warmup_time)
                camera.stop_preview()
                snap_sound.play()

                
                photo_path = os.path.join(config.images_path, f"photo{photo_number}.jpg")
                camera.capture(photo_path)
                print(f"Photo {photo_number} captured and saved to {photo_path}")
                simulate_flash()

                show_image_for_duration(photo_path, config.image_display_time)
                # clear_screen()

                if photo_number < config.num_photos:
                    time.sleep(config.photo_interval)
            except Exception as e:
                print(f"An error occurred during photo {photo_number}: {e}")
                break
            finally:
                time.sleep(config.post_capture_delay)
    manage_images_sequence()

def display_photos_in_loop():
    for _ in range(config.num_loops):  # Number of times to loop through the photos
        for i in range(1, config.num_images + 1):  # Assuming photos are named photo1.jpg to photo5.jpg
            photo_path = os.path.join(config.images_path, f"photo{i}.jpg")
            show_image_for_duration(photo_path, config.photo_display_duration)

def display_processing_image_and_wait():
    show_image_for_duration(config.processing_image_path, 3)

    # Wait for ESC key press to exit
    # while True:
    #    if check_for_exit():
    #        break

def check_for_exit():
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            return True
    return False

# Main execution
try:
    capture_sequence()
    display_processing_image_and_wait()
    display_photos_in_loop()
    
except KeyboardInterrupt:
    print("Program interrupted by user")

pygame.quit()
