import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import LocateControl
import json
import os
import time

# --- НАЛАШТУВАННЯ ---
DB_FILE = "zones.json"
POLTAVA_COORDS = [49.5894, 34.5510]
TG_BOT_USERNAME = "PoltavaParking_AndreBot" 
ADMIN_PASSWORD = "123" # 🔴 ПАРОЛЬ ТУТ

st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="Parking Poltava")

# --- CSS СТИЛІ (ВИПРАВЛЕНІ) ---
st.markdown("""
    <style>
        /* 1. Робимо верхню панель прозорою, щоб було видно стрілочку меню */
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0);
        }
        
        /* 2. Ховаємо "гамбургер" (три крапки справа), щоб не заважав */
        [data-testid="stToolbar"] {
            visibility: hidden;
        }

        /* 3. Ховаємо футер "Made with Streamlit" */
        footer {visibility: hidden;}
        
        /* 4. Прибираємо відступи */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            max-width: 100% !important;
        }
        div[data-testid="stVerticalBlock"] { gap: 0 !important; }

        /* 🔥 СТИЛЬ КНОПКИ (Як була) 🔥 */
        .floating-btn {
            position: fixed;
            bottom: 40px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            background: linear-gradient(135deg, #0088cc 0%, #005f99 100%);
            color: white !important;
            padding: 15px 35px;
            border-radius: 50px;
            text-decoration: none !important;
            font-family: sans-serif;
            font-weight: bold;
            font-size: 18px;
            box-shadow: 0 10px 20px rgba(0, 136, 204, 0.4);
            border: 2px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .floating-btn:hover {
            box-shadow: 0 15px 25px rgba(0, 136, 204, 0.6);
            transform: translateX(-50%) scale(1.05);
        }
    </style>
    """, unsafe_allow_html=True)

# --- ФУНКЦІЇ ---
def load_data():
    if not os.path.exists(DB_FILE):
        return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return []

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

zones = load_data()

# --- САЙДБАР (ВХІД) ---
with st.sidebar:
    st.title("🔐 Вхід для адміна")
    password = st.text_input("Введи пароль", type="password")
    st.caption("Щоб малювати зони, введи пароль.")

# ==========================================
# 🌍 РЕЖИМ 1: ПУБЛІЧНА КАРТА
# ==========================================
if password != ADMIN_PASSWORD:
    
    # Карта
    m = folium.Map(location=POLTAVA_COORDS, zoom_start=15, tiles='CartoDB positron', control_scale=False, zoom_control=False)
    
    danger_group = folium.FeatureGroup(name="⛔ Заборона")
    safe_group = folium.FeatureGroup(name="✅ Парковка")

    for spot in zones:
        if spot["type"] == "danger":
            target_group = danger_group
            col, fill, icon = "#D32F2F", "#EF5350", "⛔"
        else:
            target_group = safe_group
            col, fill, icon = "#388E3C", "#66BB6A", "✅"
            
        spot_id = spot.get('id', '???')
        link = f"https://t.me/{TG_BOT_USERNAME}?text=Помилка%20ID:{spot_id}"
        
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 14px; min-width: 160px;">
            <b>{icon} {spot['name']}</b><br>
            <span style="color:#555;">{spot.get('info', '')}</span><br>
            <hr style="margin:5px 0; border:0; border-top:1px solid #eee;">
            <a href="{link}" target="_blank" style="color:#d9534f; text-decoration:none;">⚠️ Повідомити про помилку</a>
        </div>
        """

        if spot.get("shape") == "polygon":
            folium.Polygon(
                locations=spot["points"], color=col, fill=True, fill_color=fill, fill_opacity=0.4,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(target_group)
        else:
            folium.Circle(
                location=spot["coords"], radius=spot.get("radius", 20),
                color=col, fill=True, fill_color=fill, fill_opacity=0.4,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(target_group)

    danger_group.add_to(m)
    safe_group.add_to(m)
    LocateControl(auto_start=True).add_to(m)

    st_folium(m, width="100%", height=800, returned_objects=[])

    # КНОПКА
    st.markdown(f"""
        <a href="https://t.me/{TG_BOT_USERNAME}" target="_blank" class="floating-btn">
            <span>📢</span> Додати зону
        </a>
    """, unsafe_allow_html=True)

# ==========================================
# ⚙️ РЕЖИМ 2: АДМІНКА
# ==========================================
else:
    st.success("🔓 Привіт, Адмін!")
    
    tab1, tab2 = st.tabs(["🖌️ МАЛЮВАТИ", "🗑️ ВИДАЛЯТИ"])
    
    with tab1:
        st.info("Малюй на карті -> тисни 'Зберегти'")
        from folium.plugins import Draw
        m_draw = folium.Map(location=POLTAVA_COORDS, zoom_start=16)
        Draw(draw_options={'polyline':False, 'marker':False, 'polygon':True, 'circle':True, 'rectangle':True}).add_to(m_draw)
        output = st_folium(m_draw, width=800, height=500)
        
        if output.get("last_active_drawing"):
            drawing = output["last_active_drawing"]
            with st.form("save"):
                name = st.text_input("Назва зони")
                z_type = st.selectbox("Тип", ["danger", "safe"])
                info = st.text_input("Опис")
                if st.form_submit_button("💾 Зберегти"):
                    new_id = int(time.time())
                    geom = drawing['geometry']
                    new_entry = {"id": new_id, "name": name, "type": z_type, "info": info}
                    if geom['type'] == 'Polygon':
                        new_entry["shape"] = "polygon"
                        new_entry["points"] = [[p[1], p[0]] for p in geom['coordinates'][0]]
                    else:
                        new_entry["shape"] = "circle"
                        new_entry["coords"] = [geom['coordinates'][1], geom['coordinates'][0]]
                        new_entry["radius"] = 20
                    zones.append(new_entry)
                    save_data(zones)
                    st.toast("Збережено!", icon="✅")
                    time.sleep(1)
                    st.rerun()

    with tab2:
        for i, z in enumerate(zones):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{z['name']}**")
            with col2:
                if st.button("🗑️", key=f"del_{i}"):
                    zones.pop(i)
                    save_data(zones)
                    st.rerun()
