import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import json
import pandas as pd
from collections import deque
from streamlit_autorefresh import st_autorefresh
import plotly.graph_objects as go
import re
from Machine_Learning import WaterQualityModel
from Sistem_Pakar import evaluate_water_quality, get_recommendations


# =====================================================
# CONFIGURATION & CONSTANTS
# =====================================================

PAGE_CONFIG = {
    "page_title": "SISTEM MONITORING KUALITAS AIR BERBASIS IOT DENGAN PREDIKSI MACHINE LEARNING DAN SISTEM PAKAR",
    "page_icon": "💧",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

    
REFRESH_INTERVAL = 3000  # milliseconds
HISTORY_MAXLEN = 30
DEVICE_TIMEOUT = 15  # seconds - consider device offline if no update within this time

# =====================================================
# SVG ICONS
# =====================================================

SVG_ICONS = {
    "water": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2.69l5.66 5.66a8 8 0 1 1-11.31 0z"/></svg>',
    "chart": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="2" x2="12" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    "settings": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 1v6m0 6v6M4.22 4.22l4.24 4.24m2.12 2.12l4.24 4.24M1 12h6m6 0h6m-15.78 7.78l4.24-4.24m2.12-2.12l4.24-4.24"/></svg>',
    "trending": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 17"/><polyline points="17 6 23 6 23 12"/></svg>',
    "database": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/></svg>',
    "layers": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="12 2 2 7 2 17 12 22 22 17 22 7 12 2"/><polyline points="2 7 12 12 22 7"/><polyline points="2 17 12 12 22 17"/></svg>',
    "target": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="1"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="9"/></svg>',
    "check": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
    "alert": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3.05h16.94a2 2 0 0 0 1.71-3.05L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "info": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    "docs": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="13" x2="8" y2="13"/><line x1="12" y1="17" x2="8" y2="17"/><line x1="16" y1="13" x2="16" y2="17"/></svg>',
    "arrow": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>',
    "wifi": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12.55a11 11 0 0 1 14.08 0"/><path d="M1.42 9a16 16 0 0 1 21.16 0"/><path d="M8.53 16.11a6 6 0 0 1 6.95 0"/><line x1="12" y1="20" x2="12.01" y2="20"/></svg>',
    "cpu": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/></svg>',
    "activity": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
}

RECOMMENDATION_ICONS = {
    "check": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><polyline points="9 12 11 14 15 10"/></svg>',
    "warning": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "error": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
}


# =====================================================
# HELPER FUNCTIONS
# =====================================================

def svg_icon(name: str) -> str:
    """Return SVG icons for professional UI"""
    return SVG_ICONS.get(name, '')


def initialize_session_state():
    """Initialize session state variables"""
    if "ph_hist" not in st.session_state:
        st.session_state.ph_hist = deque(maxlen=HISTORY_MAXLEN)
    if "tds_hist" not in st.session_state:
        st.session_state.tds_hist = deque(maxlen=HISTORY_MAXLEN)
    if "ntu_hist" not in st.session_state:
        st.session_state.ntu_hist = deque(maxlen=HISTORY_MAXLEN)
    if "time_hist" not in st.session_state:
        st.session_state.time_hist = deque(maxlen=HISTORY_MAXLEN)
    if "last_timestamp" not in st.session_state:
        st.session_state.last_timestamp = None
    if "no_update_count" not in st.session_state:
        st.session_state.no_update_count = 0


def init_firebase(key_file, db_url: str) -> tuple:
    """Initialize Firebase with proper error handling"""
    try:
        key_file.seek(0)
        key_dict = json.load(key_file)
        
        if firebase_admin._apps:
            firebase_admin.delete_app(firebase_admin.get_app())
        
        cred = credentials.Certificate(key_dict)
        firebase_admin.initialize_app(
            cred,
            {
                'databaseURL': db_url,
                'databaseAuthVariableOverride': {
                    'uid': 'streamlit-app'
                }
            }   
        )
        return True, "✅ Firebase connected"
    except Exception as e:
        return False, f"❌ Error: {str(e)}"


@st.cache_resource
def load_model():
    """Load ML model with caching"""
    return WaterQualityModel("water_potability_model.pkl")


def get_sensor_data_wib(path: str) -> tuple:
    """Fetch data from Firebase and ensure WIB timestamp"""
    try:
        ref = db.reference(path)
        data = ref.get()

        if not data:
            return None, "Tidak ada data"

        ph = float(data.get("ph", 0))
        tds = float(data.get("tds", 0))
        ntu = float(data.get("ntu", 0))

        # Get timestamp directly from Firebase (no conversion)
        timestamp = data.get("timestamp", "00:00:00")

        return {
            "ph": ph,
            "tds": tds,
            "ntu": ntu,
            "timestamp": timestamp
        }, None

    except Exception as e:
        return None, str(e)


def upload_status_to_firebase(sensor_path: str, status: str, confidence: int):
    """Upload final status and confidence to sensor node in Firebase"""
    try:
        ref = db.reference(sensor_path)
        
        # Update only status and confidence fields in the sensor node
        ref.update({
            "status": status
        })
    except Exception as e:
        st.sidebar.error(f"❌ Error uploading status: {str(e)}")


def check_device_status(no_update_count) -> dict:
    """Check if device is online based on whether sensor data is updating"""
    # If sensor data hasn't changed for 5 consecutive checks (15 seconds)
    # then ESP32 is not sending new data
    max_no_update_checks = 5  # 5 checks x 3 seconds = 15 seconds
    
    if no_update_count >= max_no_update_checks:
        return {
            "is_online": False,
            "message": f"Tidak ada data baru ({no_update_count * 3}s)"
        }
    else:
        return {
            "is_online": True,
            "message": "Menerima data baru"
        }



def create_plotly_chart(data, title: str, color: str, y_label: str):
    """Create Plotly chart for sensor data"""
    fig = go.Figure()
    
    # Convert color hex to rgba
    rgb = tuple(int(color.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
    fill_color = f'rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, 0.1)'
    
    fig.add_trace(go.Scatter(
        y=list(data),
        mode='lines+markers',
        line=dict(color=color, width=2),
        marker=dict(size=6),
        fill='tozeroy',
        fillcolor=fill_color
    ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color='#333')),
        xaxis_title="Time",
        yaxis_title=y_label,
        height=250,
        margin=dict(l=20, r=20, t=40, b=20),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
    )
    
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128,128,128,0.2)')
    
    return fig


def get_status_class(status: str) -> tuple:
    """Get CSS class and text for status"""
    if status == "Layak Minum":
        return "status-safe-full", "LAYAK UNTUK MINUM"
    elif status == "Cukup Layak Minum":
        return "status-moderate-full", "CUKUP LAYAK UNTUK MINUM <br> (Baca rekomendasi tindakan)"
    else:
        return "status-unsafe-full", "TIDAK LAYAK MINUM"


def render_status_and_confidence(status: str, confidence: int):
    """Render status card and confidence box side by side"""
    status_class, status_text = get_status_class(status)
    
    st.markdown(f"""
        <style>
        .equal-height-wrapper {{
            display: flex;
            gap: 15px;
            margin: 20px 0;
        }}
        
        .confidence-box {{
            flex: 0.53;
            background: #f8f8f8;
            border: 2px solid #d0d0d0;
            border-radius: 0px;
            padding: 20px;
            text-align: center;
            min-height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }}
        
        @media (prefers-color-scheme: dark) {{
            .confidence-box {{
                background: #2a2a2a;
                border-color: #404040;
            }}
        }}
        
        .status-box {{
            flex: 2;
            border-radius: 0px;
            text-align: center;
            font-size: 32px;
            font-weight: 700;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
            letter-spacing: 0.5px;
            border: 2px solid;
            min-height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }}
        
        .status-box:hover {{
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }}
        
        .status-safe-full {{
            background: #ffffff;
            color: #059669;
            border-color: #10b981;
        }}
        
        @media (prefers-color-scheme: dark) {{
            .status-safe-full {{
                background: #064e3b;
                color: #a7f3d0;
                border-color: #10b981;
            }}
        }}
        
        .status-moderate-full {{
            background: #cccccc;
            color: #000000;
            border-color: #333333;
        }}
        
        @media (prefers-color-scheme: dark) {{
            .status-moderate-full {{
                background: #78350f;
                color: #fcd34d;
                border-color: #f59e0b;
            }}
        }}
        
        .status-unsafe-full {{
            background: #333333;
            color: #ffffff;
            border-color: #000000;
        }}
        
        @media (prefers-color-scheme: dark) {{
            .status-unsafe-full {{
                background: #7f1d1d;
                color: #fecaca;
                border-color: #dc2626;
            }}
        }}
        
        .confidence-label-inline {{
            font-size: 14px;
            color: #666;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        
        @media (prefers-color-scheme: dark) {{
            .confidence-label-inline {{
                color: #999;
            }}
        }}
        
        .confidence-value-inline {{
            font-size: 48px;
            font-weight: 700;
            color: #000;
            margin: 10px 0;
        }}
        
        @media (prefers-color-scheme: dark) {{
            .confidence-value-inline {{
                color: #fff;
            }}
        }}
        
        .confidence-bar-inline {{
            width: 100%;
            height: 12px;
            background: #e0e0e0;
            border-radius: 0px;
            overflow: hidden;
            margin-top: 10px;
        }}
        
        @media (prefers-color-scheme: dark) {{
            .confidence-bar-inline {{
                background: #404040;
            }}
        }}
        
        .confidence-fill-inline {{
            height: 100%;
            background: linear-gradient(90deg, #333 0%, #000 100%);
            transition: width 0.5s ease;
            width: {confidence}%;
        }}
        
        @media (prefers-color-scheme: dark) {{
            .confidence-fill-inline {{
                background: linear-gradient(90deg, #fff 0%, #ccc 100%);
            }}
        }}
        </style>
        
        <div class="equal-height-wrapper">
            <div class="confidence-box">
                <div class="confidence-label-inline">Tingkat Keyakinan</div>
                <div class="confidence-value-inline">{confidence}%</div>
                <div class="confidence-bar-inline">
                    <div class="confidence-fill-inline"></div>
                </div>
            </div>
            <div class="status-box {status_class}">
                {status_text}
            </div>
        </div>
    """, unsafe_allow_html=True)


def render_decision_explanation(ml_result: str, es_result: str, final_status: str, explanations: list, rule_ids: list, has_active_rules: bool):
    """Render decision explanation card with parallel processing"""
    ml_result_clean = ml_result.strip()
    es_result_clean = es_result.strip()
    
    # Format ML result
    ml_summary = f"<b>Machine Learning:</b> memprediksi kualitas air → <b>{ml_result_clean}</b>"
    
    # Format Expert System result
    if has_active_rules:
        rules_html = "<ul style='margin-top:5px;'>"
        for exp in explanations:
            if exp.startswith("R") or exp.startswith("\nR") or exp.startswith("  R"):
                rules_html += f"<li>{exp.strip()}</li>"
        rules_html += "</ul>"
        es_summary = f"<b>Sistem Pakar:</b> {len(set(rule_ids))} aturan aktif → <b>{es_result_clean}</b>{rules_html}"
    else:
        es_summary = f"<b>Sistem Pakar:</b> ❌ tidak ada aturan yang aktif → <b>{es_result_clean}</b>"
    
    # Format final decision
    if ml_result_clean == final_status and es_result_clean == final_status:
        decision_icon = "✅"
        decision_text = "Kedua sistem setuju"
    elif ml_result_clean != es_result_clean:
        decision_icon = "⚖️"
        if final_status == "Layak Minum":
            decision_text = "Sistem Pakar lebih spesifik → menggunakan hasil Sistem Pakar"
        else:
            decision_text = "Prioritas keamanan → status lebih aman dipilih"
    else:
        decision_icon = "✅"
        decision_text = "Hasil konsisten"
    
    st.markdown(
        f"""
        <div class="decision-card">
            {ml_summary}<br><br>
            {es_summary}<br><br>
            <b>{decision_icon} Kesimpulan:</b> {decision_text} → <b>Status Final: {final_status}</b>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_recommendations(recommendations: list):
    """Render recommendations with icons"""
    rec_html = '<div class="decision-card">'
    
    for rec in recommendations:
        if rec.startswith("✅"):
            icon = RECOMMENDATION_ICONS["check"]
            text = rec.replace("✅ ", "")
            rec_html += f"<h4 style='margin-top:0; display:flex; align-items:center; gap:8px;'>{icon}<span>{text}</span></h4>"
        elif rec.startswith("⚠️"):
            icon = RECOMMENDATION_ICONS["warning"]
            text = rec.replace("⚠️ ", "")
            rec_html += f"<h4 style='margin-top:0; display:flex; align-items:center; gap:8px;'>{icon}<span>{text}</span></h4>"
        elif rec.startswith("❌"):
            icon = RECOMMENDATION_ICONS["error"]
            text = rec.replace("❌ ", "")
            rec_html += f"<h4 style='margin-top:0; display:flex; align-items:center; gap:8px;'>{icon}<span>{text}</span></h4>"
        else:
            rec_html += f"<p style='margin:5px 0;'>{rec}</p>"
    
    rec_html += '</div>'
    st.markdown(rec_html, unsafe_allow_html=True)


def render_pipeline(data, ml_active: bool, es_active: bool):
    """Render system intelligence pipeline with 4 steps"""
    st.markdown("### Pipeline Sistem")
    
    step1_active = True
    step2_active = data is not None
    step3_active = step2_active and ml_active
    step4_active = step2_active and es_active
    
    # 4 columns for pipeline steps with arrows between them
    col_p1, col_arrow1, col_p2, col_arrow2, col_p3, col_arrow3, col_p4 = st.columns([2, 0.5, 2, 0.5, 2, 0.5, 2])
    
    with col_p1:
        active_class = "pipeline-active" if step1_active else ""
        st.markdown(f'<div class="pipeline-step {active_class}">Sensor IoT<br><span style="font-size:12px;opacity:0.8">ESP32</span></div>', unsafe_allow_html=True)
    
    with col_arrow1:
        st.markdown("<div style='text-align:center; color:#999; margin-top:30px; font-size:20px'>→</div>", unsafe_allow_html=True)
    
    with col_p2:
        active_class = "pipeline-active" if step2_active else ""
        st.markdown(f'<div class="pipeline-step {active_class}">Firebase<br><span style="font-size:12px;opacity:0.8">Database Realtime</span></div>', unsafe_allow_html=True)
    
    with col_arrow2:
        st.markdown("<div style='text-align:center; color:#999; margin-top:30px; font-size:20px'>→</div>", unsafe_allow_html=True)
    
    with col_p3:
        ml_class = "pipeline-active" if step3_active else ""
        st.markdown(f'<div class="pipeline-step {ml_class}">Model ML<br><span style="font-size:12px;opacity:0.8">Random Forest</span></div>', unsafe_allow_html=True)
    
    with col_arrow3:
        st.markdown("<div style='text-align:center; color:#999; margin-top:30px; font-size:20px'>→</div>", unsafe_allow_html=True)
    
    with col_p4:
        es_class = "pipeline-active" if step4_active else ""
        st.markdown(f'<div class="pipeline-step {es_class}">Sistem Pakar<br><span style="font-size:12px;opacity:0.8">Fuzzy Logic</span></div>', unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 40px;'></div>", unsafe_allow_html=True)


def render_documentation():
    """Render technical documentation"""
    with st.expander("Dokumentasi Teknis & Standar Klasifikasi", expanded=False):
        doc_tab1, doc_tab2, doc_tab3 = st.tabs([
            "📊 Parameter Kualitas Air",
            "⚖️ Aturan Inferensi Sistem Pakar",
            "🔬 Penjelasan Sistem"
        ])
        
        with doc_tab1:
            st.markdown("##### Ambang Batas Parameter (Standar WHO)")
            
            st.markdown("**Tabel 1: Klasifikasi Tingkat pH**")
            ph_df = pd.DataFrame({
                'Klasifikasi': ['Asam', 'Sedikit Asam', 'Netral', 'Sedikit Basa', 'Basa'],
                'Rentang': ['≤ 6.5', '6.6 - 6.9', '7.0', '7.1 - 8.5', '≥ 8.6'],
                'Penilaian': ['Tidak Layak', 'Cukup', 'Optimal', 'Cukup', 'Tidak Layak']
            })
            st.dataframe(ph_df, hide_index=True, use_container_width=True)
            
            st.markdown("**Tabel 2: Klasifikasi Total Padatan Terlarut (TDS)**")
            tds_df = pd.DataFrame({
                'Klasifikasi': ['Sempurna', 'Baik', 'Cukup', 'Buruk', 'Tidak Diterima'],
                'Rentang (mg/L)': ['≤ 300', '301 - 600', '601 - 900', '901 - 1199', '≥ 1200'],
                'Penilaian': ['Layak', 'Layak', 'Cukup Layak', 'Tidak Layak', 'Tidak Layak']
            })
            st.dataframe(tds_df, hide_index=True, use_container_width=True)
            
            st.markdown("**Tabel 3: Klasifikasi Kekeruhan**")
            turb_df = pd.DataFrame({
                'Klasifikasi': ['Sempurna', 'Baik', 'Cukup', 'Buruk', 'Tidak Diterima'],
                'Rentang (NTU)': ['≤ 1', '1.1 - 5', '5.1 - 25.0', '25.1 - 100', '≥ 100'],
                'Penilaian': ['Layak', 'Layak', 'Cukup Layak', 'Tidak Layak', 'Tidak Layak']
            })
            st.dataframe(turb_df, hide_index=True, use_container_width=True)
        
        with doc_tab2:
            st.markdown("##### Aturan Inferensi Logika Fuzzy (R1–R24)")
            
            st.markdown("**Kondisi Tidak Layak Minum**")
            st.markdown("""
            - **R1:** IF pH *Asam* (< 6,5) → STATUS *Tidak Layak Minum*  
            - **R2:** IF pH *Basa* (> 8,5) → STATUS *Tidak Layak Minum*  
            - **R3:** IF TDS *Buruk* (500 – 900 mg/L) → STATUS *Tidak Layak Minum*  
            - **R4:** IF TDS *Tidak Diterima* (> 900 mg/L) → STATUS *Tidak Layak Minum*  
            - **R5:** IF Kekeruhan *Buruk* (10 – 25 NTU) → STATUS *Tidak Layak Minum*  
            - **R6:** IF Kekeruhan *Tidak Diterima* (> 25 NTU) → STATUS *Tidak Layak Minum*  
            """)
            
            st.markdown("**Kondisi Cukup Layak Minum**")
            st.markdown("""
            - **R7:** IF pH *Sedikit Asam* AND TDS *Cukup* AND Kekeruhan *Cukup*  
            - **R8:** IF pH *Sedikit Basa* AND TDS *Cukup* AND Kekeruhan *Cukup*  
            - **R9:** IF pH *Netral* AND TDS *Cukup* AND Kekeruhan *Baik*  
            - **R10:** IF pH *Netral* AND TDS *Baik* AND Kekeruhan *Cukup*
            - **R11:** IF pH *Netral* AND TDS *Sempurna* AND Kekeruhan *Baik* 
            - **R12:** IF pH *Netral* AND TDS *Baik* AND Kekeruhan *Sempurna*
            - **R13:** IF pH *Sedikit Asam* AND TDS *Baik* AND Kekeruhan *Baik*  
            - **R14:** IF pH *Sedikit Basa* AND TDS *Baik* AND Kekeruhan *Baik*
            - **R15:** IF pH *Sedikit Asam* AND TDS *Baik* AND Kekeruhan *Sempurna*
            - **R16:** IF pH *Sedikit Basa* AND TDS *Baik* AND Kekeruhan *Sempurna*
            - **R17:** IF pH *Sedikit Asam* AND TDS *Sempurna* AND Kekeruhan *Baik*
            - **R18:** IF pH *Sedikit Basa* AND TDS *Sempurna* AND Kekeruhan *Baik*                     
            """)
            
            st.markdown("**Kondisi Layak Minum**")
            st.markdown("""
            - **R19:** IF pH *Sedikit Asam* AND TDS *Sempurna* AND Kekeruhan *Sempurna*
            - **R20:** IF pH *Sedikit Basa* AND TDS *Sempurna* AND Kekeruhan *Sempurna*
            - **R21:** IF pH *Netral* AND TDS *Sempurna* AND Kekeruhan *Sempurna*  
            - **R22:** IF pH *Netral* AND TDS *Baik* AND Kekeruhan *Baik*  
            - **R23:** IF pH *Netral* AND TDS *Sempurna* AND Kekeruhan *Baik*  
            - **R24:** IF pH *Netral* AND TDS *Baik* AND Kekeruhan *Sempurna*  
            """)
            
            st.info(
                "**Catatan:** Aturan inferensi disusun berdasarkan standar WHO dan "
                "divalidasi oleh pakar menggunakan Logika Fuzzy untuk menangani ketidakpastian "
                "pengukuran parameter kualitas air."
            )
        
        with doc_tab3:
            st.markdown("##### Penjelasan Sistem")
            
            st.markdown("""
            **IOT → Machine Learning ⚡ Sistem Pakar (Parallel Processing)**
            
            Sistem ini menggunakan **pendekatan paralel** untuk meningkatkan 
            akurasi dan kepercayaan dalam evaluasi kualitas air:
            
            **Tahap 1: Analisis Paralel**
            - **Machine Learning (Random Forest)** dan **Sistem Pakar (Fuzzy Logic)** berjalan **bersamaan**
            - Kedua sistem menganalisis parameter yang sama secara **independen**
            - ML menggunakan pola dari 13.276 sampel historis
            - Sistem Pakarmenggunakan 16 aturan berbasis standar WHO yang telah di validasi oleh pakar
            
            **Tahap 2: Kombinasi Hasil**
            - Jika **kedua sistem setuju** → gunakan hasil tersebut
            - Jika **hasil berbeda**:
              - **ML: Tidak Layak, Sistem Pakar: Layak** → Gunakan hasil Sistem Pakar (rule-based lebih spesifik)
              - **ML: Layak, Sistem Pakar: Tidak Layak** → Gunakan hasil Sistem Pakar (prioritas keamanan)
            
            **Keunggulan Pendekatan Parallel:**
            - **Redundansi**: Dua sistem independen meningkatkan reliabilitas
            - **Cross-Validation**: Hasil saling memvalidasi
            - **Fleksibilitas**: Dapat menangani edge cases dari kedua sisi
            - **Transparansi**: Semua hasil ditampilkan untuk audit
            - **Safety First**: Prioritas pada keamanan air minum
            
            **Tingkat Keyakinan (Confidence Level):**
            - **95-100%**: Kedua sistem setuju + parameter ideal (Rule R13-R16)
            - **85-94%**: Kedua sistem setuju + kondisi baik
            - **75-84%**: Sistem berbeda pendapat (gunakan yang lebih aman)
            - **60-74%**: Tidak ada rule aktif pada Sistem Pakar
            """)
            
            st.markdown("**Diagram Alur Keputusan:**")
            st.code("""
                    
                                            ┌─────────────────────┐
                                            │    Sensor Data      │
                                            └──────────┬──────────┘
                                                       │
                                                       ▼
                                            ┌─────────────────────┐
                                            │    Firebase DB      │
                                            └────┬───────────┬────┘
                                                 │           │
                                                 ▼           ▼
                                    ┌─────────────────┐ ┌─────────────────┐
                                    │     ML Model    │ │  Sistem Pakar   │
                                    │ (Random Forest) │ │(16 Fuzzy Rules) │
                                    └────────┬────────┘ └───────┬─────────┘
                                             │                  │
                                             ▼                  ▼
                                        ┌──────────┐     ┌─────────────┐
                                        │ Prediksi │     │  Validasi   │
                                        └────┬─────┘     └──────┬──────┘
                                             │                  │
                                             └─────────┬────────┘
                                                       │
                                                       ▼
                                   ┌────────────────────────────────────────┐
                                   │  Final Decision (Status + Confidence)  │
                                   │      ↓ Upload to Firebase ↓            │
                                   └────────────────────────────────────────┘
                    
                        """, language="text")


def render_welcome_screen():
    """Render welcome screen when Firebase is not connected"""
    st.markdown("""
    <div class="info-box">
        <h3>Konfigurasi Firebase Diperlukan</h3>
        <p>Konfigurasi Firebase melalui bilah samping untuk mengaktifkan pemantauan kualitas air secara real-time.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Langkah Setup Awal")
        st.markdown("""
        **1. Buat Proyek Firebase**  
        Buat proyek baru di Firebase Console.

        **2. Aktifkan Database Realtime**  
        Aktifkan Database Realtime dan salin URL Database
        """)
        
        st.code("https://nama-proyek.asia-southeast1.firebasedatabase.app/", language="text")
        
        st.markdown("""
        **3. Konfigurasi Akun Layanan**  
        Unduh JSON Akun Layanan dari Pengaturan Proyek.
                    
        **4. Tentukan Path Database**  
        Tentukan path atau node di Database Realtime yang akan digunakan untuk menyimpan dan mengambil data.
        """)
    
    with col2:
        st.subheader("Kemampuan Sistem")
        st.markdown("""
        **Pemantauan Real-time**  
        Akuisisi dan visualisasi data sensor otomatis setiap 3 detik.

        **Machine Learning**  
        Prediksi menggunakan algoritma Random Forest berdasarkan pH, TDS, dan kekeruhan.

        **Sistem Pakar**  
        Validasi prediksi menggunakan 16 aturan berdasarkan standar WHO dan pengetahuan pakar.
        
        **Confidence Level**  
        Tingkat keyakinan 0-100% untuk transparansi keputusan.
        
        **Device Status**  
        Status perangkat ESP32 secara real-time dalam tampilan kompak.
        
        **Firebase Upload**  
        Status final dan confidence otomatis diupload ke Firebase.
        """)
    
    st.divider()
    
    with st.expander("Aturan Akses Database Realtime", expanded=False):
        st.code("""
{
    "rules": {
        ".read": true,
        ".write": true
    }
}
        """, language="json")
        st.warning("⚠️ Konfigurasi untuk pengembangan saja. Gunakan autentikasi yang lebih ketat.")
    
    st.divider()
    
    st.subheader("Instruksi Penggunaan")
    
    steps = st.columns(5)
    
    step_data = [
        ("1", "URL Database", "Masukkan di bilah samping", "#ffffff", "#000000"),
        ("2", "Database Path", "Tentukan node di Firebase", "#e8e8e8", "#333333"),
        ("3", "Unggah JSON", "File Akun Layanan", "#ffffff", "#000000"),
        ("4", "Koneksi", "Terhubung otomatis", "#e8e8e8", "#333333"),
        ("5", "Pemantauan", "Dashboard real-time", "#ffffff", "#000000")
    ]
    
    for idx, (num, title, desc, bg, border) in enumerate(step_data):
        with steps[idx]:
            st.markdown(f"""
            <div style='text-align: center; padding: 12px; background: {bg}; border: 2px solid {border}; border-radius: 0px;'>
                <h3 style='margin-top: 0; color: #000000;'>{num}</h3>
                <p style='color: #1a1a1a; margin-bottom: 0;'>
                    <strong>{title}</strong><br>
                    <span style='font-size: 12px;'>{desc}</span>
                </p>
            </div>
            """, unsafe_allow_html=True)


def load_custom_css():
    """Load custom CSS styles"""
    st.markdown("""
    <style>
    * {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    .main {
        padding: 1.5rem 2rem;
        background: #ffffff;
    }
    
    @media (prefers-color-scheme: dark) {
        .main {
            background: #1a1a1a;
        }
    }
    
    /* HEADER STYLING */
    h1 {
        color: #000000;
        text-align: center;
        padding: 15px 0 5px 0;
        font-size: 2.8em;
        font-weight: 700;
        letter-spacing: -0.5px;
        margin-bottom: 5px;
    }
    
    @media (prefers-color-scheme: dark) {
        h1 {
            color: #ffffff;
        }
    }
    
    h2 {
        color: #1a1a1a;
        border-left: 3px solid #000000;
        padding-left: 12px;
        margin-top: 25px;
        margin-bottom: 15px;
        font-size: 1.4em;
        font-weight: 600;
    }
    
    @media (prefers-color-scheme: dark) {
        h2 {
            color: #ffffff;
            border-left-color: #ffffff;
        }
    }
    
    h3 {
        color: #1a1a1a;
        font-size: 1.1em;
        font-weight: 600;
        margin-top: 15px;
        margin-bottom: 10px;
    }
    
    @media (prefers-color-scheme: dark) {
        h3 {
            color: #ffffff;
        }
    }
    
    h4 {
        color: #2a2a2a;
        font-weight: 600;
        margin-top: 12px;
        margin-bottom: 8px;
    }
    
    @media (prefers-color-scheme: dark) {
        h4 {
            color: #e0e0e0;
        }
    }
    
    /* METRIC CARDS */
    .stMetric {
        background: #f8f8f8;
        padding: 20px 12px !important;
        border-radius: 0px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        border: 1px solid #d0d0d0;
        transition: all 0.3s ease;
        min-height: 120px !important;
        height: 120px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    
    .stMetric:hover {
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
        border-color: #808080;
    }
    
    @media (prefers-color-scheme: dark) {
        .stMetric {
            background: #2a2a2a;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
            border: 1px solid #404040;
        }
        
        .stMetric:hover {
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
            border-color: #606060;
        }
    }
    
    /* Force equal height for ALL metric containers */
    [data-testid="metric-container"] {
        height: 120px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    
    [data-testid="stMetric"] {
        height: 120px !important;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        line-height: 1.2 !important;
    }
    
    div[data-testid="stMetricLabel"] {
        font-size: 0.95rem !important;
        margin-bottom: 8px !important;
    }
    
    div[data-testid="stMetricDelta"] {
        font-size: 0.85rem !important;
    }
    
    /* INFO/ALERT BOXES */
    .info-box {
        background: #f0f0f0;
        border-left: 3px solid #000000;
        border-radius: 0px;
        padding: 12px;
        color: #1a1a1a;
        font-size: 0.95em;
    }
    
    @media (prefers-color-scheme: dark) {
        .info-box {
            background: #2a2a2a;
            border-left-color: #ffffff;
            color: #e0e0e0;
        }
    }
    
    .info-panel {
        background: #f8f8f8;
        border: 1px solid #d0d0d0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
    }
    
    @media (prefers-color-scheme: dark) {
        .info-panel {
            background: #2a2a2a;
            border-color: #404040;
        }
    }
    
    .info-panel h4 {
        margin-top: 0;
        margin-bottom: 10px;
        font-size: 16px;
    }
    
    .info-panel p {
        margin: 5px 0;
        font-size: 14px;
    }
    
    .stAlert {
        border-radius: 0px;
        padding: 10px 12px;
        margin: 10px 0;
        border-left: 3px solid;
        font-size: 0.95em;
    }
    
    /* DECISION CARD */
    .decision-card {
        background-color: #e0e0e0;
        color: #1a1a1a;
        border: 2px solid #a0a0a0;
        border-radius: 10px;
        padding: 15px;
        font-size: 14px;
        line-height: 1.5;
        margin: 10px 0;
    }

    @media (prefers-color-scheme: dark) {
        .decision-card {
            background-color: #2a2a2a;
            color: #f0f0f0;
            border: 2px solid #555555;
        }
    }

    .decision-card ul {
        padding-left: 18px;
        margin-top: 5px;
    }
    
    /* PIPELINE SECTION */
    .pipeline-step {
        background: #f5f5f5;
        border: 2px solid #333333;
        border-radius: 0px;
        padding: 15px;
        text-align: center;
        font-weight: 600;
        font-size: 0.9em;
        transition: all 0.3s ease;
        color: #1a1a1a;
        min-height: 85px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .pipeline-step.pipeline-active {
        background: #ffffff;
        border-color: #000000;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
        color: #000000;
    }
    
    @media (prefers-color-scheme: dark) {
        .pipeline-step {
            background: #1f1f1f;
            border-color: #505050;
            color: #e0e0e0;
        }
        
        .pipeline-step.pipeline-active {
            background: #2a2a2a;
            border-color: #ffffff;
            color: #ffffff;
        }
    }
    
    /* EXPANDABLE SECTIONS */
    .streamlit-expanderHeader {
        background: #f0f0f0;
        border-radius: 0px;
        padding: 10px 12px;
        border: 1px solid #d0d0d0;
        transition: all 0.2s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: #e5e5e5;
        border-color: #808080;
    }
    
    @media (prefers-color-scheme: dark) {
        .streamlit-expanderHeader {
            background: #252525;
            border-color: #404040;
        }
        
        .streamlit-expanderHeader:hover {
            background: #2a2a2a;
            border-color: #606060;
        }
    }
    
    /* DIVIDERS & SPACING */
    hr {
        margin: 20px 0;
        opacity: 0.5;
        height: 1px;
        background: #808080;
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        background: #ffffff;
        border: 1px solid #d0d0d0;
        border-radius: 0px;
        transition: all 0.2s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: #000000;
        border-color: #000000;
        color: white;
    }
    
    @media (prefers-color-scheme: dark) {
        .stTabs [data-baseweb="tab"] {
            background: #1f1f1f;
            border-color: #404040;
        }
        
        .stTabs [aria-selected="true"] {
            background: #ffffff;
            color: #000000;
            border-color: #ffffff;
        }
    }
    
    /* DATAFRAME */
    .stDataframe {
        border-radius: 0px;
        overflow: hidden;
    }
    
    /* GENERAL ELEMENTS */
    .stColumns {
        gap: 15px;
    }
    
    [data-testid="stBlock"] {
        margin-bottom: 8px;
    }
    </style>
    """, unsafe_allow_html=True)


# =====================================================
# MAIN APPLICATION
# =====================================================

def main():
    """Main application function"""
    # Page configuration
    st.set_page_config(**PAGE_CONFIG)
    
    # Load custom CSS
    load_custom_css()
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown("<h1>SISTEM MONITORING KUALITAS AIR BERBASIS IOT DENGAN PREDIKSI MACHINE LEARNING DAN SISTEM PAKAR</h1>", unsafe_allow_html=True)
    st.markdown("""
        <p style='text-align: center; color: #666; font-size: 15px; margin-bottom: 5px;'>
        Pemantauan real-time dengan Machine Learning ⚡ Sistem Pakar (Parallel Processing)
        </p>
    """, unsafe_allow_html=True)
    st.divider()
    
    # Sidebar - Firebase Configuration
    with st.sidebar:
        st.title("Konfigurasi")
        
        with st.expander("Pengaturan Firebase", expanded=True):
            firebase_url = st.text_input(
                "Database URL",
                placeholder="https://project-id.firebaseio.com/",
                help="URL dari Firebase Realtime Database"
            )
            
            db_path = st.text_input(
                "Database Path (Sensor Data)",
                value="sensor",
                help="Path lokasi data sensor di database (status akan disimpan di node yang sama)"
            )
            
            firebase_key = st.file_uploader(
                "Service Account JSON",
                type=["json"],
                help="Upload file JSON dari Firebase Console"
            )
        
        st.markdown("---")
        
        with st.expander("Informasi Sistem"):
            st.info("""
            **Model ML:** Random Forest  
            **Aturan:** 16 Fuzzy Logic  
            **Mode:** Parallel Processing
            **Update:** Real-time (3s)
            **Firebase Upload:** Aktif
            """)
        
        st.markdown("---")
    
    # Connect to Firebase
    firebase_connected = False
    
    if firebase_url and firebase_key:
        if not firebase_url.startswith("https://") or not firebase_url.endswith("/"):
            st.sidebar.warning("⚠️ URL harus format: https://...firebaseio.com/")
        else:
            success, message = init_firebase(firebase_key, firebase_url)
            
            if success:
                firebase_connected = True
                st.sidebar.success(message)
            else:
                st.sidebar.error(message)
    
    # Auto refresh if connected
    if firebase_connected:
        st_autorefresh(interval=REFRESH_INTERVAL, key="refresh")
    
    # Main dashboard logic
    if firebase_connected:
        data, error = get_sensor_data_wib(db_path)
        
        if error:
            st.error(f"Error mengambil data: {error}")
            st.info("""
            **Pemecahan Masalah:**
            1. Periksa Firebase Rules (harus allow read/write)
            2. Verifikasi path database
            3. Periksa koneksi internet
            """)
        
        elif not data:
            st.warning(f"Tidak ada data di path: `{db_path}`")
            st.info("Pastikan sensor ESP32 mengirim data ke Firebase")
        
        else:
            # Parse sensor data
            ph = float(data.get("ph", 0))
            tds = float(data.get("tds", 0))
            ntu = float(data.get("ntu", 0))
            timestamp = data.get("timestamp", "00:00:00")  # Direct from Firebase
            
            # Create a data signature from sensor values (not timestamp)
            # Round values to avoid floating point precision issues
            current_data_signature = f"{ph:.2f}|{tds:.1f}|{ntu:.2f}"
            
            # Check if data has changed (ESP32 is sending new data)
            if st.session_state.last_timestamp is None:
                # First run
                st.session_state.last_timestamp = current_data_signature
                st.session_state.no_update_count = 0
            elif current_data_signature == st.session_state.last_timestamp:
                # Data hasn't changed - ESP32 not sending new data
                st.session_state.no_update_count += 1
            else:
                # Data has changed - ESP32 is sending new data
                st.session_state.last_timestamp = current_data_signature
                st.session_state.no_update_count = 0
            
            # Check device status based on data updates
            device_status = check_device_status(st.session_state.no_update_count)
            is_online = device_status["is_online"]
            status_message = device_status["message"]
            
            # Update history
            st.session_state.ph_hist.append(ph)    
            st.session_state.tds_hist.append(tds)
            st.session_state.ntu_hist.append(ntu)
            st.session_state.time_hist.append(timestamp)
            
            # 1. COMPACT DEVICE STATUS
            if is_online:
                status_bg = "#333333"
                status_bg_dark = "#064e3b"
                status_border = "#059669"
                status_dot = "#059669"
                status_text = "ESP32 Online"
                status_text_color = "#ffffff"
                status_text_color_dark = "#a7f3d0"
                status_icon = "✓"
                status_detail_color = "#e5e5e5"
                status_detail_color_dark = "#6ee7b7"
            else:
                status_bg = "#333333"
                status_bg_dark = "#7f1d1d"
                status_border = "#dc2626"
                status_dot = "#dc2626"
                status_text = "ESP32 Offline"
                status_text_color = "#ffffff"
                status_text_color_dark = "#fecaca"
                status_icon = "✗"
                status_detail_color = "#e5e5e5"
                status_detail_color_dark = "#fca5a5"
            
            st.markdown(f"""
                <div style='
                    background: {status_bg};
                    border: 2px solid {status_border};
                    border-radius: 8px;
                    padding: 12px 20px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 20px;
                '>
                    <div style='display: flex; align-items: center; gap: 10px;'>
                        <div style='
                            width: 12px;
                            height: 12px;
                            border-radius: 50%;
                            background: {status_dot};
                            animation: pulse-device 2s ease-in-out infinite;
                            box-shadow: 0 0 8px {status_dot};
                        '></div>
                        <span style='font-weight: 600; color: {status_text_color}; font-size: 14px;'>
                            {status_text}
                        </span>
                    </div>
                    <div style='display: flex; align-items: center; gap: 15px; font-size: 13px; color: {status_detail_color};'>
                        <span>{status_icon} {status_message}</span>
                        <span>⏱{timestamp}</span>
                    </div>
                </div>
                
                <style>
                @keyframes pulse-device {{
                    0%, 100% {{ opacity: 1; transform: scale(1); }}
                    50% {{ opacity: 0.6; transform: scale(1.2); }}
                }}
                
                @media (prefers-color-scheme: dark) {{
                    div[style*='background: {status_bg}'] {{
                        background: {status_bg_dark} !important;
                    }}
                    div[style*='color: {status_text_color}'] {{
                        color: {status_text_color_dark} !important;
                    }}
                    div[style*='color: {status_detail_color}'] {{
                        color: {status_detail_color_dark} !important;
                    }}
                }}
                </style>
            """, unsafe_allow_html=True)
            
            # Show warning if offline
            if not is_online:
                st.warning(f"⚠️ **ESP32 tidak mengirim data baru ke Firebase.** Data terakhir diterima {st.session_state.no_update_count * 3} detik yang lalu. Pastikan ESP32 terhubung ke WiFi dan Firebase.")
            
            # 2. CHARTS & TRENDS
            st.markdown("### Tren Historis")
            
            chart_col1, chart_col2, chart_col3 = st.columns(3)
            
            with chart_col1:
                fig_ph = create_plotly_chart(
                    st.session_state.ph_hist,
                    "pH Level Trend",
                    "#1f77b4",
                    "pH"
                )
                st.plotly_chart(fig_ph, use_container_width=True)
            
            with chart_col2:
                fig_tds = create_plotly_chart(
                    st.session_state.tds_hist,
                    "TDS Trend",
                    "#ff7f0e",
                    "TDS (ppm)"
                )
                st.plotly_chart(fig_tds, use_container_width=True)
            
            with chart_col3:
                fig_ntu = create_plotly_chart(
                    st.session_state.ntu_hist,
                    "Turbidity Trend",
                    "#2ca02c",
                    "NTU"
                )
                st.plotly_chart(fig_ntu, use_container_width=True)
            
            # 3. REAL-TIME METRICS
            st.markdown("### Data Sensor Real-time")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                ph_delta = ph - 7.0 if len(st.session_state.ph_hist) > 1 else None
                
                if ph_delta is not None and len(st.session_state.ph_hist) >= 2:
                    previous_ph = st.session_state.ph_hist[-2]
                    
                    # Cek apakah pH melewati nilai 7 (crossing)
                    crossed_neutral = (previous_ph < 7.0 and ph > 7.0) or (previous_ph > 7.0 and ph < 7.0)
                    
                    # Hitung jarak dari 7
                    current_distance = abs(ph - 7.0)
                    previous_distance = abs(previous_ph - 7.0)
                    
                    # Jika melewati 7 = merah
                    # Jika tidak melewati 7:
                    #   - mendekati 7 = hijau
                    #   - menjauhi 7 = merah
                    if crossed_neutral:
                        ph_delta_color = "inverse"  # merah (melewati 7)
                    elif current_distance < previous_distance:
                        ph_delta_color = "normal"   # hijau (mendekati 7)
                    else:
                        ph_delta_color = "inverse"  # merah (menjauhi 7)
                else:
                    ph_delta_color = "off"
                
                st.metric(
                    label="pH",
                    value=f"{ph:.2f}",
                    delta=f"{ph_delta:+.2f}" if ph_delta is not None else None,
                    delta_color=ph_delta_color
                )
            with col2:
                tds_delta_color = "inverse"
                tds_delta = tds - 900 if len(st.session_state.tds_hist) > 1 else None
                st.metric(
                    label="TDS",
                    value=f"{tds:.1f} ppm",
                    delta=f"{tds_delta:.1f}" if tds_delta is not None else None,
                    delta_color=tds_delta_color
                )

            with col3:
                ntu_delta_color = "inverse"
                ntu_delta = ntu - 25 if len(st.session_state.ntu_hist) > 1 else None
                st.metric(
                    label="Kekeruhan",
                    value=f"{ntu:.2f} NTU",
                    delta=f"{ntu_delta:.2f}" if ntu_delta is not None else None,
                    delta_color=ntu_delta_color
                )

            with col4:
                st.metric(
                    label="Update Terakhir",
                    value=timestamp
                )
            
            # 4. AI ANALYSIS & FINAL STATUS - PARALLEL PROCESSING
            model = load_model()
            
            # *** PARALLEL HYBRID WORKFLOW ***
            # Tahap 1: Machine Learning - berjalan independen
            ml_result = model.predict(ph, tds, ntu)
            ml_confidence = 85  # Confidence ML
            
            # Tahap 2: Expert System - berjalan independen (selalu dijalankan)
            es_result, es_explanations, es_confidence, has_active_rules = evaluate_water_quality(ph, tds, ntu, None)
            rule_ids = re.findall(r"R\d+", " ".join(es_explanations))
            
            # Tahap 3: Kombinasi hasil (Voting Logic)
            # Jika keduanya setuju → gunakan hasil tersebut
            # Jika berbeda → prioritaskan yang lebih aman atau rule-based
            
            if ml_result == "Layak Minum" and es_result == "Layak Minum":
                # Kedua sistem setuju: Layak Minum
                status = "Layak Minum"
                confidence = max(ml_confidence, es_confidence)
                explanations = es_explanations
            
            elif ml_result == "Tidak Layak Minum" and es_result == "Tidak Layak Minum":
                # Kedua sistem setuju: Tidak Layak Minum
                status = "Tidak Layak Minum"
                confidence = max(ml_confidence, es_confidence)
                explanations = es_explanations
            
            elif ml_result == "Tidak Layak Minum" and es_result == "Layak Minum":
                # ML: Tidak Layak, ES: Layak → Prioritaskan ES (rule-based lebih spesifik)
                status = "Layak Minum"
                confidence = es_confidence
                explanations = es_explanations
                explanations.append("\n⚠️ ML memprediksi 'Tidak Layak', namun Sistem Pakar mendeteksi kondisi aman berdasarkan aturan spesifik")

            elif ml_result == "Tidak Layak Minum" and es_result == "Cukup Layak Minum":
                # ML: Tidak Layak, ES: Cukup Layak → Prioritaskan ES (rule-based lebih spesifik)
                status = "Cukup Layak Minum"
                confidence = es_confidence
                explanations = es_explanations
                explanations.append("\n⚠️ ML memprediksi 'Tidak Layak', namun Sistem Pakar mendeteksi kondisi cukup aman berdasarkan aturan spesifik")
            
            elif ml_result == "Layak Minum" and es_result == "Cukup Layak Minum":
                # ML: Layak, ES: Cukup Layak → Prioritaskan ES (rule-based lebih spesifik)
                status = "Cukup Layak Minum"
                confidence = es_confidence
                explanations = es_explanations
                explanations.append("\n⚠️ ML memprediksi 'Layak Minum', namun Sistem Pakar mendeteksi kondisi cukup aman berdasarkan aturan spesifik")

            
            else:  # ml_result == "Layak Minum" and es_result == "Tidak Layak Minum"
                # ML: Layak, ES: Tidak Layak → Prioritaskan keamanan (Tidak Layak)
                status = "Tidak Layak Minum"
                confidence = es_confidence if has_active_rules else 75
                explanations = es_explanations
                if not has_active_rules:
                    explanations.append("\n⚠️ ML memprediksi 'Layak Minum', tetapi tidak ada aturan yang aktif di Sistem Pakar")
                else:
                    explanations.append("\n⚠️ ML memprediksi 'Layak Minum', tetapi Sistem Pakar mendeteksi kondisi tidak aman berdasarkan aturan")
            
            # **UPLOAD STATUS TO FIREBASE (same node as sensor)**
            upload_status_to_firebase(db_path, status, confidence)
            
            # Status Card + Confidence
            st.markdown("### Status Kualitas Air")
            render_status_and_confidence(status, confidence)
            
            # Decision Explanation
            st.markdown("### Penjelasan Keputusan")
            render_decision_explanation(ml_result, es_result, status, explanations, rule_ids, has_active_rules)
            
            # Recommendations
            st.markdown("### Rekomendasi Tindakan")
            recommendations = get_recommendations(status, ph, tds, ntu)
            render_recommendations(recommendations)
            
            # System Pipeline
            render_pipeline(data, True, True)
            
            # Technical Documentation
            render_documentation()
    
    else:
        # Welcome screen
        render_welcome_screen()


if __name__ == "__main__":
    main()