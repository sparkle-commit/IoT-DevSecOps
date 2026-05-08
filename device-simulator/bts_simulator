"""
BTS Monitoring Device Simulator for ThingsBoard
================================================
Kategori: overview, battery, rectifier, inverter, general_data, events,
          grounding, presence, temperature, cctv, fiber_optic

Format payload (1 ts bersama per kategori):
{
  "ts": 1777882102,
  "values": {
    "Usys":  {"value": "48.30", "unit": "V"},
    "Iload": {"value": "55.00", "unit": "A"},
    ...
  }
}

Interval: 30 detik
Topic   : bts/{region}/{site_code}/{site_name}/{category}
"""

import base64
import json
import math
import random
import time
import logging
from datetime import datetime

import paho.mqtt.client as mqtt

# ─────────────────────────────────────────────
#  KONFIGURASI
# ─────────────────────────────────────────────
MQTT_HOST     = "selin.solu.co.id"
MQTT_PORT     = 9099
MQTT_USERNAME = "selin_dev"
MQTT_PASSWORD = "VA!#J*O[MUhNCV7T"
DEVICE_ID     = "a6ca0510-4771-11f1-a741-2323891940a8"
INTERVAL_SEC  = 30

SITE_REGION   = "JAW"
SITE_CODE     = "CCJ_0037"
SITE_NAME     = "Jagakarsa"

def make_topic(category: str) -> str:
    return f"bts/{SITE_REGION}/{SITE_CODE}/{SITE_NAME}/{category}"

# ─────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("BTS-Simulator")

