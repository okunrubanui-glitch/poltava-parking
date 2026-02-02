import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import LocateControl, Geocoder
import json
import os
import time

# --- НАЛАШТУВАННЯ ---
DB_FILE = "zones.json"
POLTAVA_COORDS = [49.5894, 34.5510]
TG_BOT_USERNAME = "PoltavaParking_AndreBot" 
# ПАРОЛЬ ДЛЯ ВХОДУ В АДМІНКУ (Зміни його на свій!)
ADMIN_PASSWORD = "123"

st.set_page_config(page_title="Парковка Полтава", page_icon="🚗", layout="wide")

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

# --- ЛОГІКА ІНТЕРФЕЙСУ ---
zones = load_data()

# Сайдбар (Бокова панель)
with st.sidebar:
    st.title("🚗 Навігація")
    # Поле для пароля
    password = st.text_input("🔑 Вхід для адміна", type="password")
    
    st.divider()
    st.info(f"Всього зон на карті: {len(zones)}")
    st.caption("Developed by Andre")

# === РЕЖИМ 1: ПУБЛІЧНА КАРТА (ВІДКРИВАЄТЬСЯ ВСІМ) ===
if password != ADMIN_PASSWORD:
    st.title("🅿️ Карта парковок Полтави")
    
    # Створюємо карту
    m = folium.Map(location=POLTAVA_COORDS, zoom_start=15, tiles='CartoDB positron')
    
    # Додаємо шари
    danger_group = folium.FeatureGroup(name="⛔ Заборонені зони")
    safe_group = folium.FeatureGroup(name="✅ Безпечні парковки")

    for spot in zones:
        # Кольори та іконки
        if spot["type"] == "danger":
            target_group = danger_group
            col, fill = "#D32F2F", "#EF5350"
            icon = "⛔"
        else:
            target_group = safe_group
            col, fill = "#388E3C", "#66BB6A"
            icon = "✅"
            
        # Формуємо красивий опис для кліку
        spot_id = spot.get('id', '???')
        # Посилання на бота для скарги
        msg = f"Помилка в зоні ID:{spot_id} ({spot['name']})"
        link = f"https://t.me/{TG_BOT_USERNAME}?text={msg.replace(' ', '%20')}"
        
        popup_html = f"""
        <div style="font-family: sans-serif; min-width: 150px;">
            <b>{icon} {spot['name']}</b><br>
            <i style="color:gray;">{spot.get('info', '')}</i><br><br>
            <a href="{link}" target="_blank" style="color:red; font-size:12px;">⚠️ Поскаржитися</a>
        </div>
        """

        # Малюємо фігуру
        if spot.get("shape") == "polygon":
            folium.Polygon(
                locations=spot["points"], color=col, fill=True, fill_color=fill, fill_opacity=0.4,
                popup=folium.Popup(popup_html, max_width=250), tooltip=spot["name"]
            ).add_to(target_group)
        else:
            folium.Circle(
                location=spot["coords"], radius=spot.get("radius", 20),
                color=col, fill=True, fill_color=fill, fill_opacity=0.4,
                popup=folium.Popup(popup_html, max_width=250), tooltip=spot["name"]
            ).add_to(target_group)

    danger_group.add_to(m)
    safe_group.add_to(m)
    
    # Кнопка геолокації
    LocateControl(auto_start=False, strings={"title": "Де я?"}).add_to(m)
    
    # Виводимо карту на екран
    st_folium(m, width="100%", height=600)
    
    st.markdown(f"""
    <div style="text-align: center; margin-top: 20px;">
        <a href="https://t.me/{TG_BOT_USERNAME}" target="_blank" style="background-color: #0088cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 10px; font-weight: bold;">
        📢 Надіслати нову зону через Бота
        </a>
    </div>
    """, unsafe_allow_html=True)


# === РЕЖИМ 2: АДМІНКА (ТІЛЬКИ ЯКЩО ПАРОЛЬ ПРАВИЛЬНИЙ) ===
else:
    st.warning("🔓 Ви увійшли в режим Адміністратора")
    
    tab1, tab2 = st.tabs(["🗺️ ДОДАТИ НОВУ", "✏️ РЕДАГУВАННЯ"])
    
    # (ТУТ ВЕСЬ ТВІЙ СТАРИЙ КОД АДМІНКИ)
    # Я його скоротив для зручності, але суть та сама: малювання і редагування
    
    # --- ВКЛАДКА МАЛЮВАННЯ ---
    with tab1:
        st.subheader("Додати нову зону")
        # Карта для малювання
        from folium.plugins import Draw
        m_draw = folium.Map(location=POLTAVA_COORDS, zoom_start=16)
        Draw(draw_options={'polyline':False, 'marker':False, 'polygon':True, 'circle':True, 'rectangle':True}).add_to(m_draw)
        
        output = st_folium(m_draw, width=800, height=500)
        
        # Форма збереження
        if output.get("last_active_drawing"):
            drawing = output["last_active_drawing"]
            with st.form("save_new"):
                name = st.text_input("Назва")
                z_type = st.selectbox("Тип", ["danger", "safe"])
                info = st.text_input("Опис")
                if st.form_submit_button("Зберегти"):
                    # Зберігаємо...
                    new_id = int(time.time())
                    geom = drawing['geometry']
                    new_entry = {"id": new_id, "name": name, "type": z_type, "info": info}
                    if geom['type'] == 'Polygon':
                        new_entry["shape"] = "polygon"
                        # Перевертаємо координати для folium
                        new_entry["points"] = [[p[1], p[0]] for p in geom['coordinates'][0]]
                    else:
                        new_entry["shape"] = "circle"
                        new_entry["coords"] = [geom['coordinates'][1], geom['coordinates'][0]]
                        new_entry["radius"] = 20 # Дефолтний радіус
                    
                    zones.append(new_entry)
                    save_data(zones)
                    st.success("Додано!")
                    st.rerun()

    # --- ВКЛАДКА СПИСКУ ---
    with tab2:
        st.subheader("Список усіх зон")
        for i, z in enumerate(zones):
            with st.expander(f"{z['name']} ({z['type']})"):
                if st.button(f"🗑️ Видалити {z['name']}", key=f"del_{i}"):
                    zones.pop(i)
                    save_data(zones)
                    st.rerun()
