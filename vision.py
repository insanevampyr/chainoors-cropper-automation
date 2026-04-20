import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import cv2
import mss
import numpy as np
import pytesseract

import config


@dataclass(frozen=True)
class SlotCandidate:
    rect: tuple[int, int, int, int]
    center: tuple[int, int]
    top: int
    feed_score: float
    crop_score: float


class Vision:
    def __init__(self):
        print(f"VISION CONFIG FILE: {config.__file__}")
        print(f"VISION CONFIG COUNTER_REGION: {config.COUNTER_REGION}")
        self._sct = mss.mss()
        self.templates = {
            name: self._load_template(path)
            for name, path in config.TEMPLATE_PATHS.items()
        }
        self.feed_template_names = [
            "feed_chicken",
            "feed_cow",
            "feed_fuzzy",
            "feed_pig",
            "feed_pumpkin_pig",
            "feed_deer",
        ]
        if self.templates["crop"] is None:
            raise FileNotFoundError("Missing required template: crop.png")
        if self.templates["counter_full_12_12"] is None:
            raise FileNotFoundError("Missing required template: counter_full_12_12.png")
        if self.templates["filled_destination_slot"] is None:
            raise FileNotFoundError("Missing required template: filled_destination_slot.png")
        for template_name in self.feed_template_names:
            if self.templates[template_name] is None:
                raise FileNotFoundError(f"Missing required template: {config.TEMPLATE_PATHS[template_name].name}")

    def _load_template(self, path: Path):
        if not path.exists():
            return None
        image = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Could not read template: {path}")
        return image

    def capture_screen(self):
        monitor = self._sct.monitors[1]
        frame = np.array(self._sct.grab(monitor))
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    # === CALIBRATION MODE START ===
    def save_calibration_debug(self, screen):
        logs_dir = Path(__file__).resolve().parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        full_screen_path = logs_dir / f"full_screen_{timestamp}.png"
        overlay_path = logs_dir / f"debug_overlay_{timestamp}.png"

        cv2.imwrite(str(full_screen_path), screen)

        overlay = screen.copy()
        self._draw_region(overlay, config.COUNTER_REGION, "COUNTER_REGION", (0, 255, 255))
        self._draw_region(overlay, config.LEFT_PANEL_REGION, "CROP_REGION", (0, 255, 0))
        self._draw_region(overlay, config.SEND_BUTTON_REGION, "SEND_BUTTON", (255, 0, 0))
        self._draw_region(overlay, config.ALL_BUTTON_REGION, "ALL_BUTTON", (255, 165, 0))
        self._draw_region(overlay, config.CHARGE_BUTTON_REGION, "CHARGE_BUTTON", (255, 0, 255))

        self._draw_click_point(overlay, config.SEND_BUTTON_REGION, "SEND_BUTTON")
        self._draw_click_point(overlay, config.ALL_BUTTON_REGION, "ALL_BUTTON")
        self._draw_click_point(overlay, config.CHARGE_BUTTON_REGION, "CHARGE_BUTTON")

        cv2.imwrite(str(overlay_path), overlay)

        cv2.imwrite(str(logs_dir / "counter_crop.png"), self._crop_region(screen, config.COUNTER_REGION))
        cv2.imwrite(str(logs_dir / "crop_region.png"), self._crop_region(screen, config.LEFT_PANEL_REGION))
        cv2.imwrite(str(logs_dir / "send_button.png"), self._crop_region(screen, config.SEND_BUTTON_REGION))
        cv2.imwrite(str(logs_dir / "all_button.png"), self._crop_region(screen, config.ALL_BUTTON_REGION))
        cv2.imwrite(str(logs_dir / "charge_button.png"), self._crop_region(screen, config.CHARGE_BUTTON_REGION))

        send_point = self._region_center(config.SEND_BUTTON_REGION)
        all_point = self._region_center(config.ALL_BUTTON_REGION)
        charge_point = self._region_center(config.CHARGE_BUTTON_REGION)

        print(f"COUNTER_REGION = {config.COUNTER_REGION}")
        print(f"CROP_REGION = {config.LEFT_PANEL_REGION}")
        print(f"SEND_BUTTON = {send_point}")
        print(f"ALL_BUTTON = {all_point}")
        print(f"CHARGE_BUTTON = {charge_point}")

    def _draw_region(self, image, region, label, color):
        x, y, w, h = region
        cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
        cv2.putText(
            image,
            label,
            (x, max(20, y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )

    def _draw_click_point(self, image, region, label):
        cx, cy = self._region_center(region)
        cv2.circle(image, (cx, cy), 8, (0, 0, 255), -1)
        cv2.putText(
            image,
            f"{label}_CLICK",
            (cx + 10, cy - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )

    def _crop_region(self, screen, region):
        x, y, w, h = region
        return screen[y : y + h, x : x + w]

    def _region_center(self, region):
        x, y, w, h = region
        return x + w // 2, y + h // 2
    # === CALIBRATION MODE END ===

    def read_counter(self, screen):
        region = config.COUNTER_REGION
        value = self._read_counter_from_templates(screen)
        if value is not None:
            return value
        # Fallback: OCR is only used when template or digit detection is unavailable.
        return self._read_counter_with_ocr(screen, region)

    def _read_counter_from_templates(self, screen):
        return None

    def _read_counter_with_ocr(self, screen, region):
        x, y, w, h = region
        print(f"COUNTER OCR REGION: {region}")
        roi = screen[y : y + h, x : x + w]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        scaled = cv2.resize(
            gray,
            None,
            fx=config.COUNTER_OCR_SCALE,
            fy=config.COUNTER_OCR_SCALE,
            interpolation=cv2.INTER_CUBIC,
        )

        variants = [
            cv2.threshold(scaled, 180, 255, cv2.THRESH_BINARY)[1],
            cv2.threshold(scaled, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
        ]

        attempted_texts = []
        for variant in variants:
            text = pytesseract.image_to_string(variant, config=config.COUNTER_TESSERACT_CONFIG).strip()
            attempted_texts.append(text)
            match = re.search(r"(\d{1,2})\s*/\s*12", text)
            if not match:
                continue
            value = int(match.group(1))
            if value < 0 or value > 12:
                raise RuntimeError(f"Counter value out of range: {value}")
            return value

        raise RuntimeError(
            f"Could not read counter from OCR. Texts={attempted_texts!r}, Region={region!r}"
        )

    def find_button_center(self, screen, template_name, region, threshold=config.BUTTON_MATCH_THRESHOLD):
        template = self.templates.get(template_name)
        if template is None:
            raise FileNotFoundError(f"Missing template asset: {config.TEMPLATE_PATHS[template_name]}")

        x, y, w, h = region
        roi = screen[y : y + h, x : x + w]
        result = cv2.matchTemplate(roi, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, location = cv2.minMaxLoc(result)
        if score < threshold:
            raise RuntimeError(f"Could not locate {template_name} button. Score={score:.3f}")

        center_x = x + location[0] + template.shape[1] // 2
        center_y = y + location[1] + template.shape[0] // 2
        return center_x, center_y

    def is_counter_full(self, screen):
        x, y, w, h = config.COUNTER_REGION
        roi = screen[y : y + h, x : x + w]

        logs_dir = Path(__file__).resolve().parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        cv2.imwrite(str(logs_dir / "counter_region_raw.png"), roi)

        expand_x = 120
        expand_y = 60
        screen_height, screen_width = screen.shape[:2]
        expanded_x1 = max(0, x - expand_x)
        expanded_y1 = max(0, y - expand_y)
        expanded_x2 = min(screen_width, x + w + expand_x)
        expanded_y2 = min(screen_height, y + h + expand_y)
        expanded_region = (
            expanded_x1,
            expanded_y1,
            expanded_x2 - expanded_x1,
            expanded_y2 - expanded_y1,
        )
        expanded_roi = screen[expanded_y1:expanded_y2, expanded_x1:expanded_x2]
        cv2.imwrite(str(logs_dir / "counter_region_expanded.png"), expanded_roi)
        print(
            f"COUNTER DEBUG: raw_region={(x, y, w, h)} "
            f"expanded_region={expanded_region}"
        )
        try:
            counter_value = self.read_counter(screen)
            print(f"COUNTER OCR VALUE: {counter_value}/12")
            return counter_value == 12
        except RuntimeError as exc:
            print(f"COUNTER OCR ERROR: {exc}")
            return False

    def find_valid_crop_slots(self, screen):
        x0, y0, w, h = config.LEFT_PANEL_REGION
        roi = screen[y0 : y0 + h, x0 : x0 + w]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array(config.GOLD_HSV_LOW), np.array(config.GOLD_HSV_HIGH))
        kernel = np.ones((3, 3), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        self._save_left_panel_debug_images(roi, mask)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for contour in contours:
            x, y, cw, ch = cv2.boundingRect(contour)
            area = cw * ch
            if cw < config.SLOT_MIN_WIDTH or cw > config.SLOT_MAX_WIDTH:
                continue
            if ch < config.SLOT_MIN_HEIGHT or ch > config.SLOT_MAX_HEIGHT:
                continue
            if area < config.SLOT_MIN_AREA or area > config.SLOT_MAX_AREA:
                continue

            rect = self._expand_rect((x, y, cw, ch), roi.shape[1], roi.shape[0])
            slot_image = roi[rect[1] : rect[1] + rect[3], rect[0] : rect[0] + rect[2]]
            slot_mask = mask[rect[1] : rect[1] + rect[3], rect[0] : rect[0] + rect[2]]
            gold_density = float(np.count_nonzero(slot_mask)) / float(slot_mask.size)
            if gold_density < config.GOLD_SLOT_DENSITY_THRESHOLD:
                continue
            crop_score = self._template_score(slot_image, self.templates.get("crop"))
            max_feed_template = None
            max_feed_score = 0.0
            for template_name in self.feed_template_names:
                score = self._template_score(slot_image, self.templates.get(template_name))
                if score > max_feed_score:
                    max_feed_score = score
                    max_feed_template = template_name

            decision = "accepted"

            reject_as_feed = (
                max_feed_score >= 0.85
                or (max_feed_score >= 0.70 and max_feed_score >= crop_score)
            )

            if reject_as_feed:
                decision = "rejected_feed"
                print(
                    f"CANDIDATE rect={(x0 + rect[0], y0 + rect[1], rect[2], rect[3])} "
                    f"crop_score={crop_score:.3f} max_feed_score={max_feed_score:.3f} "
                    f"max_feed_template={max_feed_template} decision={decision}"
                )
                continue

            if crop_score < 0.70:
                decision = "rejected_low_crop"
                print(
                    f"CANDIDATE rect={(x0 + rect[0], y0 + rect[1], rect[2], rect[3])} "
                    f"crop_score={crop_score:.3f} max_feed_score={max_feed_score:.3f} "
                    f"max_feed_template={max_feed_template} decision={decision}"
                )
                continue

            print(
                f"CANDIDATE rect={(x0 + rect[0], y0 + rect[1], rect[2], rect[3])} "
                f"crop_score={crop_score:.3f} max_feed_score={max_feed_score:.3f} "
                f"max_feed_template={max_feed_template} decision={decision}"
            )

            abs_rect = (x0 + rect[0], y0 + rect[1], rect[2], rect[3])
            candidates.append(
                SlotCandidate(
                    rect=abs_rect,
                    center=(abs_rect[0] + abs_rect[2] // 2, abs_rect[1] + abs_rect[3] // 2),
                    top=abs_rect[1],
                    feed_score=max_feed_score,
                    crop_score=crop_score,
                )
            )

        return self._dedupe_and_sort(candidates)

    def _expand_rect(self, rect, max_width, max_height):
        x, y, w, h = rect
        pad = config.SLOT_PADDING
        left = max(0, x - pad)
        top = max(0, y - pad)
        right = min(max_width, x + w + pad)
        bottom = min(max_height, y + h + pad)
        return left, top, right - left, bottom - top

    def _save_left_panel_debug_images(self, roi, mask):
        logs_dir = Path(__file__).resolve().parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        cv2.imwrite(str(logs_dir / "left_panel_raw.png"), roi)
        cv2.imwrite(str(logs_dir / "left_panel_mask.png"), mask)

    def _template_score(self, image, template):
        if template is None:
            return 0.0
        if image.shape[0] < template.shape[0] or image.shape[1] < template.shape[1]:
            return 0.0
        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, score, _, _ = cv2.minMaxLoc(result)
        return float(score)

    def _dedupe_and_sort(self, candidates):
        kept = []
        for candidate in sorted(candidates, key=lambda item: (item.top, item.rect[0])):
            if any(self._overlaps(candidate.rect, existing.rect) for existing in kept):
                continue
            kept.append(candidate)
        return kept

    def _overlaps(self, a, b):
        ax1, ay1, aw, ah = a
        bx1, by1, bw, bh = b
        ax2, ay2 = ax1 + aw, ay1 + ah
        bx2, by2 = bx1 + bw, by1 + bh
        return ax1 < bx2 and ax2 > bx1 and ay1 < by2 and ay2 > by1
