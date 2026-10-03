"""
dashboard_hmi.py
Streamlit HMI (Human Machine Interface) Dashboard for Modbus TCP Power Meter.
Visualizes real-time telemetry from meter_server.py.
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from pymodbus.client import ModbusTcpClient
import plotly.express as px
import plotly.graph_objects as go

# --- Page Configuration ---
st.set_page_config(
    page_title="Industrial Modbus HMI",
    page_icon="⚡",
    layout="wide"
)

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5020
SLAVE_UNIT_ID = 1

# Alarm Limits
V_ALARM_HIGH = 425.0
V_ALARM_LOW = 400.0
PF_ALARM_LOW = 0.80

if 'df_history' not in st.session_state:
    st.session_state.df_history = pd.DataFrame(columns=['timestamp', 'voltage', 'current', 'power', 'pf'])

st.title("⚡ Industrial Gateway Dashboard (IIoT)")
st.markdown(f"**Modbus TCP Source:** `{SERVER_HOST}:{SERVER_PORT}` (Unit ID: {SLAVE_UNIT_ID})")
st.divider()

@st.cache_resource
def get_modbus_client():
    client = ModbusTcpClient(SERVER_HOST, port=SERVER_PORT)
    client.connect()
    return client

client = get_modbus_client()

def poll_meter():
    if not client.is_socket_open():
        client.connect()
    
    response = client.read_holding_registers(address=0, count=4, slave=SLAVE_UNIT_ID)
    if response.isError():
        st.error(f"Modbus Communication Error: {response}")
        return None
    
    raw = response.registers
    return {
        'timestamp': datetime.now(),
        'voltage': raw[0] / 10.0,
        'current': raw[1] / 10.0,
        'pf': raw[2] / 100.0,
        'power': raw[3] / 10.0
    }

top_col1, top_col2, top_col3 = st.columns([2, 1, 1])

live_data = poll_meter()

if live_data:
    new_row = pd.DataFrame([live_data])
    st.session_state.df_history = pd.concat([st.session_state.df_history, new_row]).tail(60)
    
    with top_col1:
        st.subheader("Live Power Trend (kW)")
        fig_p = px.line(st.session_state.df_history, x='timestamp', y='power', range_y=[0, 150])
        fig_p.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=300)
        st.plotly_chart(fig_p, use_container_width=True)

    with top_col2:
        st.subheader("Line Voltage")
        fig_v = go.Figure(go.Indicator(
            mode="gauge+number",
            value=live_data['voltage'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Volts (V)"},
            gauge={
                'axis': {'range': [380, 440], 'tickwidth': 1},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [380, V_ALARM_LOW], 'color': "#ffcccc"},
                    {'range': [V_ALARM_LOW, V_ALARM_HIGH], 'color': "#e6f3ff"},
                    {'range': [V_ALARM_HIGH, 440], 'color': "#ffcccc"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': V_ALARM_HIGH
                }
            }
        ))
        fig_v.update_layout(height=300, margin=dict(l=10, r=10, t=30, b=10))
        st.plotly_chart(fig_v, use_container_width=True)

    with top_col3:
        st.subheader("Load Current")
        st.metric(label="Current (A)", value=f"{live_data['current']:.1f} A")
        
        st.subheader("Power Factor")
        st.metric(label="PF (lag)", value=f"{live_data['pf']:.2f}")

    st.divider()
    st.subheader("⚠️ Active System Alarms")
    
    alarms_found = False
    if live_data['voltage'] > V_ALARM_HIGH:
        st.error(f"🚨 **HIGH VOLTAGE ALARM** | Reading: **{live_data['voltage']:.1f}V** (Limit: {V_ALARM_HIGH}V)")
        alarms_found = True
    elif live_data['voltage'] < V_ALARM_LOW:
        st.warning(f"⚠️️ **LOW VOLTAGE WARNING** | Reading: **{live_data['voltage']:.1f}V** (Limit: {V_ALARM_LOW}V)")
        alarms_found = True

    if live_data['pf'] < PF_ALARM_LOW:
        st.error(f"🚨 **LOW POWER FACTOR PENALTY RISK** | Reading: **{live_data['pf']:.2f}** (Limit: {PF_ALARM_LOW})")
        alarms_found = True

    if not alarms_found:
        st.success("✅ ALL SYSTEMS NORMAL")

time.sleep(1)
st.rerun()