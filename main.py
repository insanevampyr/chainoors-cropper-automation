import time
from pathlib import Path
import importlib

import actions
import cv2
import config
from vision import Vision

importlib.reload(config)


def execute_full_load(vision, screen, logs_dir):
    try:
        print("FULL BRANCH ENTERED")
        cv2.imwrite(str(logs_dir / "full_branch_before_all.png"), screen)
        print("ABOUT TO FIND ALL")
        x, y, w, h = config.ALL_BUTTON_REGION
        all_button = (x + w // 2, y + h // 2)
        print("FOUND ALL")
        print(f"ALL BUTTON CENTER: {all_button}")
        print("ABOUT TO CLICK ALL")
        actions.click_point(all_button)
        print("CLICKED ALL")
        time.sleep(config.POST_CLICK_DELAY)

        print("ABOUT TO CAPTURE POST-ALL SCREEN")
        screen = vision.capture_screen()
        print("CAPTURED POST-ALL SCREEN")
        cv2.imwrite(str(logs_dir / "full_branch_before_charge.png"), screen)
        print("ABOUT TO FIND CHARGE")
        x, y, w, h = config.CHARGE_BUTTON_REGION
        charge_button = (x + w // 2, y + h // 2)
        print(f"FOUND CHARGE: {charge_button}")
        print("ABOUT TO CLICK CHARGE")
        actions.click_charge(charge_button)
        print("CLICKED CHARGE")
        time.sleep(config.POST_CHARGE_DELAY)
        screen = vision.capture_screen()
        cv2.imwrite(str(logs_dir / "post_charge_screen.png"), screen)
    except Exception as exc:
        print(f"FULL BRANCH ERROR: {exc}")
    print("RETURNING FROM FULL BRANCH")


def run_cycle(vision, full_load_handled):
    logs_dir = Path(__file__).resolve().parent / "logs"
    logs_dir.mkdir(exist_ok=True)

    screen = vision.capture_screen()
    # === CALIBRATION MODE START ===
    if config.CALIBRATION_MODE:
        vision.save_calibration_debug(screen)
    # === CALIBRATION MODE END ===
    try:
        counter_full = vision.is_counter_full(screen)
    except RuntimeError:
        print("COUNTER UNREADABLE - ABORTING CYCLE")
        return full_load_handled
    if not counter_full:
        full_load_handled = False
    if counter_full:
        if full_load_handled:
            print("FULL LOAD ALREADY HANDLED")
            return full_load_handled
        execute_full_load(vision, screen, logs_dir)
        return True

    while True:
        screen = vision.capture_screen()
        # === CALIBRATION MODE START ===
        if config.CALIBRATION_MODE:
            vision.save_calibration_debug(screen)
        # === CALIBRATION MODE END ===
        try:
            counter_full = vision.is_counter_full(screen)
        except RuntimeError:
            print("COUNTER UNREADABLE - ABORTING CYCLE")
            return full_load_handled
        if not counter_full:
            full_load_handled = False
        if counter_full:
            if full_load_handled:
                print("FULL LOAD ALREADY HANDLED")
                return full_load_handled
            execute_full_load(vision, screen, logs_dir)
            return True

        slots = vision.find_valid_crop_slots(screen)
        if not slots:
            time.sleep(0.2)
            continue

        print(f"ABOUT TO CLICK SLOT: {slots[0].center}")
        actions.click_point(slots[0].center)
        print("CLICKED SLOT")

        x, y, w, h = config.SEND_BUTTON_REGION
        send_point = (x + w // 2, y + h // 2)
        print(f"ABOUT TO CLICK SEND: {send_point}")
        try:
            actions.click_send(send_point)
            print("CLICKED SEND")
        except Exception as exc:
            print(f"SEND ERROR: {exc}")
        time.sleep(config.POST_SEND_DELAY)
        screen = vision.capture_screen()
        cv2.imwrite(str(logs_dir / "post_send_screen.png"), screen)


def main():
    print(f"RUNNING MAIN FROM: {Path(__file__).resolve()}")
    print(f"MAIN CONFIG FILE: {config.__file__}")
    print(f"MAIN CONFIG COUNTER_REGION: {config.COUNTER_REGION}")
    print("CONFIG LOADED:", config.COUNTER_REGION)
    vision = Vision()
    full_load_handled = False
    while True:
        started_at = time.time()
        print("MAIN LOOP TICK")
        full_load_handled = run_cycle(vision, full_load_handled)
        actions.wait_for_next_cycle(started_at)


if __name__ == "__main__":
    main()
