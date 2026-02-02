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
ADMIN_PASSWORD = "123" # 🔴 ЗМІНИ ПАРОЛЬ!

# Вмикаємо режим "на весь екран" і ховаємо сайдбар
st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="Parking Poltava")

# --- CSS МАГІЯ (ХОВАЄМО ВСЕ ЗАЙВЕ) ---
st.markdown("""
    <style>
        /* 1. Прибираємо верхню кольорову смужку (Header) */
        header {visibility: hidden !important;}
        .stApp > header {display: none !important;}
        
        /* 2. Прибираємо кнопку-гамбургер (Три смужки справа зверху) */
        #MainMenu {visibility: hidden !important;}
        
        /* 3. Прибираємо напис внизу "Made with Streamlit" */
        footer {visibility: hidden !important;}
        
        /* 4. Прибираємо білі відступи по краях, щоб карта була на весь екран */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 0rem !important;
            padding-right: 0rem !important;
            max-width: 100% !important;
        }
        
        /* 5. Прибираємо відступи між елементами */
        div[data-testid="stVerticalBlock"] {
            gap: 0rem !important;
        }

        /* 6. Стиль для твоєї кнопки "Додати зону" */
        .floating-btn {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            z-index: 9999;
            background-color: #0088cc;
            color: white; 
            padding: 15px 30px;
            border-radius: 50px;
            text-decoration: none;
            font-weight: bold;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif;
            font-size: 16px;
            border: 2px solid white;
        }
        .floating-btn:hover {
            background-color: #006699;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

# --- ФУНКЦІЇ ЗАВАНТАЖЕННЯ ---
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

# --- ПРИХОВАНА АДМІНКА ---
# Сайдбар тепер закритий. Щоб зайти, треба натиснути стрілочку > зліва зверху.
with st.sidebar:
    st.write("🔐 **Адмін-панель**")
    password = st.text_input("Пароль", type="password")

# ==========================================
# 🌍 РЕЖИМ 1: ПУБЛІЧНА КАРТА (ТЕ ЩО БАЧАТЬ УСІ)
# ==========================================
if password != ADMIN_PASSWORD:
    
    # Створюємо карту без зайвих кнопок зуму (вони дрібні на телефоні)
    m = folium.Map(location=POLTAVA_COORDS, zoom_start=15, tiles='CartoDB positron', control_scale=False, zoom_control=False)
    
    danger_group = folium.FeatureGroup(name="⛔ Заборона")
    safe_group = folium.FeatureGroup(name="✅ Парковка")

    for spot in zones:
        if spot["type"] == "danger":
            target_group = danger_group
            col, fill = "#D32F2F", "#EF5350"
            icon = "⛔"
        else:
            target_group = safe_group
            col, fill = "#388E3C", "#66BB6A"
            icon = "✅"
            
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
    
    # Кнопка "Де я?"
    LocateControl(auto_start=True, strings={"title": "Де я?"}).add_to(m)

    # ВАЖЛИВО: Висота 95vh (95% висоти екрану телефону)
    st_folium(m, width="100%", height=800, returned_objects=[])

    # Кнопка поверх карти (HTML)
    st.markdown(f"""
        <a href="https://t.me/{TG_BOT_USERNAME}" target="_blank" class="floating-btn">
            📢 Додати зону
        </a>
    """, unsafe_allow_html=True)

# ==========================================
# ⚙️ РЕЖИМ 2: АДМІНКА (ТІЛЬКИ З ПАРОЛЕМ)
# ==========================================
else:
    st.success("🔓 Режим Адміністратора активовано")
    
    tab1, tab2 = st.tabs(["🖌️ МАЛЮВАТИ", "🗑️ ВИДАЛЯТИ"])
    
    with tab1:
        st.write("Намалюй зону і натисни 'Зберегти' під картою")
        from folium.plugins import Draw
        m_draw = folium.Map(location=POLTAVA_COORDS, zoom_start=16)
        Draw(draw_options={'polyline':False, 'marker':False, 'polygon':True, 'circle':True, 'rectangle':True}).add_to(m_draw)
        output = st_folium(m_draw, width=800, height=500)
        
        if output.get("last_active_drawing"):
            drawing = output["last_active_drawing"]
            with st.form("save"):
                name = st.text_input("Назва зони")
                z_type = st.selectbox("Тип", ["danger", "safe"])
                info = st.text_input("Опис (напр. 'Штрафують зранку')")
                if st.form_submit_button("💾 Зберегти в базу"):
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
                    st.toast("Зону успішно додано!", icon="✅")
                    time.sleep(1)
                    st.rerun()

    with tab2:
        st.write("Список усіх зон у базі:")
        for i, z in enumerate(zones):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"**{z['name']}** ({z['type']})")
            with col2:
                if st.button("🗑️", key=f"del_{i}"):
                    zones.pop(i)
                    save_data(zones)
                    st.rerun()
