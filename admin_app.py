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
ADMIN_PASSWORD = "123" # 🔴 Твій пароль

st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="Parking Poltava")

# --- CSS: ВИПРАВЛЯЄМО ІНТЕРФЕЙС ---
st.markdown("""
    <style>
        /* 1. Робимо верхню панель ПРОЗОРОЮ, але ВИДИМОЮ */
        /* Це поверне стандартну стрілочку >, яка точно працює */
        [data-testid="stHeader"] {
            background-color: rgba(0,0,0,0); /* Прозорий фон */
            color: black;
        }
        
        /* 2. Ховаємо "Три крапки" справа зверху (вони людям не треба) */
        [data-testid="stToolbar"] {
            visibility: hidden;
        }

        /* 3. Ховаємо футер */
        footer {visibility: hidden;}
        
        /* 4. Прибираємо відступи контенту */
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            max-width: 100% !important;
        }
        
        /* 5. Стиль нижньої кнопки "Додати зону" */
        .floating-btn {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 999;
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
            display: flex; align-items: center; gap: 10px;
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

# ==========================================
# 🌍 ГОЛОВНИЙ ЕКРАН
# ==========================================

# Перевірка пароля
if password != ADMIN_PASSWORD:
    
    # Карта
    m = folium.Map(location=POLTAVA_COORDS, zoom_start=15, tiles='CartoDB positron', control_scale=False, zoom_control=False)
    
    danger_group = folium.FeatureGroup(name="⛔ Заборона")
    safe_group = folium.FeatureGroup(name="✅ Парковка")

    for spot in zones:
        if spot["type"] == "danger":
            col, fill, icon = "#D32F2F", "#EF5350", "⛔"
            grp = danger_group
        else:
            col, fill, icon = "#388E3C", "#66BB6A", "✅"
            grp = safe_group
            
        spot_id = spot.get('id', '???')
        link = f"https://t.me/{TG_BOT_USERNAME}?text=Помилка%20ID:{spot_id}"
        
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 14px;">
            <b>{icon} {spot['name']}</b><br>
            <span style="color:#555;">{spot.get('info', '')}</span><br>
            <a href="{link}" target="_blank" style="color:#d9534f;">⚠️ Помилка</a>
        </div>
        """
        
        if spot.get("shape") == "polygon":
            folium.Polygon(locations=spot["points"], color=col, fill=True, fill_color=fill, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=200)).add_to(grp)
        else:
            folium.Circle(location=spot["coords"], radius=spot.get("radius", 20), color=col, fill=True, fill_color=fill, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=200)).add_to(grp)

    danger_group.add_to(m)
    safe_group.add_to(m)
    LocateControl(auto_start=True).add_to(m)

    # Карта на весь екран
    st_folium(m, width="100%", height=850, returned_objects=[])

    # Кнопка "Додати" (Тільки вона, без зайвих написів)
    st.markdown(f"""
        <a href="https://t.me/{TG_BOT_USERNAME}" target="_blank" class="floating-btn">
            <span>📢</span> Додати зону
        </a>
    """, unsafe_allow_html=True)


# ==========================================
# ⚙️ АДМІНКА
# ==========================================
else:
    st.success("🔓 Режим Адміністратора")
    
    tab1, tab2 = st.tabs(["🖌️ МАЛЮВАТИ", "🗑️ ВИДАЛЯТИ"])
    
    with tab1:
        st.info("Малюй на карті -> тисни 'Зберегти'")
        from folium.plugins import Draw
        m_draw = fol
