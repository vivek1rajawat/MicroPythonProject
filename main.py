# FINAL SOLDIER HEALTH MONITORING SYSTEM
# Connections EXACTLY from your final PDF

from machine import Pin, I2C, PWM
from time import sleep
import onewire, ds18x20
import ustruct

# -----------------------
# PIN CONFIG (as per PDF)
# -----------------------
I2C_SCL = 22
I2C_SDA = 21

DS18B20_PIN = 4

BUZZER_PIN = 25
RGB_R = 12
RGB_G = 13
RGB_B = 14

# Thresholds
TEMP_LIMIT = 38.0
FALL_LIMIT = 2.5  # g-force

# -----------------------
# SETUP I2C
# -----------------------
i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=400000)

# -----------------------
# OLED
# -----------------------
from ssd1306 import SSD1306_I2C
try:
    oled = SSD1306_I2C(128, 64, i2c)
    oled_ok = True
except:
    oled_ok = False

def oled_print(lines):
    if not oled_ok:
        return
    oled.fill(0)
    y = 0
    for t in lines:
        oled.text(t, 0, y)
        y += 10
    oled.show()

# -----------------------
# DS18B20 TEMP SENSOR
# -----------------------
ow = onewire.OneWire(Pin(DS18B20_PIN))
ds = ds18x20.DS18X20(ow)
roms = ds.scan()
TEMP_OK = len(roms) > 0
if TEMP_OK:
    rom = roms[0]

# -----------------------
# BUZZER PWM
# -----------------------
buzzer = PWM(Pin(BUZZER_PIN))
buzzer.duty(0)

def buzzer_on():
    buzzer.freq(1500)
    buzzer.duty(400)

def buzzer_off():
    buzzer.duty(0)

# -----------------------
# RGB LED
# -----------------------
r = PWM(Pin(RGB_R), freq=1000, duty=0)
g = PWM(Pin(RGB_G), freq=1000, duty=0)
b = PWM(Pin(RGB_B), freq=1000, duty=0)

def rgb_red():
    r.duty(1023); g.duty(0); b.duty(0)

def rgb_off():
    r.duty(0); g.duty(0); b.duty(0)

# -----------------------
# MPU6050 (Fall Detection)
# -----------------------
MPU_ADDR = 0x68
mpu_ok = MPU_ADDR in i2c.scan()

def mpu_init():
    try:
        i2c.writeto_mem(MPU_ADDR, 0x6B, b'\x00')
        sleep(0.1)
    except:
        pass

if mpu_ok:
    mpu_init()

def read_mpu():
    try:
        raw = i2c.readfrom_mem(MPU_ADDR, 0x3B, 6)
        ax = ustruct.unpack('>h', raw[0:2])[0] / 16384
        ay = ustruct.unpack('>h', raw[2:4])[0] / 16384
        az = ustruct.unpack('>h', raw[4:6])[0] / 16384
        return ax, ay, az
    except:
        return None

# -----------------------
# MAX30102 (Just presence check)
# -----------------------
MAX_ADDR = 0x57
max_ok = MAX_ADDR in i2c.scan()

# -----------------------
# MAIN LOOP
# -----------------------
print("System Started...")

while True:
    # TEMP
    if TEMP_OK:
        ds.convert_temp()
        sleep(0.7)
        temp = ds.read_temp(rom)
    else:
        temp = None

    # ACCELEROMETER
    fall_detect = False
    if mpu_ok:
        acc = read_mpu()
        if acc:
            ax, ay, az = acc
            mag = (ax*ax + ay*ay + az*az)**0.5
            if mag > FALL_LIMIT:
                fall_detect = True

    # ALERT
    alert = False
    if temp and temp >= TEMP_LIMIT:
        alert = True
    if fall_detect:
        alert = True

    if alert:
        buzzer_on()
        rgb_red()
    else:
        buzzer_off()
        rgb_off()

    # OLED DISPLAY
    oled_print([
        "Soldier Monitor",
        "Temp: {}".format(temp if temp else "--"),
        "Fall: {}".format("YES" if fall_detect else "NO"),
        "HR Sensor: {}".format("OK" if max_ok else "NO"),
        "Alert: {}".format("YES" if alert else "NO")
    ])

    # Console Print
    print("TEMP:", temp, "| FALL:", fall_detect, "| ALERT:", alert)
    sleep(1)
