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

# --- CSS: ЖОРСТКА ФІКСАЦІЯ КНОПКИ ---
st.markdown("""
    <style>
        /* 1. Хедер прозорий */
        [data-testid="stHeader"] {
            background-color: transparent !important;
            height: 0px;
        }
        [data-testid="stToolbar"] {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 2. Прибираємо відступи */
        .block-container { padding: 0 !important; max-width: 100% !important; }
        
        /* 3. 🔥 СТИЛІЗАЦІЯ НАШОЇ КНОПКИ ВХОДУ (КЛЮЧИК) 🔥 */
        /* Ми знаходимо кнопку за її унікальним класом (створимо нижче) */
        div.stButton > button:first-child {
            position: fixed !important;
            top: 180px !important; /* Висота під зумом */
            left: 10px !important;
            z-index: 99999 !important;
            
            /* Робимо її схожою на кнопки карти */
            background-color: white !important;
            color: #333 !important;
            border: 2px solid rgba(0,0,0,0.2) !important;
            border-radius: 4px !important;
            width: 34px !important;
            height: 34px !important;
            padding: 0 !important;
            box-shadow: 0 1px 5px rgba(0,0,0,0.4) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            font-size: 18px !important;
        }
        
        /* Ефект натискання */
        div.stButton > button:first-child:active {
            background-color: #ddd !important;
            transform: scale(0.95);
        }
        
        /* Прибираємо стандартні ефекти наведення Streamlit */
        div.stButton > button:first-child:hover {
            border-color: rgba(0,0,0,0.2) !important;
            color: #333 !important;
        }

        /* 4. Кнопка "Додати зону" (HTML) */
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
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

zones = load_data()

# Ініціалізація стану адміна
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# --- МОДАЛЬНЕ ВІКНО ВХОДУ (НОВА ФІШКА) ---
@st.dialog("🔐 Вхід для Адміна")
def login_dialog():
    st.write("Введи секретний код:")
    pwd = st.text_input("Пароль", type="password")
    if st.button("Увійти"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.error("Невірний пароль!")

# ==========================================
# 🌍 ГОЛОВНА ЛОГІКА
# ==========================================

# Якщо ми НЕ адмін
if not st.session_state.is_admin:
    
    # 1. Створюємо справжню кнопку Streamlit
    # Вона автоматично полетить на coordinates top:180px завдяки CSS вище
    if st.button("🔑"):
        login_dialog()

    # 2. Карта
    m = folium.Map(location=POLTAVA_COORDS, zoom_start=15, tiles='CartoDB positron', control_scale=False, zoom_control=True)
    
    # CSS хак для кнопок Leaflet (Зум і Локація)
    css_fix = """
    <style>
    .leaflet-top.leaflet-left { top: 60px !important; }
    </style>
    """
    m.get_root().html.add_child(folium.Element(css_fix))
    
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
        popup_html = f"""<div style="font-family: sans-serif; font-size: 14px;"><b>{icon} {spot['name']}</b><br><span style="color:#555;">{spot.get('info', '')}</span><br><a href="{link}" target="_blank" style="color:#d9534f;">⚠️ Помилка</a></div>"""
        
        if spot.get("shape") == "polygon":
            folium.Polygon(locations=spot["points"], color=col, fill=True, fill_color=fill, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=200)).add_to(grp)
        else:
            folium.Circle(location=spot["coords"], radius=spot.get("radius", 20), color=col, fill=True, fill_color=fill, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=200)).add_to(grp)

    danger_group.add_to(m)
    safe_group.add_to(m)
    LocateControl(auto_start=True).add_to(m)

    st_folium(m, width="100%", height=850, returned_objects=[])

    # Кнопка "Додати зону" (HTML)
    st.markdown(f"""
        <a href="https://t.me/{TG_BOT_USERNAME}" target="_blank" class="floating-btn">
            <span>📢</span> Додати зону
        </a>
    """, unsafe_allow_html=True)

# ==========================================
# ⚙️ АДМІН ПАНЕЛЬ
# ==========================================
else:
    # Кнопка виходу
    if st.button("🚪 Вийти з адмінки"):
        st.session_state.is_admin = False
        st.rerun()
        
    st.success("🔓 Режим Адміністратора")
    
    tab1, tab2 = st.tabs(["🖌️ МАЛЮВАТИ", "✏️ РЕДАГУВАННЯ"])
    
    with tab1:
        st.info("Малюй -> Зберегти")
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
        st.subheader("Список зон")
        for i, z in enumerate(zones):
            with st.expander(f"{z['name']} (ID: {z.get('id')})"):
                if st.button("🗑️ Видалити", key=f"del_{i}"):
                    zones.pop(i)
                    save_data(zones)
                    st.rerun()