# ─────────────────────────────────────────────
#  UNIT MAP
# ─────────────────────────────────────────────
UNIT_MAP = {
    # Overview
    "Usys":"V","Iload":"A","Psys":"W","Eload":"kWh","Irect":"A","Prect":"W",
    "Erect":"kWh","Udcdc":"V","Idcdc":"A","Pdcdc":"W","Edcdc":"kWh",
    "Ipvc":"A","Ppvc":"W","Epvc":"kWh","Iwpc":"A","Pwpc":"W","Ewpc":"kWh",
    "Ibatt":"A","Tbatt":"degC","TA":"degC","ACV":"V","alarmBattStolen":"",
    "ChargeMode":"","SoC":"%","EbattIn":"kWh","Ebatt":"kWh",
    "AhOut":"Ah","TotalCapacity":"Ah","RemainingBackupTime":"h",
    # Battery (suffix match)
    "voltage":"V","current":"A","soc":"%","soh":"%",
    "remaingCap":"Ah","fullCap":"Ah","cycle":"",
    # Rectifier (suffix match)
    "Iout":"A","Pout":"W","Temp1":"degC","Temp2":"degC",
    # Inverter
    "PV1_voltage":"V","PV1_current":"A","PV2_voltage":"V","PV2_current":"A",
    "PV3_voltage":"V","PV3_current":"A","PV4_voltage":"V","PV4_current":"A",
    "PV5_voltage":"V","PV5_current":"A","PV6_voltage":"V","PV6_current":"A",
    "PV7_voltage":"V","PV7_current":"A","PV8_voltage":"V","PV8_current":"A",
    "Grid_A_phase_voltage":"V","Grid_B_phase_voltage":"V","Grid_C_phase_voltage":"V",
    "Grid_A_phase_current":"A","Grid_B_phase_current":"A","Grid_C_phase_current":"A",
    "Todays_peak_active_power":"kW","Active_power":"kW","Reactive_power":"kVar",
    "Power_factor":"","Grid_frequency":"Hz","Cabinet_temperature":"degC",
    "Insulation_resistance":"Ohm","Device_status":"","Startup_time":"","Shutdown_time":"",
    "Total_energy_yield":"kWh","Energy_yield_of_current_day":"kWh",
    "Total_number_of_optimizers":"","Reactive_power_adjustment":"kVar",
    "Active_power_adjustment":"kW","Locking":"","Collect_DSP_data":"",
    # General data
    "Transfer_Trip":"","Qty_PV_Invt":"","Qty_ESS_Pcs":"",
    "Active_PV_Power":"kW","Reactive_PV_Power":"kVar",
    "Active_ESS_Power":"kW","Reactive_ESS_Power":"kVar",
    "Rated_PV_Power":"kW","Rated_ESS_Power":"kW",
    "Power_Supply_Grid":"kW","Total_Power_Supply_Grid":"kWh",
    "Energy_Charged":"kWh","Energy_Discharged":"kWh",
    "Total_Energy_Charged":"kWh","Total_Energy_Discharged":"kWh",
    "Chargeable_Capacity":"kWh","Dischargeable_Capacity":"kWh","Rated_ESS":"kW",
    "Maximum_ESS_Charge_Power":"kW","Maximum_ESS_Discharge_Power":"kW",
    "Highest_Stable_Charge_Power_Of_ESS":"kW","Highest_Stable_Discharge_Power_Of_ESS":"kW",
    "DC_Current":"A","Soc_ESS":"%","Soh_ESS":"%","Soe_ESS":"%","Rated_ESS_Capacity":"kWh",
    "Input_Power":"kW","Active_Power":"kW","Power_Factor":"","Reactive_Power":"kVar",
    "CO2_Reduced":"t","Total_Energy":"kWh","Yield_Today":"kWh","Todays_Power_Generation":"kWh",
    "Iphase_A":"A","Iphase_B":"A","Iphase_C":"A",
    "AB_Voltage":"V","BC_Voltage":"V","CA_Voltage":"V",
    "Inverter_Efficiency":"%","Locking_Status":"",
    # Grounding
    "ground_resistance":"Ohm","ground_status":"","ground_voltage":"V",
    "ground_leakage_current":"mA","ground_last_test_ts":"",
    # Presence
    "presence_detected":"","presence_distance":"cm",
    "presence_sensitivity":"","presence_zone":"","presence_duration":"s",
    # Temperature
    "temp_shelter_in":"degC","temp_shelter_out":"degC","humidity_shelter":"%",
    "heat_index":"degC","temp_alert":"",
    # CCTV
    "cctv_snapshot":"base64",
    # Fiber optic telemetry
    "mtxrOpticalRxLoss":"","mtxrOpticalTxFault":"",
    "mtxrOpticalWavelength":"nm","mtxrOpticalTemperature":"degC",
    "mtxrOpticalSupplyVoltage":"V","mtxrOpticalTxBiasCurrent":"mA",
    "mtxrOpticalTxPower":"dBm","mtxrOpticalRxPower":"dBm",
    "sysUpTime":"s","ifSpeed":"bps","ifOperStatus":"",
    "ifInOctets":"bytes","ifOutOctets":"bytes",
    "ifInErrors":"","ifOutErrors":"","ifInDiscards":"","ifOutDiscards":"",
}

def get_unit(key: str) -> str:
    if key in UNIT_MAP:
        return UNIT_MAP[key]
    parts = key.split("_")
    for i in range(1, len(parts)):
        suffix = "_".join(parts[i:])
        if suffix in UNIT_MAP:
            return UNIT_MAP[suffix]
    return ""

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
_tick = 0

def rnd(lo, hi, decimals=2):
    return round(random.uniform(lo, hi), decimals)

def sine_drift(base, amp, period=120):
    return round(base + amp * math.sin(2 * math.pi * _tick / period), 2)

def bool_event(prob=0.05):
    return random.random() < prob

def fmtval(value) -> str:
    if isinstance(value, float):
        return f"{value:.2f}"
    return str(value)

def build_payload(raw: dict) -> dict:
    """
    Bungkus semua key dengan 1 ts bersama:
    {
      "ts": unix_seconds,
      "values": {
        "key": {"value": "...", "unit": "..."},
        ...
      }
    }
    """
    ts_now = int(time.time())
    values = {}
    for k, v in raw.items():
        values[k] = {"value": fmtval(v), "unit": get_unit(k)}
    return {"ts": ts_now, "values": values}

