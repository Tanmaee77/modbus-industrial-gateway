"""
scada_client.py
Industrial Modbus TCP Client / SCADA Telemetry Collector.
Polls 3-Phase Meter Holding Registers (FC03), reconstructs engineering units,
and detects threshold alarms (Overvoltage, Undervoltage, Low Power Factor).
"""

import time
import logging
from pymodbus.client import ModbusTcpClient

# Configure clean logging
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("SCADA_Client")

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5020
SLAVE_UNIT_ID = 1

# Engineering Thresholds for Alarms
V_NOMINAL = 415.0
V_ALARM_HIGH = 425.0
V_ALARM_LOW = 400.0
PF_ALARM_LOW = 0.80

def evaluate_alarms(voltage: float, pf: float):
    """Checks industrial telemetry against tolerance limits."""
    alerts = []
    if voltage > V_ALARM_HIGH:
        alerts.append(f"HIGH VOLTAGE ALARM ({voltage:.1f}V > {V_ALARM_HIGH}V)")
    elif voltage < V_ALARM_LOW:
        alerts.append(f"LOW VOLTAGE ALARM ({voltage:.1f}V < {V_ALARM_LOW}V)")

    if pf < PF_ALARM_LOW:
        alerts.append(f"LOW POWER FACTOR PENALTY RISK (PF {pf:.2f} < {PF_ALARM_LOW})")

    return alerts

def main():
    logger.info(f"Connecting to Modbus Gateway at {SERVER_HOST}:{SERVER_PORT}...")
    client = ModbusTcpClient(SERVER_HOST, port=SERVER_PORT)

    if not client.connect():
        logger.error("Unable to establish TCP connection to Modbus Server.")
        return

    logger.info("Connected successfully. Commencing polling loop (Press Ctrl+C to stop)...\n")

    try:
        while True:
            # Function Code 03: Read 4 Holding Registers starting at offset 0
            response = client.read_holding_registers(address=0, count=4, slave=SLAVE_UNIT_ID)

            if response.isError():
                logger.warning(f"Modbus Read Exception: {response}")
            else:
                raw = response.registers
                # Apply reverse scaling factors to reconstruct engineering units
                voltage = raw[0] / 10.0   # Scale factor: /10
                current = raw[1] / 10.0   # Scale factor: /10
                pf = raw[2] / 100.0       # Scale factor: /100
                power = raw[3] / 10.0     # Scale factor: /10

                alarms = evaluate_alarms(voltage, pf)
                alarm_str = f" | \033[91m{' | '.join(alarms)}\033[0m" if alarms else " | \033[92mNORMAL\033[0m"

                print(
                    f"[Telemetry] V: {voltage:5.1f} V | "
                    f"I: {current:5.1f} A | "
                    f"PF: {pf:.2f} | "
                    f"P: {power:5.2f} kW"
                    f"{alarm_str}"
                )

            time.sleep(1.0)

    except KeyboardInterrupt:
        logger.info("\nPolling stopped by operator.")
    finally:
        client.close()
        logger.info("TCP socket closed cleanly.")

if __name__ == "__main__":
    main()