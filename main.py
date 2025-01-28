import os
import random

IsDebug = False  # REDUCES FPS A LOT!
CROSSHAIR_CHECK = False
MOUSEMOVE_CHECK = True
RCLICK_CHECK = True
THRESHOLD = 80

import time
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from pynput import mouse
import numpy as np
import cv2
import mss
import win32api
import win32con
import keyboard
from skimage.metrics import structural_similarity as ssim
import sys

pygame.init()
pygame.mixer.init()

def resource_path(relative_path):
    """Get the absolute path to a resource, considering if it's bundled with PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

sound_charge = pygame.mixer.Sound(resource_path("sounds/charge.mp3"))
sound_shot = pygame.mixer.Sound(resource_path("sounds/shot.mp3"))

print("SCRIPT STARTED")

with mss.mss() as sct:
    # Get the monitor size
    monitor = sct.monitors[1]
    width = monitor["width"]
    height = monitor["height"]
    #Custom width
    # width = 1920

    radius = ((width // 120) * 2 // 2)
    scan_x = (width - radius) // 2
    scan_y = (height - radius) // 2

def drawDiffImage(current_img, gray_img, prev_img, percentage, real_fps):
    diff_img = cv2.absdiff(gray_img, prev_img)

    # Threshold the difference image to create a binary mask of the difference pixels
    _, thresh = cv2.threshold(diff_img, 5, 255, cv2.THRESH_BINARY)

    # Create a new image where the difference pixels are displayed in red
    red_img = np.zeros_like(img)
    red_img[:, :, 2] = thresh

    x = 10
    red_img = cv2.resize(red_img, (0, 0), fx=x, fy=x, interpolation=cv2.INTER_NEAREST)
    current_img = cv2.resize(current_img, (0, 0), fx=x, fy=x, interpolation=cv2.INTER_NEAREST)



    combined_img = cv2.hconcat([current_img, red_img])

    text = f"FPS: {round(real_fps, 1)}"
    cv2.putText(combined_img, text, (10, red_img.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 255, 0), 2)

    text = f"{round(percentage, 1)}%"
    cv2.putText(combined_img, text, (red_img.shape[0] + 10, red_img.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (0, 0, 255), 2)

    # Display the resulting image
    cv2.imshow("Image / Red Difference", combined_img)
    cv2.waitKey(1)


def drawImage(img):
    x = 4
    img = cv2.resize(img, (0, 0), fx=x, fy=x, interpolation=cv2.INTER_NEAREST)
    cv2.imshow("Screen", img)
    cv2.waitKey(1)

previous_click_time = 0

def on_click(x, y, button, pressed):
    global previous_click_time

    if button == mouse.Button.right and pressed:
        previous_click_time = time.time()

listener = mouse.Listener(on_click=on_click)
listener.start()


channel = pygame.mixer.Channel(0)


# Create a monitor object
with mss.mss() as sct:

    # Set the monitor to capture a specific area of the screen
    monitor = {"top": scan_y, "left": scan_x, "width": radius, "height": radius}

    # Initialize the previous image as None
    prev_img = None
    chargeFlag = False

    frame_count = 0
    start_time = time.time()

    prev_pos = None
    last_move_time = time.time()

    last_trigger_time = 0

    # Continuously monitor the specified area for changes
    while True:
        current_time = time.time()
        if current_time - last_trigger_time < 1 or win32api.GetKeyState(win32con.VK_RBUTTON) >= 0:
            continue

        # Capture a screenshot of the specified area
        img = np.array(sct.grab(monitor))
        # Convert the image to grayscale
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        frame_count += 1
        elapsed_time = time.time() - start_time
        if elapsed_time <= 0:
            elapsed_time = 1
        real_fps = frame_count / elapsed_time

        if elapsed_time > 1:
            frame_count = 0
            start_time = time.time()

        curr_pos = mouse.Controller().position
        if curr_pos != prev_pos:
            prev_pos = curr_pos
            last_move_time = time.time()

        if prev_img is None:
            prev_img = gray_img.copy()
            continue

        y = 0
        x = 0
        h, w = radius, radius
        score, _ = ssim(gray_img[y:y + h, x:x + w], prev_img[y:y + h, x:x + w], full=True)

        # Calculate the percentage similarity between the previous and current image
        percent_sim = score * 100

        if IsDebug:
            drawDiffImage(img, gray_img, prev_img, percent_sim, real_fps)

        prev_img = gray_img.copy()



        center_pixel_x = radius // 2
        center_pixel_y = radius // 2
        #print(f"{radius}, {center_pixel_x}, {center_pixel_y}")

        # if CROSSHAIR_CHECK and not (all(img[center_pixel_x, center_pixel_y] == [0, 0, 0, 255]) and
        #                             all(img[0, center_pixel_y] == [0, 0, 0, 255]) and
        #                             all(img[radius - 1, center_pixel_y] == [0, 0, 0, 255]) and
        #                             all(img[center_pixel_x, 0] == [0, 0, 0, 255]) and
        #                             all(img[center_pixel_x, radius - 1] == [0, 0, 0, 255])):
        #     continue


        # Check if the mouse has been inactive for 500 milliseconds
        if MOUSEMOVE_CHECK and time.time() - last_move_time < 0.2:
            continue


        time_since_last_click = time.time() - previous_click_time
        if RCLICK_CHECK and time_since_last_click > 0 and time_since_last_click < 0.1:  # check if it has been more than 2 seconds since the last click
            continue

        if keyboard.is_pressed('f'):

            # print(f"1) {img[center_pixel_x, center_pixel_y]}")
            # print(f"2) {img[0, center_pixel_y]}")
            # print(f"3) {img[radius - 1, center_pixel_y]}")
            # print(f"4) {img[center_pixel_x, 0]}")
            # print(f"5) {img[center_pixel_x, radius - 1]}")
            # print("f")
            # print(all(img[center_pixel_x, center_pixel_y] == [0, 0, 0, 255]) and
            #                         all(img[0, center_pixel_y] == [0, 0, 0, 255]) and
            #                         all(img[radius - 1, center_pixel_y] == [0, 0, 0, 255]) and
            #                         all(img[center_pixel_x, 0] == [0, 0, 0, 255]) and
            #                         all(img[center_pixel_x, radius - 1] == [0, 0, 0, 255]))

            if chargeFlag == False:
                chargeFlag = True
                channel = pygame.mixer.find_channel()  # Find an available channel
                if channel:  # Check if a channel is available
                    channel.play(sound_charge)

            if percent_sim < THRESHOLD:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(random.uniform(0.3, 0.31))
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                sound_shot.play()
                # time.sleep(random.uniform(0.1, 0.11))
                # win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
                chargeFlag = False
                last_trigger_time = current_time
        else:
            chargeFlag = False
