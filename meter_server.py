"""
meter_server.py
Simulates a 3-Phase Industrial Digital Power Meter over Modbus TCP.
Uses pymodbus v3.6.9 datastore API with background dynamic telemetry.
"""

import asyncio
import logging
import math
import random
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)

# Configure clean, readable console logs
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("ModbusServer")

# Register Addressing (0-based offset for PLC 40001 - 40004)
ADDR_VOLTAGE = 0       # PLC 40001: Line Voltage (V * 10)
ADDR_CURRENT = 1       # PLC 40002: Load Current (A * 10)
ADDR_PF = 2            # PLC 40003: Power Factor (PF * 100)
ADDR_POWER = 3         # PLC 40004: Active Power (kW * 10)

async def simulate_industrial_load(slave_context: ModbusSlaveContext):
    """
    Simulates realistic factory load variations:
    Base values: 415.0V, 52.0A, 0.88 PF lagging.
    Applies small random fluctuations and motor cycling.
    """
    cycle_tick = 0

    while True:
        cycle_tick += 1
        # Realistic electrical variations
        v_noise = random.uniform(-2.5, 2.5)
        i_noise = random.uniform(-4.0, 6.0) + (8.0 * math.sin(cycle_tick * 0.15))
        pf_noise = random.uniform(-0.02, 0.02)

        v_eng = max(390.0, min(435.0, 415.0 + v_noise))
        i_eng = max(5.0, min(120.0, 52.0 + i_noise))
        pf_eng = max(0.65, min(0.98, 0.88 + pf_noise))

        # Real 3-Phase Active Power: P = sqrt(3) * V_LL * I * PF / 1000 (kW)
        p_eng = (math.sqrt(3) * v_eng * i_eng * pf_eng) / 1000.0

        # Scale to 16-bit Unsigned Integers (UINT16)
        raw_voltage = int(round(v_eng * 10))   # e.g., 415.4V -> 4154
        raw_current = int(round(i_eng * 10))   # e.g., 55.2A  -> 552
        raw_pf = int(round(pf_eng * 100))      # e.g., 0.89   -> 89
        raw_power = int(round(p_eng * 10))     # e.g., 34.2kW -> 342

        # Write to holding registers (FC 03 / fx=3)
        slave_context.setValues(3, ADDR_VOLTAGE, [raw_voltage, raw_current, raw_pf, raw_power])

        await asyncio.sleep(0.5)


async def main():
    # 100 holding registers starting at offset 0, initialized to 0
    datablock = ModbusSequentialDataBlock(0, [0] * 100)
    slave_context = ModbusSlaveContext(hr=datablock, zero_mode=True)
    server_context = ModbusServerContext(slaves={1: slave_context}, single=False)

    host = "127.0.0.1"
    port = 5020

    logger.info(f"Starting 3-Phase Power Meter Modbus TCP Server on {host}:{port} (Unit ID: 1)")

    # Launch background physical telemetry simulator
    asyncio.create_task(simulate_industrial_load(slave_context))

    # Start the TCP server
    await StartAsyncTcpServer(
        context=server_context,
        address=(host, port)
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server shutting down cleanly.")