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
ADMIN_PASSWORD = "123" # Зміни на свій пароль!

st.set_page_config(page_title="Парковка Полтава", page_icon="🚗", layout="wide", initial_sidebar_state="collapsed")

# --- CSS ХАКИ ДЛЯ "ЧИСТОГО" ЕКРАНУ ---
st.markdown("""
    <style>
        /* 1. Прибираємо верхній відступ і "гамбургер" меню */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            max-width: 100% !important;
        }
        /* 2. Ховаємо хедер (смужка зверху) */
        header {visibility: hidden;}
        /* 3. Ховаємо футер (напис внизу) */
        footer {visibility: hidden;}
        /* 4. Прибираємо відступи навколо карти */
        iframe {
            width: 100% !important;
        }
        /* 5. Стиль для кнопки "Надіслати зону" */
        .floating-btn {
            position: fixed;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 999;
            background-color: #0088cc;
            color: white;
            padding: 12px 24px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            font-family: sans-serif;
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

# --- САЙДБАР (СХОВАНИЙ ЗА ЗАМОВЧУВАННЯМ) ---
with st.sidebar:
    st.write("🔧 **Меню Адміністратора**")
    password = st.text_input("Введи пароль", type="password")
    
# === РЕЖИМ 1: ПУБЛІЧНА КАРТА ===
if password != ADMIN_PASSWORD:
    # Створюємо карту без зайвих елементів
    m = folium.Map(location=POLTAVA_COORDS, zoom_start=15, tiles='CartoDB positron', control_scale=False)
    
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
    LocateControl(auto_start=False).add_to(m)

    # ВАЖЛИВО: height=85vh означає 85% висоти екрана
    st_folium(m, width="100%", height=700, returned_objects=[])

    # Плаваюча кнопка поверх карти (через HTML)
    st.markdown(f"""
        <a href="https://t.me/{TG_BOT_USERNAME}" target="_blank" class="floating-btn">
            📢 Додати зону
        </a>
    """, unsafe_allow_html=True)

# === РЕЖИМ 2: АДМІНКА ===
else:
    st.success("🔓 Режим Адміністратора")
    
    # (Тут твій код адмінки для редагування - залишаємо як був, він потрібен тільки тобі)
    tab1, tab2 = st.tabs(["ДОДАТИ", "СПИСОК"])
    
    with tab1:
        from folium.plugins import Draw
        m_draw = folium.Map(location=POLTAVA_COORDS, zoom_start=16)
        Draw(draw_options={'polyline':False, 'marker':False, 'polygon':True, 'circle':True, 'rectangle':True}).add_to(m_draw)
        output = st_folium(m_draw, width=800, height=500)
        
        if output.get("last_active_drawing"):
            drawing = output["last_active_drawing"]
            with st.form("save"):
                name = st.text_
