import json
import math
import random
import time
import logging
from datetime import datetime

import paho.mqtt.client as mqtt

MQTT_HOST     = "selin.solu.co.id"
MQTT_PORT     = 9099
MQTT_USERNAME = "selin_dev"
MQTT_PASSWORD = "VA!#J*O[MUhNCV7T"
DEVICE_ID     = "9NzBm6GxHbbvHZCNDL0k"
INTERVAL_SEC  = 30

REGION        = "JKT"
SITE_CODE     = "GW"
DEVICE_NAME   = "2500-PIT-8001A"
MQTT_TOPIC    = f"well/{REGION}/{SITE_CODE}/{DEVICE_NAME}"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("WellSim")

UNIT_MAP = {
    # PIT — 4 sensor
    "PressureValue1": "barg", "PressureValue2": "barg",
    "PressureValue3": "barg", "PressureValue4": "barg",
    "StatusDetail1":  "",     "StatusDetail2":  "",
    "StatusDetail3":  "",     "StatusDetail4":  "",
    "ConnectionStatus1": "",  "ConnectionStatus2": "",
    "ConnectionStatus3": "",  "ConnectionStatus4": "",
    # GX Solar — tunggal
    "SOC":               "%",
    "BatteryTemperature":"degC",
    "InverterVoltage":   "V",
    # GX Solar — battery string 1 & 2
    "BatteryCurrent1":   "A",    "BatteryCurrent2":   "A",
    "BatteryVoltage1":   "V",    "BatteryVoltage2":   "V",
    "PVCurrent1":        "A",    "PVCurrent2":        "A",
    "PVPower1":          "W",    "PVPower2":          "W",
    "PVVoltage1":        "Vdc",  "PVVoltage2":        "Vdc",
    "StatusDetail_GX":   "",
    "YieldToday1":       "kWh",  "YieldToday2":       "kWh",
    # Network
    "statusGW":          "",
    "statusAP":          "",
    "statusRepeater":    "",
    "statusStarlink":    "",
    "HighBattAlarm":     "",
    "LowBattAlarm":      "",
}

_tick = 0

def rnd(lo, hi, decimals=2):
    return round(random.uniform(lo, hi), decimals)

def sine_drift(base, amp, period=120):
    return round(base + amp * math.sin(2 * math.pi * _tick / period), 2)

def weighted_status(on_prob=0.90):
    """Sebagian besar ONLINE/CONNECT, sesekali OFFLINE/DISCONNECT."""
    return random.random() < on_prob

def fmtval(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)

def build_payload(raw: dict) -> dict:
    """
    Semua key dalam 1 ts bersama:
    {
      "ts": unix_seconds,
      "values": { key: {"value": "...", "unit": "..."} }
    }
    """
    ts_now = int(time.time())
    values = {}
    for k, v in raw.items():
        unit = UNIT_MAP.get(k, "")
        values[k] = {"value": fmtval(v), "unit": unit}
    return {"ts": ts_now, "values": values}


