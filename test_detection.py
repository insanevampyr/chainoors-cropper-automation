import vision

v = vision.Vision()
screen = v.capture_screen()

print("VISION FILE:", vision.__file__)
print("COUNTER FULL:", v.is_counter_full(screen))