def build_payload_with_attrs(telemetry: dict, attributes: dict) -> dict:
    """Untuk fiber optic — pisah telemetry dan attributes dalam 1 payload."""
    ts_now = int(time.time())
    tel_values = {}
    for k, v in telemetry.items():
        tel_values[k] = {"value": fmtval(v), "unit": get_unit(k)}
    return {
        "ts": ts_now,
        "values": tel_values,
        "attributes": attributes,
    }

# ─────────────────────────────────────────────
#  GENERATORS
# ─────────────────────────────────────────────

def gen_overview():
    usys = sine_drift(48.2, 0.8); iload = sine_drift(55.0, 10.0)
    return build_payload({
        "Usys": rnd(47,54), "Iload": iload, "Psys": round(usys*iload,1),
        "Eload": rnd(200,400), "Irect": rnd(20,60), "Prect": rnd(1000,3000),
        "Erect": rnd(100,300), "Udcdc": rnd(24,28), "Idcdc": rnd(5,20),
        "Pdcdc": rnd(120,560), "Edcdc": rnd(50,150), "Ipvc": rnd(0,15),
        "Ppvc": rnd(0,800), "Epvc": rnd(0,200), "Iwpc": rnd(0,10),
        "Pwpc": rnd(0,500), "Ewpc": rnd(0,100), "Ibatt": sine_drift(0,20),
        "Tbatt": rnd(25,40), "TA": rnd(28,45), "ACV": sine_drift(220,5),
        "alarmBattStolen": int(bool_event(0.01)), "ChargeMode": random.choice([0,1,2]),
        "SoC": rnd(40,100), "EbattIn": rnd(0,50), "Ebatt": rnd(50,200),
        "AhOut": rnd(0,100), "TotalCapacity": rnd(200,600), "RemainingBackupTime": rnd(1,12),
    })


def gen_battery():
    raw = {}
    for b in ["Batt1","Batt2"]:
        p = f"{b}_"
        raw[p+"voltage"]   = rnd(48,54.6)
        raw[p+"current"]   = sine_drift(0,15)
        raw[p+"soc"]       = rnd(40,100)
        raw[p+"soh"]       = rnd(85,100)
        raw[p+"remaingCap"]= rnd(50,200)
        raw[p+"fullCap"]   = rnd(180,200)
        raw[p+"cycle"]     = random.randint(0,500)
    return build_payload(raw)


def gen_rectifier():
    raw = {}
    for s in [1,2,3]:
        p = f"RM1_slot{s}_"
        raw[p+"Iout"] = rnd(5,25); raw[p+"Pout"] = rnd(200,1200)
        raw[p+"Temp1"]= rnd(30,60); raw[p+"Temp2"]= rnd(30,60)
    return build_payload(raw)


def gen_inverter():
    now = int(time.time())
    startup_str  = datetime.fromtimestamp(now - random.randint(3600,86400)).strftime("%Y-%m-%d %H:%M:%S")
    shutdown_str = datetime.fromtimestamp(now - random.randint(0,3600)).strftime("%Y-%m-%d %H:%M:%S")
    raw = {
        **{f"PV{n}_voltage": rnd(280,400) for n in range(1,9)},
        **{f"PV{n}_current": rnd(0,12)    for n in range(1,9)},
        "Grid_A_phase_voltage": sine_drift(220,4),
        "Grid_B_phase_voltage": sine_drift(220,4),
        "Grid_C_phase_voltage": sine_drift(220,4),
        "Grid_A_phase_current": rnd(5,20),
        "Grid_B_phase_current": rnd(5,20),
        "Grid_C_phase_current": rnd(5,20),
        "Todays_peak_active_power": rnd(3,8), "Active_power": rnd(1,7),
        "Reactive_power": rnd(-0.5,0.5), "Power_factor": rnd(0.9,1.0),
        "Grid_frequency": rnd(49.8,50.2), "Cabinet_temperature": rnd(30,55),
        "Insulation_resistance": rnd(500,2000), "Device_status": random.choice([0,1]),
        "Startup_time": startup_str, "Shutdown_time": shutdown_str,
        "Total_energy_yield": rnd(5000,50000), "Energy_yield_of_current_day": rnd(0,30),
        "Total_number_of_optimizers": random.randint(0,32),
        "Reactive_power_adjustment": rnd(-100,100), "Active_power_adjustment": rnd(0,100),
        "Locking": 0, "Collect_DSP_data": 1,
    }
    return build_payload(raw)