def gen_all():
    # ── PIT — 4 sensor ──
    pit = []
    for i in range(4):
        connected = weighted_status(0.92)
        pressure  = round(sine_drift(5.0 + i*0.3, 2.0) if connected else 0.0, 2)
        pit.append({"connected": connected, "pressure": pressure})

    # ── GX Solar — tunggal ──
    soc         = max(0.0, min(100.0, sine_drift(75.0, 20.0)))
    batt_temp   = rnd(25.0, 45.0)
    inv_voltage = rnd(220.0, 230.0)
    high_alarm  = "ON" if soc > 95.0 else "OFF"
    low_alarm   = "ON" if soc < 20.0 else "OFF"
    gx_online   = weighted_status(0.95)
    # String 1
    pv_power1   = max(0.0, sine_drift(150.0, 100.0))
    pv_voltage1 = rnd(18.0, 36.0) if pv_power1 > 0 else 0.0
    pv_current1 = round(pv_power1 / pv_voltage1, 2) if pv_voltage1 > 0 else 0.0
    batt_volt1  = sine_drift(24.5, 1.5)
    batt_curr1  = sine_drift(5.0, 8.0)
    yield1      = rnd(0.0, 8.0)
    # String 2
    pv_power2   = max(0.0, sine_drift(130.0, 90.0, period=100))
    pv_voltage2 = rnd(18.0, 36.0) if pv_power2 > 0 else 0.0
    pv_current2 = round(pv_power2 / pv_voltage2, 2) if pv_voltage2 > 0 else 0.0
    batt_volt2  = sine_drift(25.0, 1.2, period=110)
    batt_curr2  = sine_drift(4.5, 7.0, period=115)
    yield2      = rnd(0.0, 8.0)

    raw = {
        # ── PIT — 4 sensor ──
        **{f"PressureValue{i+1}":    pit[i]["pressure"]                          for i in range(4)},
        **{f"StatusDetail{i+1}":     "GOOD" if pit[i]["connected"] else "BAD"    for i in range(4)},
        **{f"ConnectionStatus{i+1}": "CONNECT" if pit[i]["connected"] else "DISCONNECT" for i in range(4)},

        # ── GX Solar — tunggal ──
        "SOC":               soc,
        "BatteryTemperature":batt_temp,
        "InverterVoltage":   inv_voltage,
        "HighBattAlarm":     high_alarm,
        "LowBattAlarm":      low_alarm,
        "StatusDetail_GX":   "ONLINE" if gx_online else "OFFLINE",

        # ── GX Solar — String 1 ──
        "BatteryCurrent1":   batt_curr1,
        "BatteryVoltage1":   batt_volt1,
        "PVCurrent1":        pv_current1,
        "PVPower1":          pv_power1,
        "PVVoltage1":        pv_voltage1,
        "YieldToday1":       yield1,

        # ── GX Solar — String 2 ──
        "BatteryCurrent2":   batt_curr2,
        "BatteryVoltage2":   batt_volt2,
        "PVCurrent2":        pv_current2,
        "PVPower2":          pv_power2,
        "PVVoltage2":        pv_voltage2,
        "YieldToday2":       yield2,

        # ── Network ──
        "statusGW":          "ONLINE" if weighted_status(0.95) else "OFFLINE",
        "statusAP":          "ONLINE" if weighted_status(0.93) else "OFFLINE",
        "statusRepeater":    "ONLINE" if weighted_status(0.92) else "OFFLINE",
        "statusStarlink":    "ONLINE" if weighted_status(0.90) else "OFFLINE",
    }

    return build_payload(raw)


def on_connect(client, userdata, flags, rc):
    codes = {0:"Connected OK", 1:"Bad protocol", 2:"ID rejected",
             3:"Server unavailable", 4:"Bad credentials", 5:"Not authorized"}
    if rc == 0:
        log.info(f"MQTT {codes[0]} -> {MQTT_HOST}:{MQTT_PORT}")
        log.info(f"Publishing to topic: {MQTT_TOPIC}")
    else:
        log.error(f"MQTT Connection failed: {codes.get(rc, rc)}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        log.warning(f"Unexpected disconnect (rc={rc})")

def on_publish(client, userdata, mid):
    log.debug(f"Published mid={mid}")



def main():
    global _tick

    log.info("=" * 55)
    log.info("  Well Monitoring Device Simulator")
    log.info(f"  Host    : {MQTT_HOST}:{MQTT_PORT}")
    log.info(f"  Device  : {DEVICE_NAME}")
    log.info(f"  Topic   : {MQTT_TOPIC}")
    log.info(f"  Interval: {INTERVAL_SEC}s")
    log.info('  Format  : {"ts":unix, "values":{"key":{"value","unit"}}}')
    log.info("=" * 55)

    client = mqtt.Client(client_id=f"well-sim-{DEVICE_ID[:8]}", clean_session=True)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish    = on_publish

    log.info(f"Connecting to {MQTT_HOST}:{MQTT_PORT} ...")
    client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
    client.loop_start()
    time.sleep(2)

    try:
        while True:
            _tick += 1
            payload = gen_all()
            msg     = json.dumps(payload)
            result  = client.publish(MQTT_TOPIC, msg, qos=1)
            n_keys  = len(payload.get("values", {}))

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                log.info(
                    f"Tick #{_tick:4d} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"{n_keys} keys -> {MQTT_TOPIC} (mid={result.mid})"
                )
            else:
                log.error(f"Publish FAILED rc={result.rc}")

            time.sleep(INTERVAL_SEC)

    except KeyboardInterrupt:
        log.info("Simulator dihentikan (Ctrl+C).")
    finally:
        client.loop_stop()
        client.disconnect()
        log.info("MQTT disconnected. Bye!")


if __name__ == "__main__":
    main()
