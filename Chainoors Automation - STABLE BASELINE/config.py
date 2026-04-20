from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"

# === CALIBRATION MODE START ===
CALIBRATION_MODE = True
# === CALIBRATION MODE END ===

CYCLE_SECONDS = 120
POST_CLICK_DELAY = 0.35
POST_SEND_DELAY = 0.8
POST_CHARGE_DELAY = 1.0

COUNTER_REGION = (900, 350, 420, 90)
LEFT_PANEL_REGION = (700, 350, 900, 650)
DESTINATION_PANEL_REGION = (560, 255, 445, 285)
SEND_BUTTON_REGION = (855, 865, 90, 70)
ALL_BUTTON_REGION = (1285, 845, 130, 70)
CHARGE_BUTTON_REGION = (1440, 390, 150, 70)

COUNTER_TESSERACT_CONFIG = "--psm 7 -c tessedit_char_whitelist=0123456789/"
COUNTER_OCR_SCALE = 3

SLOT_MIN_WIDTH = 55
SLOT_MAX_WIDTH = 120
SLOT_MIN_HEIGHT = 55
SLOT_MAX_HEIGHT = 120
SLOT_MIN_AREA = 3600
SLOT_MAX_AREA = 12000
SLOT_PADDING = 6

GOLD_HSV_LOW = (12, 110, 150)
GOLD_HSV_HIGH = (40, 255, 255)

BUTTON_MATCH_THRESHOLD = 0.88
ANIMAL_FEED_MATCH_THRESHOLD = 0.80
CROP_MATCH_THRESHOLD = 0.70
GOLD_SLOT_DENSITY_THRESHOLD = 0.15
FILLED_SLOT_MATCH_THRESHOLD = 0.82
FILLED_SLOT_REQUIRED_COUNT = 12

TEMPLATE_PATHS = {
    "animal_feed": ASSETS_DIR / "animal_feed.png",
    "counter_full_12_12": ASSETS_DIR / "counter_full_12_12.png",
    "crop": ASSETS_DIR / "crop.png",
    "feed_chicken": ASSETS_DIR / "feed_chicken.png",
    "feed_cow": ASSETS_DIR / "feed_cow.png",
    "feed_fuzzy": ASSETS_DIR / "feed_fuzzy.png",
    "feed_pig": ASSETS_DIR / "feed_pig.png",
    "feed_pumpkin_pig": ASSETS_DIR / "feed_pumpkin_pig.png",
    "feed_deer": ASSETS_DIR / "feed_deer.png",
    "filled_destination_slot": ASSETS_DIR / "filled_destination_slot.png",
    "send": ASSETS_DIR / "send.png",
    "all": ASSETS_DIR / "all.png",
    "charge": ASSETS_DIR / "charge.png",
}