def gen_general_data():
    soc = rnd(30,100)
    return build_payload({
        "Transfer_Trip": 0, "Qty_PV_Invt": random.randint(1,4), "Qty_ESS_Pcs": random.randint(1,4),
        "Active_PV_Power": rnd(0,10), "Reactive_PV_Power": rnd(-0.5,0.5),
        "Active_ESS_Power": rnd(-5,5), "Reactive_ESS_Power": rnd(-0.5,0.5),
        "Rated_PV_Power": 10.0, "Rated_ESS_Power": 5.0,
        "Power_Supply_Grid": rnd(0,5), "Total_Power_Supply_Grid": rnd(0,50),
        "Energy_Charged": rnd(0,50), "Energy_Discharged": rnd(0,50),
        "Total_Energy_Charged": rnd(100,5000), "Total_Energy_Discharged": rnd(100,5000),
        "Chargeable_Capacity": rnd(0,100), "Dischargeable_Capacity": rnd(0,100),
        "Rated_ESS": 5.0, "Maximum_ESS_Charge_Power": rnd(3,5),
        "Maximum_ESS_Discharge_Power": rnd(3,5),
        "Highest_Stable_Charge_Power_Of_ESS": rnd(2,4.5),
        "Highest_Stable_Discharge_Power_Of_ESS": rnd(2,4.5),
        "DC_Current": rnd(0,100), "Soc_ESS": soc, "Soh_ESS": rnd(85,100),
        "Soe_ESS": round(soc*0.95,2), "Rated_ESS_Capacity": 200.0,
        "Input_Power": rnd(0.5,8), "Active_Power": rnd(0.5,7),
        "Power_Factor": rnd(0.9,1.0), "Reactive_Power": rnd(-0.5,0.5),
        "CO2_Reduced": rnd(0,10), "Total_Energy": rnd(5000,50000),
        "Yield_Today": rnd(0,30), "Todays_Power_Generation": rnd(0,30),
        "Iphase_A": rnd(5,20), "Iphase_B": rnd(5,20), "Iphase_C": rnd(5,20),
        "AB_Voltage": sine_drift(380,8), "BC_Voltage": sine_drift(380,8),
        "CA_Voltage": sine_drift(380,8), "Inverter_Efficiency": rnd(95,99),
        "Locking_Status": 0,
    })


def gen_events():
    p_major, p_minor = 0.03, 0.05
    alarms = (
        [("Major_ACV_Low",p_major),("Major_AC_Main_fail",p_major),
         ("Major_Battery_Backup_Cut_Off_Over_SLA",p_major),
         ("Major_High_Temperature",p_major),("Major_Low_DC_Voltage",p_major),
         ("Major_Rectifier_Module_ALM",p_major),
         ("Minor_ACV_High",p_minor),("Minor_AC_SPD",p_minor)] +
        [(f"Minor_Batt{n}_{s}",p_minor) for n in range(1,6) for s in [
            "Cell_OV_Alarm","Cell_UV_Alarm","Cell_Unbalance_Alarm","Charging_HT_Alarm",
            "Commu_Fault","Discharging_OC_Alarm","Environment_HT_Alarm",
            "Environment_LT_Alarm","SOC_Low_Alarm"]] +
        [("Minor_Batt_CB_trip",p_minor),("Minor_Battery_Stolen",0.01),
         ("Minor_Battery_temp_high",p_minor),("Minor_Breaker_Trip",p_minor),
         ("Minor_DC_SPD_Alarm",p_minor),("Minor_Door_Open",p_minor),
         ("Minor_Fan_Fail",p_minor),("Minor_Genset_On",p_minor),
         ("Minor_High_DC_Voltage",p_minor),("Minor_L_LVBD_trip",p_minor),
         ("Minor_L_LVLD_trip",p_minor),("Minor_PL_CB_trip",p_minor),
         ("Minor_S_Battery_On_Discharge",p_minor),("Minor_S_Non_Urg_Alarm",p_minor),
         ("Minor_S_Non_Urg_RFA",p_minor),("Minor_S_RM_Com_Failure",p_minor),
         ("Minor_S_Urgent_Alarm",p_minor),("Minor_S_Urgent_RFA",p_minor),
         ("Minor_Smoke_alarm",0.01),("Minor_TAH",p_minor),("Minor_TAL",p_minor)]
    )
    return build_payload({k: int(bool_event(p)) for k,p in alarms})


