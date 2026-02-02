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

# --- CSS: БЕЗПЕЧНІ ВІДСТУПИ + КНОПКИ ---
st.markdown("""
    <style>
        /* 1. Робимо відступ зверху, щоб не лізти під "чубчик" телефону */
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            max-width: 100% !important;
        }
        
        /* 2. Ховаємо стандартний хедер Streamlit, він нам не треба */
        header {visibility: hidden !important;}
        footer {visibility: hidden !important;}

        /* 3. КНОПКА "ДОДАТИ ЗОНУ" (ЗНИЗУ) */
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

        /* 4. 🔥 НОВА КНОПКА "КЛЮЧ" (ЗЛІВА ЗВЕРХУ) 🔥 */
        /* Ми опускаємо її на 60px вниз, щоб вона не ховалася за інтерфейсом браузера */
        .admin-key-btn {
            position: fixed;
            top: 60px; 
            left: 20px;
            z-index: 9999;
            background-color: rgba(255, 255, 255, 0.9);
            color: #333 !important;
            width: 45px;
            height: 45px;
            border-radius: 50%;
            text-decoration: none !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            justify_content: center;
            font-size: 24px;
            border: 1px solid #ddd;
        }
        .admin-key-btn:hover {
            background-color: #f0f0f0;
            transform: scale(1.1);
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

# --- ЛОГІКА ВХОДУ ЧЕРЕЗ SESSION STATE ---
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Якщо натиснули "Увійти" (імітація через кнопку в інтерфейсі)
# Ми зробимо простіше: Сайдбар завжди доступний, але ми відкриваємо його кодом?
# Streamlit не дає відкривати сайдбар кнопкою. Тому ми зробимо своє "вікно" входу.

# --- САЙДБАР (ВХІД) ---
with st.sidebar:
    st.title("🔐 Вхід")
    password = st.text_input("Пароль", type="password")
    if password == ADMIN_PASSWORD:
        st.session_state.is_admin = True
    else:
        st.session_state.is_admin = False

# ==========================================
# 🌍 ГОЛОВНИЙ ЕКРАН
# ==========================================

# 1. Якщо ми НЕ адмін — показуємо карту і кнопку входу
if not st.session_state.is_admin:
    
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
        
        # Малюємо
        if spot.get("shape") == "polygon":
            folium.Polygon(locations=spot["points"], color=col, fill=True, fill_color=fill, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=200)).add_to(grp)
        else:
            folium.Circle(location=spot["coords"], radius=spot.get("radius", 20), color=col, fill=True, fill_color=fill, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=200)).add_to(grp)

    danger_group.add_to(m)
    safe_group.add_to(m)
    LocateControl(auto_start=True).add_to(m)

    st_folium(m, width="100%", height=850, returned_objects=[])

    # 👇 КНОПКА "ДОДАТИ" (Знизу)
    st.markdown(f"""
        <a href="https://t.me/{TG_BOT_USERNAME}" target="_blank" class="floating-btn">
            <span>📢</span> Додати зону
        </a>
    """, unsafe_allow_html=True)

    # 👇 КНОПКА "ВХІД" (Зверху зліва - ВІДСТУП 60px)
    # Це маленький "хак": ми робимо прозору кнопку поверх стрілочки сайдбару, щоб ти знав де вона
    # АБО ми просто пишемо текст
    st.markdown("""
        <div style="position: fixed; top: 60px; left: 15px; z-index: 9999; background: white; padding: 5px 10px; border-radius: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); font-size: 12px; font-weight: bold; pointer-events: none;">
            ⬅️ Адмін тут
        </div>
    """, unsafe_allow_html=True)
    
    # ВАЖЛИВО: Я повернув видимість хедера трішки, щоб стрілочка точно була
    st.markdown("""
        <style>
            [data-testid="stHeader"] {
                background-color: transparent !important;
                visibility: visible !important;
            }
            [data-testid="stSidebarCollapsedControl"] {
                display: block !important;
                color: black !important;
                background-color: white;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                top: 60px !important; /* Опускаємо стрілочку вниз! */
                left: 15px !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
        </style>
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
        m_draw = folium.Map(location=POLTAVA_COORDS, zoom_start=16)
        Draw(draw_options={'polyline':False, 'marker':False, 'polygon':True, 'circle':True, 'rectangle':True}).add_to(m_draw)
        output = st_folium(m_draw, width=800, height=500)
        
        if output.get("last_active_drawing"):
            drawing = output["last_active_drawing"]
            with st.form("save"):
                name = st.text_input("Назва")
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
                    st.toast("Готово!")
                    time.sleep(1)
                    st.rerun()

    with tab2:
        for i, z in enumerate(zones):
            col1, col2 = st.columns([4, 1])
            with col1: st.write(f"**{z['name']}**")
            with col2:
                if st.button("🗑️", key=f"del_{i}"):
                    zones.pop(i)
                    save_data(zones)
                    st.rerun()
