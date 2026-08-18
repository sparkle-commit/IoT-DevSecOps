package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"log"
	"math"
	"os"
	"strings"
	"time"

	mqtt "github.com/eclipse/paho.mqtt.golang"
	"github.com/gosnmp/gosnmp"
)

// locationTopicBase can be overridden at build time using:
// go build -ldflags="-X 'main.locationTopicBase=TTC/ACEH-LEMBARO/RACK-01'"
var locationTopicBase = "TTC/UNKNOWN/RACK-01"

const (
	mqttBroker    = "tcp://telkomsel.solu.co.id:1883"
	mqttUsername  = "telkomsel_ttc_user"
	mqttPassword  = "e91TE5ALAJKpTmSM"
	snmpCommunity = "public"
	intervalSecs  = 60
)

type TargetDef struct {
	Name      string
	Interface string
	Port      uint16
}

var targetsConfig = []TargetDef{
	{Name: "PDU-01", Interface: "br-lan", Port: 161},
	{Name: "PDU-2", Interface: "eth0.3", Port: 161},
}

// Payload struct strictly define\s the JSON key order
type Payload struct {
	TS                                 int64   `json:"ts"`
	BankStatusCurrent1                 float64 `json:"rPDU2BankStatusCurrent1"`
	BankStatusCurrent2                 float64 `json:"rPDU2BankStatusCurrent2"`
	BankStatusPeakCurrent1             float64 `json:"rPDU2BankStatusPeakCurrent1"`
	BankStatusPeakCurrent2             float64 `json:"rPDU2BankStatusPeakCurrent2"`
	DeviceStatusEnergy                 float64 `json:"rPDU2DeviceStatusEnergy"`
	DeviceStatusPeakPower              float64 `json:"rPDU2DeviceStatusPeakPower"`
	DeviceStatusPower                  float64 `json:"rPDU2DeviceStatusPower"`
	PhaseStatusCurrent                 float64 `json:"rPDU2PhaseStatusCurrent"`
	PhaseStatusPeakCurrent             float64 `json:"rPDU2PhaseStatusPeakCurrent"`
	SensorTempHumidityRelativeHumidity float64 `json:"rPDU2SensorTempHumidityStatusRelativeHumidity"`
	SensorTempHumidityTempC            float64 `json:"rPDU2SensorTempHumidityStatusTempC"`
}

type OIDConfig struct {
	FieldName string
	Divisor   float64
}

var oidMap = map[string]OIDConfig{
	"1.3.6.1.4.1.318.1.1.26.4.3.1.5.1":     {"rPDU2DeviceStatusPower", 100},
	"1.3.6.1.4.1.318.1.1.26.4.3.1.6.1":     {"rPDU2DeviceStatusPeakPower", 100},
	"1.3.6.1.4.1.318.1.1.26.4.3.1.9.1":     {"rPDU2DeviceStatusEnergy", 10},
	"1.3.6.1.4.1.318.1.1.26.6.3.1.5.1":     {"rPDU2PhaseStatusCurrent", 10},
	"1.3.6.1.4.1.318.1.1.26.6.3.1.10.1":    {"rPDU2PhaseStatusPeakCurrent", 10},
	"1.3.6.1.4.1.318.1.1.26.8.3.1.5.1":     {"rPDU2BankStatusCurrent1", 10},
	"1.3.6.1.4.1.318.1.1.26.8.3.1.5.2":     {"rPDU2BankStatusCurrent2", 10},
	"1.3.6.1.4.1.318.1.1.26.8.3.1.6.1":     {"rPDU2BankStatusPeakCurrent1", 10},
	"1.3.6.1.4.1.318.1.1.26.8.3.1.6.2":     {"rPDU2BankStatusPeakCurrent2", 10},
	"1.3.6.1.4.1.318.1.1.26.10.2.2.1.8.1":  {"rPDU2SensorTempHumidityStatusTempC", 10},
	"1.3.6.1.4.1.318.1.1.26.10.2.2.1.10.1": {"rPDU2SensorTempHumidityStatusRelativeHumidity", 1},
}

var oids []string

func init() {
	for oid := range oidMap {
		oids = append(oids, oid)
	}
}

// discoverIP reads the /proc/net/arp file to find the first reachable IP for a given interface
func discoverIP(iface string) string {
	file, err := os.Open("/proc/net/arp")
	if err != nil {
		log.Printf("Cannot open ARP table: %v", err)
		return ""
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		fields := strings.Fields(line)
		// Expected format: IP address, HW type, Flags, HW address, Mask, Device
		if len(fields) >= 6 {
			ip := fields[0]
			flags := fields[2]
			device := fields[5]

			if device == iface && flags != "0x0" {
				return ip
			}
		}
	}
	return ""
}

