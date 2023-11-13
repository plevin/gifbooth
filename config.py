# config.py

# Camera settings
camera_resolution = (960, 540)
camera_iso = 1000

# Screen Settings
screen_width = 1920  # Adjust as per your screen resolution
screen_height = 1080  # Adjust as per your screen resolution

# Sound and image file locations
snap_path = '/home/plevin/gifbooth/click.wav'
processing_image_path = '/home/plevin/gifbooth/start_images/processing.png'
start_image_path = '/home/plevin/gifbooth/start_images/stooges.jpg'

# Image storage settings
images_path = '/home/plevin/gifbooth/gbooth_temp'  # Ensure this directory exists
current_photos_path = '/home/plevin/gifbooth/gbooth_temp'
recent_sets_path = '/home/plevin/gifbooth/gbooth_recent'
archive_path = '/home/plevin/gifbooth/gbooth_archive'
num_images = 5  # Number of images to keep

# Delay Times (in seconds)
camera_warmup_time = .5    # Time for camera warm-up
image_display_time = .25    # Time to display the captured image
post_capture_delay = .1    # Delay after displaying captured image
flash_time = 0.1          # Duration of the flash in seconds
photo_display_duration = .15 # Duration of simulated gif after taking the 5-pics

# Sequential Photo Capture Settings
num_photos = 5            # Number of photos to take in a sequence
photo_interval = .1        # Interval between photos in seconds
num_loops = 5              # Number of times the 'gif' loops after taking the 5-pics
num_photo_sets = 5         # the number of photo sets you want to keep
num_loops_per_set = 3      # the number of loops for a set of gifs

# GIF Creation Settings
gif_frame_duration = 500  # Duration for each frame in the GIF (in milliseconds)
