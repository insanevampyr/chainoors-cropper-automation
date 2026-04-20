import time

import pyautogui

import config


pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.0


def click_point(point, delay=config.POST_CLICK_DELAY):
    x, y = point
    pyautogui.moveTo(x, y, duration=0.1)
    pyautogui.click()
    time.sleep(delay)


def click_send(point):
    click_point(point, delay=config.POST_SEND_DELAY)


def click_charge(point):
    click_point(point, delay=config.POST_CHARGE_DELAY)


def wait_for_next_cycle(started_at):
    elapsed = time.time() - started_at
    remaining = max(0.0, config.CYCLE_SECONDS - elapsed)
    time.sleep(remaining)
