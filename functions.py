#functions.py

import os
import pyautogui
import pyttsx3
import speech_recognition as sr
import win32gui #type:ignore
import win32con #type:ignore
import time
import datetime
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import POINTER, cast
import screen_brightness_control as sbc
import tkinter as tk
from tkinter import messagebox
import webbrowser
import cv2
import platform
import subprocess
import threading
import requests

pyautogui.PAUSE = 0.5
pyautogui.FAILSAFE = True

API_KEY = "2c2114b163e86b1962bc9451303e7c32"

def active_windows():
    """Returns a list of tuples (hwnd, window_title) for all visible windows with titles."""
    windows = []
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title:  # Ignore windows without a title
                windows.append((title))
        return True
    win32gui.EnumWindows(callback, None)
    speak(windows)

def close_window_by_title(target_title):
    """Close a visible window by its title (exact match)."""
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title == target_title:
                try:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    print(f"Closed window: {title}")
                except Exception as e:
                    print(f"Failed to close {title}: {e}")
        return True

    win32gui.EnumWindows(callback, None)
    # speak(target_title+ "is closed")

def close_all_except(title_to_keep):
    """Close all visible windows except the one with the given title."""
    def callback(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            title = win32gui.GetWindowText(hwnd)
            if title and title != title_to_keep:
                try:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    print(f"Closed window: {title}")
                except Exception as e:
                    print(f"Failed to close {title}: {e}")
        return True

    win32gui.EnumWindows(callback, None)
    # speak(f"except {title_to_keep} is closed")

def close_window():
    """Close active window instantly."""
    pyautogui.hotkey('alt', 'f4')
    # speak("top window is closed")

def close_all_windows():
    def enum_handler(hwnd, _):
        # Ignore invisible, minimized, or system windows
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        if not title:
            return
        if title in ["Program Manager", "Task Manager", "Settings"]:
            return

        # Try closing the window
        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
        except:
            pass

    win32gui.EnumWindows(enum_handler, None)

def minimize_window():
    """Minimize the active window."""
    pyautogui.hotkey('win', 'down')
    # speak("Window minimized")

def maximize_window():
    """Maximize the active window."""
    pyautogui.hotkey('win', 'up')
    # speak("window maximized")

def reload(): #used to refresh the window
    pyautogui.hotkey('ctrl', 'r')

def snap_left():
    """Snap window to left."""
    pyautogui.hotkey('win', 'left')
    # speak("window snapped to left")

def snap_right():
    """Snap window to right."""
    pyautogui.hotkey('win', 'right')
    # speak("window snapped to right")

def type_or_search(text):
    time.sleep(0.5)
    pyautogui.click()   # ensure focus
    pyautogui.write(text, interval=0.05)

def mute_volume(): #for toggling volume
    pyautogui.press("volumemute")

def press_key(key):
    pyautogui.press(key)

def click_right():
    pyautogui.press("right")

def click_left():
    pyautogui.press("left")

def click_up():
    pyautogui.press("up")

def click_down():
    pyautogui.press("down")

def click_win():
    pyautogui.press("win")

def enter():
    pyautogui.press("enter")
    speak("Lets go")

def escape():
    pyautogui.press("esc")

def backsp():
    pyautogui.press("backspace")

def tabsp():
    pyautogui.press('tab')
    
def selectall():
    pyautogui.hotkey('ctrl','a')

def paste():
    pyautogui.hotkey('ctrl','v')
    # speak("Text is pasted")
    
def copy():
    pyautogui.hotkey('ctrl','c')

def delete():
    pyautogui.press('delete')
    
def startrecord():
    pyautogui.hotkey('win','alt', 'r')
    # speak("Recording is started")

def stoprecord():
    pyautogui.hotkey('win','alt', 'r')
    # speak("Recording is stopped")

def tab():
    pyautogui.press('tab')

def left_mouse_click():
    pyautogui.click()

def right_mouse_click():
    pyautogui.rightClick()

def move_mouse(x, y):
    pyautogui.moveTo(x, y)

# def browser_search(text):
#     open_app("chrome")
#     pyautogui.hotkey('ctrl', 'l')  # focus address/search bar
#     pyautogui.write(text, interval=0.02)
#     pyautogui.press('enter')

def set_volume(percent):
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        scalar = max(0.0, min(1.0, percent / 100.0))  # clamp 0–1
        volume.SetMasterVolumeLevelScalar(scalar, None)
        return True
    except Exception as e:
        print("Volume Error:", e)
        return False
    
def increase_volume(step=10):
    """Increase system volume by step%"""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current = volume.GetMasterVolumeLevelScalar()
        new_volume = min(current + step / 100.0, 1.0)
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        return True
    except Exception as e:
        print("Increase Volume Error:", e)
        return False

def decrease_volume(step=10):
    """Decrease system volume by step%"""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current = volume.GetMasterVolumeLevelScalar()
        new_volume = max(current - step / 100.0, 0.0)
        volume.SetMasterVolumeLevelScalar(new_volume, None)
        return True

    except Exception as e:
        print("Decrease Volume Error:", e)
        return False
    
def increase_brightness(step=10):
    """Increase brightness by step%"""
    current = sbc.get_brightness(display=0)[0]
    sbc.set_brightness(min(current + step, 100))

def decrease_brightness(step=10):
    """Decrease brightness by step%"""
    current = sbc.get_brightness(display=0)[0]
    sbc.set_brightness(max(current - step, 0))

def set_brightness(percent):
    sbc.set_brightness(percent)
    # speak(f"Brightness set to {percent}")

def is_window_visible(app_name):
    """Check if a window containing the app name is visible."""
    def callback(hwnd, name_list):
        title = win32gui.GetWindowText(hwnd).lower()
        if name_list[0] in title and win32gui.IsWindowVisible(hwnd):
            name_list.append(hwnd)
        return True

    result = [app_name.lower()]
    win32gui.EnumWindows(callback, result)
    return result[1] if len(result) > 1 else None

def wait_for_window(app_name, timeout=10):
    """Wait until window appears."""
    start = time.time()
    while time.time() - start < timeout:
        hwnd = is_window_visible(app_name)
        if hwnd:
            return True
        time.sleep(0.5)
    return False

def open_app(app_name):

    pyautogui.press('win')
    pyautogui.write(app_name, interval=0.1)
    pyautogui.press('enter')
    if wait_for_window(app_name):
        speak(f"{app_name} is ready to watch.")
    else:
        pass
        # speak(f"{app_name} is opened, but window not detected.")

def switch_tab(direction="next"):
    if direction == "next":
        pyautogui.hotkey('ctrl', 'tab')
        # speak("switched to next window")
    elif direction == "previous":
        pyautogui.hotkey('ctrl', 'shift', 'tab')
        # speak("switched to previous window")

def switch_window(direction="next"):
    if "next" in direction or "previous" in direction:
        pyautogui.hotkey('alt', 'tab')
        # speak("switched to next window")
    elif direction == "previous":
        pyautogui.hotkey('alt', 'shift', 'tab')
        # speak("switched to previous window")

def show_desktop():
    pyautogui.hotkey('win', 'd')
    return True

def open_new_tab():
    pyautogui.hotkey('ctrl', 't')
    # speak("new tab is ready")

def close_tab():
    """Close the current tab."""
    pyautogui.hotkey('ctrl', 'w')
    # speak("tab is closed")

def wifi_off():
    os.system("netsh interface set interface Wi-Fi disabled")
    return True

def wifi_on():
    os.system("netsh interface set interface Wi-Fi enabled")
    return True

def Quickpanel():
    pyautogui.hotkey('win','a')
    return True

def ask_yes_no(text):
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    response = messagebox.askyesno("Confirm", f"Do you want to {text}?")
    root.destroy()
    return response

def shutdown():
    if(ask_yes_no("shutdown")):
        os.system("shutdown /s /t 0")
        # speak("shutting down....")

def restart():
    if(ask_yes_no("restart")):
        os.system("shutdown /r /t 0")
        # speak("restarting....")

def lockscreen():
    pyautogui.hotkey("win","l")
    return True

def open_web_request(url: str, browser_name = "chrome"):
    browser_name = browser_name.lower().strip()
    # Map browsers to system names
    browser_paths = {"chrome": "chrome","edge": "msedge","brave": "brave"}
    if browser_name in browser_paths:
        try:
            browser = webbrowser.get(browser_paths[browser_name])
            browser.open(url)
            return
        except: pass  # If the specific browser isn't registered, fall back below           
    webbrowser.open(url) # Fallback: open in system default browser

def take_photo():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        return 0

    time.sleep(1)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return 0

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"photo_{timestamp}.jpg"
    file_path = os.path.abspath(file_name)

    cv2.imwrite(file_path, frame)

    os.startfile(file_path)

    return 1

last_screenshot_path = None  # global variable to remember last screenshot

def take_screenshot():
    global last_screenshot_path
    now = datetime.datetime.now()
    filename = f"screenshot_{now.strftime('%Y%m%d_%H%M%S')}.png"
    filepath = os.path.join(os.getcwd(), filename)
    
    image = pyautogui.screenshot()
    image.save(filepath)
    last_screenshot_path = filepath
    open_file_explorer(filepath)
    return filepath

def reopen_last_screenshot():
    if last_screenshot_path and os.path.exists(last_screenshot_path):
        open_file_explorer(last_screenshot_path)
        return 1
    else:
        return 0

def open_file_explorer(filepath):
    system = platform.system()
    if system == "Windows":
        os.startfile(filepath)
    elif system == "Darwin":
        subprocess.run(["open", filepath])
    else:
        subprocess.run(["xdg-open", filepath])

def speak(text,on_complete=None):
    def run():
        try:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
            if on_complete:
                on_complete()
        except Exception as e:
            print("Runtime Error", e)

    threading.Thread(target=run, daemon=True).start()

def get_system_location():
    try:
        response = requests.get("https://ipinfo.io/json")
        data = response.json()

        city = data.get("city")
        region = data.get("region")
        country = data.get("country")
        loc = data.get("loc")  # "lat,long"

        latitude, longitude = loc.split(",")

        print("City:", city)
        print("Region:", region)
        print("Country:", country)
        print("Latitude:", latitude)
        print("Longitude:", longitude)

        return city

    except Exception as e:
        print("Error:", e)
        return None
    
def get_weather(city = get_system_location()):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if response.status_code != 200:
            print("Sorry, I could not find that city.")
            return False
        return data

    except Exception as e:
        print("There was an error fetching the weather.")