import json
import math
import random
import time
import logging
from datetime import datetime

import paho.mqtt.client as mqtt

MQTT_HOST     = "your-mqtt-server"
MQTT_PORT     = 9099
MQTT_USERNAME = "username"
MQTT_PASSWORD = "password"
INTERVAL_SEC  = 30

REGION        = "JKT"
SITE_CODE     = "GW"

DEVICES = [
    ("2500-PIT-8001A",      "4jOqw3WyKxCdXALT0jeY", "A"),
    ("Wall Switchh@res-0001","M1CQkczxiqkCE95okaNO", "B"),
    ("Gas Sensorr@res-0001", "GzlFV9VuVr4Dicol0zSj", "C"),
    ("Water Leak@res-0001",  "BWbJ1kXYkq0Od2Rztlay", "D"),
]
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("WellSim")

UNIT_MAP = {
    "Batt":             "day",
    "PressureValue":    "barg",
    "ConnectionStatus": "",
    "StatusDetail":     "",
}

_tick = 0

def rnd(lo, hi, decimals=2):
    return round(random.uniform(lo, hi), decimals)

def sine_drift(base, amp, period=120, offset=0):
    return round(base + amp * math.sin(2 * math.pi * (_tick + offset) / period), 2)

def weighted_status(on_prob=0.92):
    return random.random() < on_prob

def fmtval(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)

def build_payload(raw: dict) -> dict:
    ts_now = int(time.time())
    values = {}
    for k, v in raw.items():
        unit = UNIT_MAP.get(k, "")
        values[k] = {"value": fmtval(v), "unit": unit}
    return {"ts": ts_now, "values": values}


def gen_pit(offset=0):
    """Generate 1 PIT sensor data dengan offset berbeda tiap device."""
    connected = weighted_status(0.92)
    pressure  = round(sine_drift(5.0, 2.0, offset=offset) if connected else 0.0, 2)
    return build_payload({
        "Batt":             random.randint(30, 365),
        "PressureValue":    pressure,
        "ConnectionStatus": "CONNECT" if connected else "DISCONNECT",
        "StatusDetail":     "GOOD" if connected else "BAD",
    })


def on_connect(client, userdata, flags, rc):
    codes = {0:"Connected OK", 1:"Bad protocol", 2:"ID rejected",
             3:"Server unavailable", 4:"Bad credentials", 5:"Not authorized"}
    label = userdata.get("label", "?")
    name  = userdata.get("name", "?")
    if rc == 0:
        log.info(f"[{label}] MQTT {codes[0]} | {name}")
    else:
        log.error(f"[{label}] Connection failed: {codes.get(rc, rc)}")

def on_disconnect(client, userdata, rc):
    label = userdata.get("label", "?")
    if rc != 0:
        log.warning(f"[{label}] Unexpected disconnect (rc={rc})")

def on_publish(client, userdata, mid):
    log.debug(f"Published mid={mid}")


def main():
    global _tick

    log.info("=" * 60)
    log.info("  Well Monitoring Device Simulator — 4 PIT Devices")
    log.info(f"  Host    : {MQTT_HOST}:{MQTT_PORT}")
    log.info(f"  Region  : {REGION} / {SITE_CODE}")
    log.info(f"  Interval: {INTERVAL_SEC}s")
    log.info("=" * 60)

    # Buat 1 MQTT client per device
    clients = []
    for i, (name, token, label) in enumerate(DEVICES):
        topic = f"well/{REGION}/{SITE_CODE}/{name}"
        userdata = {"label": label, "name": name, "topic": topic, "token": token, "offset": i * 30}

        c = mqtt.Client(client_id=f"pit-sim-{label}-{token[:6]}", clean_session=True)
        c.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        c.user_data_set(userdata)
        c.on_connect    = on_connect
        c.on_disconnect = on_disconnect
        c.on_publish    = on_publish
        c.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        c.loop_start()
        clients.append((c, userdata))
        log.info(f"  [{label}] Connecting -> {name} | topic: {topic}")

    time.sleep(2)

    try:
        while True:
            _tick += 1
            ts_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log.info(f"-- Tick #{_tick} | {ts_str} --")

            for c, ud in clients:
                label   = ud["label"]
                topic   = ud["topic"]
                offset  = ud["offset"]
                payload = gen_pit(offset=offset)
                msg     = json.dumps(payload)
                result  = c.publish(topic, msg, qos=1)

                pval = payload["values"]["PressureValue"]["value"]
                conn = payload["values"]["ConnectionStatus"]["value"]
                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    log.info(f"  [{label}] {conn:10s} | P={pval} barg -> OK")
                else:
                    log.error(f"  [{label}] Publish FAILED rc={result.rc}")

                time.sleep(0.1)

            log.info(f"  Tunggu {INTERVAL_SEC}s...\n")
            time.sleep(INTERVAL_SEC)

    except KeyboardInterrupt:
        log.info("Simulator dihentikan (Ctrl+C).")
    finally:
        for c, _ in clients:
            c.loop_stop()
            c.disconnect()
        log.info("Semua MQTT client disconnected. Bye!")


if __name__ == "__main__":
    main()