func getSNMPValues(ip string, port uint16, pduName string) *Payload {
	snmpClient := &gosnmp.GoSNMP{
		Target:    ip,
		Port:      port,
		Community: snmpCommunity,
		Version:   gosnmp.Version2c,
		Timeout:   time.Duration(5) * time.Second,
		Retries:   1,
	}

	err := snmpClient.Connect()
	if err != nil {
		log.Printf("[%s] SNMP Connect error at %s:%d - %v", pduName, ip, port, err)
		return nil
	}
	defer snmpClient.Conn.Close()

	result, err := snmpClient.Get(oids)
	if err != nil {
		log.Printf("[%s] SNMP Get error at %s:%d - %v", pduName, ip, port, err)
		return nil
	}

	// Create payload with current unix timestamp in milliseconds
	payload := &Payload{
		TS: time.Now().UnixMilli(),
	}

	for _, variable := range result.Variables {
		reqOID := strings.TrimPrefix(variable.Name, ".")
		config, exists := oidMap[reqOID]
		if !exists {
			continue
		}

		var rawValue int
		switch variable.Type {
		case gosnmp.Integer, gosnmp.Gauge32, gosnmp.TimeTicks, gosnmp.Counter32, gosnmp.Uinteger32:
			rawValue = int(gosnmp.ToBigInt(variable.Value).Int64())
		}

		val := float64(rawValue)
		if config.Divisor != 1 {
			val = math.Round((val/config.Divisor)*100) / 100
		}

		// Map to struct fields dynamically is hard, so we do it explicitly
		switch config.FieldName {
		case "rPDU2BankStatusCurrent1":
			payload.BankStatusCurrent1 = val
		case "rPDU2BankStatusCurrent2":
			payload.BankStatusCurrent2 = val
		case "rPDU2BankStatusPeakCurrent1":
			payload.BankStatusPeakCurrent1 = val
		case "rPDU2BankStatusPeakCurrent2":
			payload.BankStatusPeakCurrent2 = val
		case "rPDU2DeviceStatusEnergy":
			payload.DeviceStatusEnergy = val
		case "rPDU2DeviceStatusPeakPower":
			payload.DeviceStatusPeakPower = val
		case "rPDU2DeviceStatusPower":
			payload.DeviceStatusPower = val
		case "rPDU2PhaseStatusCurrent":
			payload.PhaseStatusCurrent = val
		case "rPDU2PhaseStatusPeakCurrent":
			payload.PhaseStatusPeakCurrent = val
		case "rPDU2SensorTempHumidityStatusRelativeHumidity":
			payload.SensorTempHumidityRelativeHumidity = val
		case "rPDU2SensorTempHumidityStatusTempC":
			payload.SensorTempHumidityTempC = val
		}
	}
	return payload
}

func publishMQTT(client mqtt.Client, topic string, payload *Payload) {
	jsonBytes, err := json.Marshal(payload)
	if err != nil {
		log.Printf("Error marshaling payload: %v", err)
		return
	}

	msg := string(jsonBytes)
	token := client.Publish(topic, 0, false, msg)
	token.Wait()
	if token.Error() != nil {
		log.Printf("Failed to publish to %s: %v", topic, token.Error())
	} else {
		log.Printf("Published to %s: %s", topic, msg)
	}
}

func main() {
	log.SetOutput(os.Stdout)
	log.SetFlags(log.LstdFlags)

	log.Println("Starting PDU Monitor.")
	log.Printf("Location Base Topic: %s\n", locationTopicBase)
	log.Println("Waiting 10 seconds for boot/network/mount readiness...")
	time.Sleep(10 * time.Second)

	opts := mqtt.NewClientOptions()
	opts.AddBroker(mqttBroker)
	opts.SetUsername(mqttUsername)
	opts.SetPassword(mqttPassword)
	opts.SetClientID(fmt.Sprintf("rut956_pdu_%d", time.Now().Unix()))
	opts.SetAutoReconnect(true)

	client := mqtt.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		log.Fatalf("Error connecting to MQTT Broker: %v", token.Error())
	}
	log.Println("Connected to MQTT broker.")
	defer client.Disconnect(250)

	ticker := time.NewTicker(time.Duration(intervalSecs) * time.Second)
	defer ticker.Stop()

	pollAndPublish(client)

	for range ticker.C {
		pollAndPublish(client)
	}
}

func pollAndPublish(client mqtt.Client) {
	for _, target := range targetsConfig {
		ip := discoverIP(target.Interface)
		if ip == "" {
			log.Printf("[%s] Tidak ada device terdeteksi di %s", target.Name, target.Interface)
			continue
		}

		values := getSNMPValues(ip, target.Port, target.Name)
		if values != nil {
			topic := fmt.Sprintf("%s/%s", locationTopicBase, target.Name)
			publishMQTT(client, topic, values)
		}
	}
}