def gen_grounding():
    resistance = rnd(0.5, 8.0)
    status     = "OK" if resistance < 5.0 else "FAIL"
    return build_payload({
        "ground_resistance":      resistance,
        "ground_status":          status,
        "ground_voltage":         rnd(0.0, 0.5),          # idealnya mendekati 0
        "ground_leakage_current": rnd(0.0, 5.0),          # mA
        "ground_last_test_ts":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


def gen_presence():
    detected = int(bool_event(0.15))   # 15% chance ada orang
    return build_payload({
        "presence_detected":   detected,
        "presence_distance":   rnd(30, 500) if detected else 0,   # cm
        "presence_sensitivity":random.randint(1, 10),
        "presence_zone":       random.randint(1, 4),               # zona 1-4
        "presence_duration":   random.randint(0, 300) if detected else 0,  # detik
    })


def gen_temperature():
    temp_in  = sine_drift(32.0, 5.0)
    temp_out = sine_drift(30.0, 8.0)
    humidity = rnd(40.0, 90.0)
    # Heat index sederhana (Steadman approximation)
    hi = round(-8.78 + 1.611*temp_in + 2.338*humidity - 0.1461*temp_in*humidity
               + 0.001231*temp_in**2 + 0.00385*humidity**2
               - 0.000016*temp_in**2*humidity - 0.000048*temp_in*humidity**2, 2)
    return build_payload({
        "temp_shelter_in":  temp_in,
        "temp_shelter_out": temp_out,
        "humidity_shelter": humidity,
        "heat_index":       hi,
        "temp_alert":       int(temp_in > 35.0),
    })


def gen_cctv():
    """Simulasi snapshot CCTV — base64 dari gambar dummy 1x1 pixel JPEG."""
    # 1x1 piksel JPEG putih (bytes asli, bukan placeholder)
    jpeg_1x1 = (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
        b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
        b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),01444\x1f'9=82<.342\x1e\xc7"
        b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00"
        b"\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00"
        b"\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00"
        b"\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00"
        b"\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07\"q\x142\x81"
        b"\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19"
        b"\x1a%&'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86"
        b"\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4"
        b"\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2"
        b"\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9"
        b"\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5"
        b"\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xfb\xd7"
        b"\xff\xd9"
    )
    snapshot_b64 = base64.b64encode(jpeg_1x1).decode("utf-8")
    ts_now = int(time.time())
    return {
        "ts": ts_now,
        "values": {
            "cctv_snapshot": {
                "value": snapshot_b64,
                "unit":  "base64",
            }
        }
    }


def gen_fiber_optic():
    """
    Fiber optic via SFP SNMP (MikroTik OIDs).
    Telemetry  → masuk values
    Attributes → metadata statis device
    """
    tx_power = rnd(-5.0, 0.0)    # dBm
    rx_power = rnd(-20.0, -5.0)  # dBm

    telemetry = {
        "mtxrOpticalRxLoss":          int(bool_event(0.02)),
        "mtxrOpticalTxFault":         int(bool_event(0.02)),
        "mtxrOpticalWavelength":      1310,
        "mtxrOpticalTemperature":     rnd(25.0, 55.0),
        "mtxrOpticalSupplyVoltage":   rnd(3.10, 3.45),
        "mtxrOpticalTxBiasCurrent":   rnd(10.0, 50.0),
        "mtxrOpticalTxPower":         tx_power,
        "mtxrOpticalRxPower":         rx_power,
        "sysUpTime":                  random.randint(86400, 31536000),
        "ifSpeed":                    1000000000,
        "ifOperStatus":               random.choice([1, 1, 1, 2]),  # 1=up,2=down (lebih sering up)
        "ifInOctets":                 random.randint(1000000, 4294967295),
        "ifOutOctets":                random.randint(1000000, 2147483648),
        "ifInErrors":                 random.randint(0, 5),
        "ifOutErrors":                random.randint(0, 5),
        "ifInDiscards":               random.randint(0, 10),
        "ifOutDiscards":              random.randint(0, 150),
    }

    attributes = {
        "mtxrOpticalName":      "sfp-sfpplus1",
        "mtxrOpticalVendorSerial": f"SN-SF{random.randint(1000000,9999999)}",
        "sysDescr":             "MikroTik RouterOS 7.12.1 on CCR2004",
        "sysObjectID":          ".1.3.6.1.4.1.14988.1",
        "sysLocation":          f"{SITE_NAME} - {SITE_CODE} - Rack 01",
        "ifNumber":             24,
        "ifDescr":              "ether1-to-core",
        "ifPhysAddress":        "4C:5E:0C:81:22:A1",
    }

    return build_payload_with_attrs(telemetry, attributes)


# ─────────────────────────────────────────────
#  MQTT CALLBACKS
# ─────────────────────────────────────────────

def on_connect(client, userdata, flags, rc):
    codes = {0:"Connected OK",1:"Bad protocol",2:"ID rejected",
             3:"Server unavailable",4:"Bad credentials",5:"Not authorized"}
    if rc == 0:
        log.info(f"MQTT {codes[0]} -> {MQTT_HOST}:{MQTT_PORT}")
    else:
        log.error(f"MQTT Connection failed: {codes.get(rc, rc)}")

def on_disconnect(client, userdata, rc):
    if rc != 0:
        log.warning(f"Unexpected disconnect (rc={rc})")

def on_publish(client, userdata, mid):
    log.debug(f"Published mid={mid}")


# ─────────────────────────────────────────────
#  PUBLISH
# ─────────────────────────────────────────────

def publish_category(client, category: str, payload: dict):
    topic  = make_topic(category)
    msg    = json.dumps(payload)
    result = client.publish(topic, msg, qos=1)
    n_vals = len(payload.get("values", {}))
    if result.rc == mqtt.MQTT_ERR_SUCCESS:
        log.info(f"  [{category:14s}] {n_vals:3d} keys | {topic}")
    else:
        log.error(f"  [{category:14s}] FAILED rc={result.rc}")


# ─────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────

def main():
    global _tick

    log.info("=" * 62)
    log.info("  BTS Monitoring Device Simulator")
    log.info(f"  Host    : {MQTT_HOST}:{MQTT_PORT}")
    log.info(f"  Site    : {SITE_REGION}/{SITE_CODE}/{SITE_NAME}")
    log.info(f"  Topics  : bts/{SITE_REGION}/{SITE_CODE}/{SITE_NAME}/{{category}}")
    log.info(f"  Interval: {INTERVAL_SEC}s") 
    log.info('  Format  : {"ts":unix, "values":{"key":{"value","unit"}}}')
    log.info("=" * 62)

    client = mqtt.Client(client_id=f"bts-sim-{DEVICE_ID[:8]}", clean_session=True)
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
            log.info(f"-- Tick #{_tick} | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} --")

            categories = {
                "overview":     gen_overview(),
                "battery":      gen_battery(),
                "rectifier":    gen_rectifier(),
                "inverter":     gen_inverter(),
                "general_data": gen_general_data(),
                "events":       gen_events(),
                "grounding":    gen_grounding(),
                "presence":     gen_presence(),
                "temperature":  gen_temperature(),
                "cctv":         gen_cctv(),
                "fiber_optic":  gen_fiber_optic(),
            }

            for cat, payload in categories.items():
                publish_category(client, cat, payload)
                time.sleep(0.15)

            log.info(f"  Semua kategori terkirim. Tunggu {INTERVAL_SEC}s...\n")
            time.sleep(INTERVAL_SEC)

    except KeyboardInterrupt:
        log.info("Simulator dihentikan (Ctrl+C).")
    finally:
        client.loop_stop()
        client.disconnect()
        log.info("MQTT disconnected. Bye!")


if __name__ == "__main__":
    main()
