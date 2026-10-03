# Modbus TCP Industrial Power & Sensor Gateway Simulator

A dual-tier Industrial IoT (IIoT) telemetry simulation that implements a 3-Phase Digital Power Meter over Modbus TCP, together with an active SCADA polling client featuring real-time scaling and alarm limits.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Modbus Register Map](#modbus-register-map)
- [Physical Derivations](#physical-derivations)
- [Project Structure](#project-structure)
- [Quickstart](#quickstart)
- [Troubleshooting](#troubleshooting)

---

## Architecture Overview

```text
[ Industrial Factory Floor ]
  Simulated 3-Phase Load (Motor Cycling, Harmonics, Thermal Drift)
             │
             ▼
[ Modbus TCP Server / Slave (Port 5020, Unit ID 1) ]
  Holding Registers (FC03) — 16-bit Unsigned Integer Memory Store
             │
             │ Modbus Application Protocol (MBAP) / TCP Socket
             ▼
[ SCADA Client / Telemetry Collector ]
  Reverse Scaling ➔ Engineering Units (V, A, PF, kW) ➔ Alarm Limit Monitor
```

| Component | Role | Details |
| --- | --- | --- |
| `meter_server.py` | Modbus TCP Slave | Simulates the 3-phase power meter on port `5020`, Unit ID `1` |
| `scada_client.py` | Modbus TCP Master | Polls registers, scales values, and checks alarm limits |

---

## Modbus Register Map

**Function Code:** `FC03` (Read Holding Registers)

| Address Offset | PLC Register | Parameter | Engineering Range | Scaling Factor | Protocol Type |
| --- | --- | --- | --- | --- | --- |
| `0x0000` | 40001 | Line-to-Line Voltage (V_LL) | 390.0 – 435.0 V | x10 (0.1 V) | UINT16 |
| `0x0001` | 40002 | Load Current (I_RMS) | 5.0 – 120.0 A | x10 (0.1 A) | UINT16 |
| `0x0002` | 40003 | Power Factor (cos φ) | 0.65 – 0.98 lag | x100 (0.01) | UINT16 |
| `0x0003` | 40004 | Active Power (P) | Derived kW | x10 (0.1 kW) | UINT16 |

> **Note:** Values are stored as raw 16-bit unsigned integers. The SCADA client divides by the scaling factor to recover engineering units. For example, a raw value of `4125` in register `40001` means 412.5 V.

---

## Physical Derivations

Active 3-phase electrical power is calculated on every simulation cycle before conversion to an integer:

$$
P = \frac{\sqrt{3} \times V_{LL} \times I_{RMS} \times PF}{1000} \quad (\text{kW})
$$

In plain text:

```text
P (kW) = (√3 × V_LL × I_RMS × PF) / 1000
```

**Example:** with V_LL = 415 V, I_RMS = 50 A, PF = 0.90

```text
P = (1.732 × 415 × 50 × 0.90) / 1000 ≈ 32.3 kW
Raw register value (x10) = 323
```

---

## Project Structure

```text
.
├── meter_server.py      # Modbus TCP server (simulated power meter)
├── scada_client.py      # SCADA polling client with alarm monitoring
├── requirements.txt     # Python dependencies
└── README.md
```

---

## Quickstart

### 1. Set Up a Virtual Environment

```bash
python -m venv venv
```

Activate it:

```bash
# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# Linux / macOS
source venv/bin/activate
```

Install the dependencies:

```bash
pip install -r requirements.txt
```

### 2. Launch the Modbus Meter Server

```bash
python meter_server.py
```

### 3. Launch the SCADA Telemetry Client

In a **separate terminal** (with the virtual environment activated):

```bash
python scada_client.py
```

---

## Troubleshooting

| Problem | Likely Cause | Fix |
| --- | --- | --- |
| Client cannot connect | Server is not running | Start `meter_server.py` first |
| `Address already in use` | Port `5020` is occupied | Stop the other process or change the port in both scripts |
| `ModuleNotFoundError` | Virtual environment is not active | Activate the venv and run `pip install -r requirements.txt` |
| PowerShell blocks activation | Execution policy restriction | Use `activate.bat` in Command Prompt instead |