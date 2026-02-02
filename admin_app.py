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
ADMIN_PASSWORD = "123" # 🔴 ЗМІНИ ПАРОЛЬ НА СВІЙ!

st.set_page_config(layout="wide", initial_sidebar_state="collapsed", page_title="Parking Poltava")

# --- CSS: ФІНАЛЬНИЙ СТИЛЬ ---
st.markdown("""
    <style>
        /* 1. Хедер робимо прозорим і неклікабельним, щоб не заважав */
        [data-testid="stHeader"] {
            background-color: transparent !important;
            height: 0px;
        }
        /* Ховаємо меню налаштувань (три крапки) та футер */
        [data-testid="stToolbar"] {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 2. Прибираємо білі відступи по краях екрану */
        .block-container { padding: 0 !important; max-width: 100% !important; }
        
        /* 3. 🔥 КНОПКА ВХОДУ (КЛЮЧИК) 🔥 */
        /* Ми знаходимо першу кнопку на сторінці (це буде наш ключ) і фіксуємо її */
        div.stButton > button:first-child {
            position: fixed !important;
            /* ВІДСТУП 260px - це нижче зуму (на ПК) і нижче браузера (на телефоні) */
            top: 260px !important; 
            left: 10px !important;
            z-index: 99999 !important;
            
            /* Стиль під кнопки Google Maps / Leaflet */
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
        
        /* Ефекти натискання для ключика */
        div.stButton > button:first-child:active {
            background-color: #ddd !important;
            transform: scale(0.95);
        }
        div.stButton > button:first-child:hover {
            border-color: rgba(0,0,0,0.2) !important;
            color: #333 !important;
        }

        /* 4. Кнопка "Додати зону" (Синя знизу) */
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

# --- ФУНКЦІЇ РОБОТИ З ДАНИМИ ---
def load_data():
    if not os.path.exists(DB_FILE): return []
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return []

def save_data(data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

zones = load_data()

# Ініціалізація сесії адміна
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# --- МОДАЛЬНЕ ВІКНО ВХОДУ ---
@st.dialog("🔐 Вхід для Адміна")
def login_dialog():
    st.write("Введи пароль адміністратора:")
    pwd = st.text_input("Пароль", type="password")
    if st.button("Увійти в систему"):
        if pwd == ADMIN_PASSWORD:
            st.session_state.is_admin = True
            st.rerun()
        else:
            st.error("Невірний пароль!")

# ==========================================
# 🌍 ЛОГІКА ДОДАТКУ
# ==========================================

# СЦЕНАРІЙ 1: ЗВИЧАЙНИЙ КОРИСТУВАЧ (ПУБЛІЧНИЙ)
if not st.session_state.is_admin:
    
    # 1. Кнопка Ключа (через CSS вона полетить на top: 260px)
    # Натискання викликає діалогове вікно
    if st.button("🔑"):
        login_dialog()

    # 2. Карта
    m = folium.Map(location=POLTAVA_COORDS, zoom_start=15, tiles='CartoDB positron', control_scale=False, zoom_control=True)
    
    # CSS хак всередину карти: опускаємо кнопки зуму і локації на 60px вниз, 
    # щоб вони не ховалися під "чубчиком" телефону
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
        
        popup_html = f"""
        <div style="font-family: sans-serif; font-size: 14px;">
            <b>{icon} {spot['name']}</b><br>
            <span style="color:#555;">{spot.get('info', '')}</span><br>
            <hr style="margin:5px 0; border:0; border-top:1px solid #eee;">
            <a href="{link}" target="_blank" style="color:#d9534f; text-decoration:none;">⚠️ Повідомити про помилку</a>
        </div>
        """
        
        if spot.get("shape") == "polygon":
            folium.Polygon(locations=spot["points"], color=col, fill=True, fill_color=fill, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=200)).add_to(grp)
        else:
            folium.Circle(location=spot["coords"], radius=spot.get("radius", 20), color=col, fill=True, fill_color=fill, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=200)).add_to(grp)

    danger_group.add_to(m)
    safe_group.add_to(m)
    LocateControl(auto_start=True).add_to(m)

    st_folium(m, width="100%", height=850, returned_objects=[])

    # Кнопка "Додати зону" через HTML (висить внизу)
    st.markdown(f"""
        <a href="https://t.me/{TG_BOT_USERNAME}" target="_blank" class="floating-btn">
            <span>📢</span> Додати зону
        </a>
    """, unsafe_allow_html=True)

# СЦЕНАРІЙ 2: АДМІНІСТРАТОР (ПОВНИЙ ДОСТУП)
else:
    # Кнопка виходу (звичайна, Streamlit сама розмістить її зверху)
    if st.button("🚪 Вийти з адмінки"):
        st.session_state.is_admin = False
        st.rerun()
        
    st.success("🔓 Режим Адміністратора активовано")
    
    # Вкладки: Малювання і Редагування
    tab1, tab2 = st.tabs(["🖌️ МАЛЮВАТИ НОВУ", "✏️ СПИСОК І РЕДАГУВАННЯ"])
    
    # --- ВКЛАДКА 1: ДОДАВАННЯ ---
    with tab1:
        st.info("Інструкція: Намалюй зону на карті -> Заповни поля нижче -> Натисни 'Зберегти'")
        from folium.plugins import Draw
        m_draw = folium.Map(location=POLTAVA_COORDS, zoom_start=16)
        Draw(draw_options={'polyline':False, 'marker':False, 'polygon':True, 'circle':True, 'rectangle':True}).add_to(m_draw)
        output = st_folium(m_draw, width=800, height=500)
        
        if output.get("last_active_drawing"):
            drawing = output["last_active_drawing"]
            st.write("---")
            with st.form("save_new_zone"):
                st.subheader("Збереження нової зони")
                name = st.text_input("Назва зони")
                z_type = st.selectbox("Тип", ["danger", "safe"], format_func=lambda x: "⛔ Заборона" if x == "danger" else "✅ Парковка")
                info = st.text_input("Опис")
                
                if st.form_submit_button("💾 Зберегти в базу"):
                    new_id = int(time.time())
                    geom = drawing['geometry']
                    new_entry = {"id": new_id, "name": name, "type": z_type, "info": info}
                    
                    if geom['type'] == 'Polygon':
                        new_entry["shape"] = "polygon"
                        # Folium хоче (lat, lon), а GeoJSON дає (lon, lat) - міняємо місцями
                        new_entry["points"] = [[p[1], p[0]] for p in geom['coordinates'][0]]
                    else:
                        new_entry["shape"] = "circle"
                        new_entry["coords"] = [geom['coordinates'][1], geom['coordinates'][0]]
                        new_entry["radius"] = 20 # Дефолтний радіус, якщо не передався
                    
                    zones.append(new_entry)
                    save_data(zones)
                    st.toast("Зону успішно додано!", icon="✅")
                    time.sleep(1)
                    st.rerun()

    # --- ВКЛАДКА 2: РЕДАГУВАННЯ ---
    with tab2:
        st.subheader("🔍 Пошук і керування")
        search_query = st.text_input("Пошук (назва або ID)", placeholder="Наприклад: ЦУМ")
        
        # Фільтрація списку
        if search_query:
            filtered_zones = [z for z in zones if search_query.lower() in z['name'].lower() or str(search_query) in str(z.get('id', ''))]
        else:
            filtered_zones = zones

        st.caption(f"Знайдено зон: {len(filtered_zones)}")

        # Виводимо кожну зону як окремий блок (expander)
        for i, zone in enumerate(filtered_zones):
            # Знаходимо реальний індекс у повному списку, щоб випадково не видалити сусідню зону
            real_index = zones.index(zone)
            
            icon = "⛔" if zone["type"] == "danger" else "✅"
            
            with st.expander(f"{icon} {zone['name']} (ID: {zone.get('id', '')})"):
                with st.form(key=f"edit_form_{zone.get('id')}_{i}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        new_name = st.text_input("Назва", value=zone['name'])
                        type_idx = 0 if zone['type'] == "danger" else 1
                        new_type = st.selectbox("Тип", ["danger", "safe"], index=type_idx)
                    
                    with col2:
                        new_info = st.text_input("Опис", value=zone.get('info', ''))
                        # Дозволяємо редагувати радіус тільки для кіл
                        if zone.get('shape') != 'polygon':
                            new_radius = st.number_input("Радіус (метри)", value=int(zone.get('radius', 20)))
                        else:
                            new_radius = 0 # Для полігонів не використовується

                    # Кнопки дій
                    col_save, col_del = st.columns([1, 1])
                    if col_save.form_submit_button("💾 Зберегти зміни"):
                        zones[real_index]['name'] = new_name
                        zones[real_index]['type'] = new_type
                        zones[real_index]['info'] = new_info
                        if zone.get('shape') != 'polygon':
                            zones[real_index]['radius'] = new_radius
                        save_data(zones)
                        st.toast("Зміни збережено!")
                        time.sleep(0.5)
                        st.rerun()
                
                # Кнопка видалення винесена за межі форми (щоб уникнути вкладених форм)
                if st.button("🗑️ Видалити цю зону назавжди", key=f"del_btn_{zone.get('id')}"):
                    zones.pop(real_index)
                    save_data(zones)
                    st.error("Зону видалено!")
                    time.sleep(1)
                    st.rerun()
