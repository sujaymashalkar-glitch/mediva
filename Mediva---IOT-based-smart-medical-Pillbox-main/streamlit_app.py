import streamlit as st
import requests
from streamlit_autorefresh import st_autorefresh
from datetime import datetime

# =====================================================
# PAGE CONFIGURATION
# =====================================================
st.set_page_config(
    page_title="MEDIVA | Smart Medication",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# =====================================================
# CUSTOM CSS styling for Healthcare Aesthetics
# =====================================================
st.markdown("""
<style>
    /* Global Clean Font */
    html, body, [class*="css"] {
        font-family: 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Main Background adjustments (handled by config.toml mostly, but strict here) */
    .stApp {
        background-color: #f8fafc;
    }

    /* Card-like containers */
    .css-1r6slb0, .css-12oz5g7 { 
        padding: 1rem; 
    }
    
    .med-card {
        background-color: white;
        padding: 2rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 20px;
        border: 1px solid #e2e8f0;
    }
    
    h1, h2, h3 {
        color: #0f172a;
        font-weight: 600;
    }
    
    .stButton>button {
        background-color: #0284c7;
        color: white;
        border-radius: 8px;
        font-weight: 500;
        padding: 0.5rem 1rem;
        border: none;
        width: 100%;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background-color: #0369a1;
        box-shadow: 0 4px 12px rgba(2, 132, 199, 0.2);
    }
    
    /* Metrics Styling */
    [data-testid="stMetric"] {
        background-color: #f0f9ff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #bae6fd;
        text-align: center;
    }
    [data-testid="stMetricLabel"] {
        color: #64748b;
        font-size: 0.9rem;
    }
    [data-testid="stMetricValue"] {
        color: #0284c7;
        font-weight: 700;
        font-size: 1.8rem;
    }
    
    /* Status Badges */
    .status-badge {
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        text-align: center;
        width: fit-content;
        margin-left: auto; /* Align right in flex context if needed */
    }
    .status-taken { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }
    .status-missed { background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }
    .status-waiting { background-color: #fef9c3; color: #854d0e; border: 1px solid #fde047; }

</style>
""", unsafe_allow_html=True)

# =====================================================
# THINGSPEAK CONFIG
# =====================================================
WRITE_API = "78S00I8D5198MEEY"
READ_API  = "OVJOWI2UVIEUY08V"
CHANNEL_ID = "3232963"

WRITE_URL = "https://api.thingspeak.com/update"
READ_URL  = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds/last.json"

# =====================================================
# AUTO REFRESH
# =====================================================
st_autorefresh(interval=10000, key="refresh")

# =====================================================
# HEADER
# =====================================================
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://cdn-icons-png.flaticon.com/512/883/883407.png", width=80) 
with col2:
    st.title("MEDIVA")
    st.markdown("<p style='color: #64748b; margin-top: -15px; font-size: 1.1rem;'>Smart Medication Assistance and Health Monitoring System</p>", unsafe_allow_html=True)

st.markdown("---")

# =====================================================
# SESSION STATE (STATUS MEMORY)
# =====================================================
if "morning_status" not in st.session_state:
    st.session_state.morning_status = "Waiting"
if "afternoon_status" not in st.session_state:
    st.session_state.afternoon_status = "Waiting"
if "night_status" not in st.session_state:
    st.session_state.night_status = "Waiting"

# =====================================================
# FETCH DATA
# =====================================================
try:
    response = requests.get(READ_URL, params={"api_key": READ_API})
    data = response.json()
    if not isinstance(data, dict):
        data = {}
except:
    data = {}

# Update Logic
def update_status(field_val, current_status):
    if str(field_val) == "1":
        return "Taken"
    elif str(field_val) == "0":
        return "Missed"
    else:
        return current_status

st.session_state.morning_status = update_status(data.get("field4"), st.session_state.morning_status)
st.session_state.afternoon_status = update_status(data.get("field5"), st.session_state.afternoon_status)
st.session_state.night_status = update_status(data.get("field6"), st.session_state.night_status)


# =====================================================
# MAIN LAYOUT
# =====================================================

# Row 1: Vitals & Status
c1, c2 = st.columns([1, 1], gap="large")

with c1:
    st.markdown('<div class="med-card">', unsafe_allow_html=True)
    st.subheader("❤️ Patient Vitals")
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    vc1, vc2 = st.columns(2)
    heart_rate = data.get("field7", "--")
    if heart_rate and heart_rate.isdigit() and int(heart_rate) > 0:
        pass # use value
    else:
        heart_rate = "--"

    spo2 = data.get("field8", "--")
    if spo2 and spo2.isdigit() and int(spo2) > 0:
        pass
    else:
        spo2 = "--"

    with vc1:
        st.metric("Heart Rate", f"{heart_rate} BPM")
    with vc2:
        st.metric("SpO2 Levels", f"{spo2} %")
    
    if "created_at" in data:
        try:
            ts = data["created_at"].replace("Z", "")
            last_time = datetime.fromisoformat(ts)
            st.caption(f"Last vital update: {last_time.strftime('%H:%M:%S')}")
        except:
            pass
            
    st.markdown('</div>', unsafe_allow_html=True)

with c2:
    st.markdown('<div class="med-card">', unsafe_allow_html=True)
    st.subheader("📊 Intake Dashboard")
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    def status_html(label, status, time_icon):
        if status == "Taken":
            cls = "status-taken"
            icon = "✔️"
        elif status == "Missed":
            cls = "status-missed"
            icon = "❌"
        else:
            cls = "status-waiting"
            icon = "⏳"
        
        return f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="font-size: 1.2rem;">{time_icon}</span>
                <span style="font-weight: 500; color: #334155;">{label}</span>
            </div>
            <div class="{cls} status-badge">
                {icon} {status}
            </div>
        </div>
        """

    st.markdown(status_html("Morning", st.session_state.morning_status, "🌅"), unsafe_allow_html=True)
    st.markdown(status_html("Afternoon", st.session_state.afternoon_status, "🌞"), unsafe_allow_html=True)
    st.markdown(status_html("Night", st.session_state.night_status, "🌙"), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)


# Row 2: Configuration (Full Width)
st.markdown('<div class="med-card">', unsafe_allow_html=True)
st.subheader("⚙️ Schedule Configuration")
st.markdown("Configure the medication alarm times for the patient device.")

hours = list(range(24))
minutes = list(range(60))

sc1, sc2, sc3 = st.columns(3)

with sc1:
    st.markdown("#### 🌅 Morning")
    m_h = st.selectbox("Hour", hours, index=9, key="m_h")
    m_m = st.selectbox("Minute", minutes, index=0, key="m_m")

with sc2:
    st.markdown("#### 🌞 Afternoon")
    a_h = st.selectbox("Hour", hours, index=14, key="a_h")
    a_m = st.selectbox("Minute", minutes, index=0, key="a_m")

with sc3:
    st.markdown("#### 🌙 Night")
    n_h = st.selectbox("Hour", hours, index=20, key="n_h")
    n_m = st.selectbox("Minute", minutes, index=0, key="n_m")

morning_time   = f"{m_h:02d}:{m_m:02d}"
afternoon_time = f"{a_h:02d}:{a_m:02d}"
night_time     = f"{n_h:02d}:{n_m:02d}"

st.markdown("<br>", unsafe_allow_html=True)
if st.button("💾 Sync Alarm Times to Device"):
    params = {
    "api_key": WRITE_API,
    "field1": morning_time,
    "field2": afternoon_time,
    "field3": night_time,
    "field4": "",   # reset morning status
    "field5": "",   # reset afternoon status
    "field6": ""    # reset night status
}


    try:
        r = requests.get(WRITE_URL, params=params)
        if r.text != "0":
            st.success("Configuration successfully synced to IoT device.")
            # RESET STATUS FOR NEW CYCLE
            st.session_state.morning_status = "Waiting"
            st.session_state.afternoon_status = "Waiting"
            st.session_state.night_status = "Waiting"
            st.rerun()
        else:
            st.error("Failed to sync. Please check channel write permissions.")
    except:
        st.error("Network error: Could not connect to ThingSpeak.")

st.markdown('</div>', unsafe_allow_html=True)

# =====================================================
# DEBUG (Collapsed)
# =====================================================
with st.expander("🛠️ System Diagnostics"):
    st.code(data)