import streamlit as st
from streamlit_folium import st_folium
import folium
from folium.plugins import LocateControl, Draw, Geocoder
import json
import os
import time

# --- НАЛАШТУВАННЯ ---
DB_FILE = "zones.json"
POLTAVA_COORDS = [49.5894, 34.5510]
TG_BOT_USERNAME = "PoltavaParking_AndreBot" 
OUTPUT_MAP_FILE = "poltava_map_feedback.html"

st.set_page_config(page_title="Парковка Адмін", layout="wide")

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

def generate_public_map(zones_data):
    m = folium.Map(location=POLTAVA_COORDS, zoom_start=16, tiles=None)
    
    # 1. Шари
    folium.TileLayer(tiles='https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', attr='CartoDB', name='🗺️ Чиста карта', control=True, show=True).add_to(m)
    folium.TileLayer("OpenStreetMap", name="🚦 Детальна", control=True, show=False).add_to(m)

    # 2. Кнопка "Додати зону"
    button_html = f"""
    <div style="position: fixed; bottom: 50px; right: 10px; width: 150px; height: 40px; z-index:9999; font-size:14px;">
        <a href="https://t.me/{TG_BOT_USERNAME}" target="_blank" style="background-color: #0088cc; color: white; padding: 10px 15px; text-decoration: none; border-radius: 50px; font-weight: bold; box-shadow: 2px 2px 5px rgba(0,0,0,0.3); display: block; text-align: center;">📢 Додати зону</a>
    </div>
    """
    m.get_root().html.add_child(folium.Element(button_html))

    danger_group = folium.FeatureGroup(name="⛔ Заборонені зони")
    safe_group = folium.FeatureGroup(name="✅ Безпечні парковки")

    # 3. Малюємо зони
    for spot in zones_data:
        if spot["type"] == "danger":
            target_group = danger_group
            col, fill, icon = "#D32F2F", "#EF5350", "⛔"
        elif spot["type"] == "safe":
            target_group = safe_group
            col, fill, icon = "#388E3C", "#66BB6A", "🅿️"
        else:
            target_group = safe_group
            col, fill, icon = "blue", "blue", "ℹ️"

        spot_id = spot.get('id', 'unknown')
        msg_text = f"Привіт! Є помилка в зоні ID:{spot_id} ({spot['name']})."
        report_link = f"https://t.me/{TG_BOT_USERNAME}?text={msg_text.replace(' ', '%20')}"

        popup_html = f"""
        <div style="font-family: Arial; width: 200px;">
            <b style="font-size: 14px;">{icon} {spot['name']}</b><br>
            <hr style="margin: 5px 0;">
            {spot.get('info', '')}<br><br>
            <a href="{report_link}" target="_blank" style="color: #d9534f; font-weight: bold;">⚠️ Поскаржитися</a>
        </div>
        """

        if spot.get("shape") == "polygon":
            folium.Polygon(locations=spot["points"], color=col, weight=3, fill=True, fill_color=fill, fill_opacity=0.5, popup=folium.Popup(popup_html, max_width=250), tooltip=spot["name"]).add_to(target_group)
        else:
            folium.Circle(location=spot["coords"], radius=spot.get("radius", 20), color=col, weight=3, fill=True, fill_color=fill, fill_opacity=0.5, popup=folium.Popup(popup_html, max_width=250), tooltip=spot["name"]).add_to(target_group)

    danger_group.add_to(m)
    safe_group.add_to(m)

    # --- ОНОВЛЕНИЙ ПОШУК (ТІЛЬКИ ПОЛТАВА) ---
    Geocoder(
        collapsed=False,
        position='topleft',
        placeholder='🔍 Вулиця в Полтаві...',
        add_marker=True,
        provider='nominatim', # Використовуємо OpenStreetMap пошук
        provider_options={
            # Координати "квадрата" навколо Полтави (lon_min, lat_min, lon_max, lat_max)
            'viewbox': '34.40,49.50,34.70,49.70', 
            'bounded': 1,       # 1 означає "шукати суворо всередині квадрата"
            'countrycodes': 'ua' # Шукати тільки в Україні
        }
    ).add_to(m)

    LocateControl(auto_start=False, strings={"title": "Де я?"}).add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    m.save(OUTPUT_MAP_FILE)
    return OUTPUT_MAP_FILE

# ==========================================
# ГОЛОВНИЙ ІНТЕРФЕЙС
# ==========================================
zones = load_data()

with st.sidebar:
    st.title("⚙️ Панель керування")
    st.write(f"В базі: **{len(zones)}** зон")
    st.divider()
    st.write("👇 Натисни, щоб оновити файл карти:")
    if st.button("🔄 ОНОВИТИ ПУБЛІЧНУ КАРТУ", type="primary"):
        with st.spinner("Генерую карту..."):
            file_path = generate_public_map(zones)
            time.sleep(1)
        st.success("Готово! Пошук обмежено Полтавою.")

st.title("🚗 Центр керування парковками")
tab1, tab2 = st.tabs(["🗺️ ДОДАТИ НОВУ", "✏️ РЕДАГУВАННЯ І ПОШУК"])

# ВКЛАДКА 1: МАЛЮВАННЯ
with tab1:
    col_map, col_form = st.columns([3, 1])
    with col_map:
        m = folium.Map(location=POLTAVA_COORDS, zoom_start=16, tiles='CartoDB positron')
        for zone in zones:
            color = "#D32F2F" if zone["type"] == "danger" else "#388E3C"
            popup_txt = f"{zone['name']}\nID: {zone.get('id')}"
            if zone.get("shape") == "polygon":
                folium.Polygon(locations=zone["points"], color=color, fill=True, fill_opacity=0.3, popup=popup_txt).add_to(m)
            elif zone.get("shape") == "circle":
                folium.Circle(location=zone["coords"], radius=zone.get("radius", 20), color=color, fill=True, fill_opacity=0.3, popup=popup_txt).add_to(m)
        draw = Draw(export=False, draw_options={'polyline':False, 'circlemarker':False, 'marker':False, 'polygon':True, 'circle':True, 'rectangle':True})
        draw.add_to(m)
        st.write("🖌️ **Намалюй зону на карті:**")
        output = st_folium(m, width=800, height=500)

    with col_form:
        st.subheader("📝 Створення")
        if output.get("last_active_drawing"):
            drawing = output["last_active_drawing"]
            geom_type = drawing['geometry']['type']
            with st.form("new_zone_form"):
                name = st.text_input("Назва")
                zone_type = st.selectbox("Тип", ["danger", "safe"], format_func=lambda x: "⛔ Заборона" if x == "danger" else "✅ Парковка")
                info = st.text_input("Опис")
                radius = st.number_input("Радіус", value=20) if geom_type == "Point" else 0
                if st.form_submit_button("💾 ЗБЕРЕГТИ"):
                    if name:
                        new_id = int(time.time())
                        new_entry = {"id": new_id, "name": name, "type": zone_type, "info": info}
                        coords_raw = drawing['geometry']['coordinates']
                        if geom_type == "Polygon":
                            new_entry["shape"] = "polygon"
                            new_entry["points"] = [[p[1], p[0]] for p in coords_raw[0]]
                        else:
                            new_entry["shape"] = "circle"
                            new_entry["coords"] = [coords_raw[1], coords_raw[0]]
                            new_entry["radius"] = radius
                        zones.append(new_entry)
                        save_data(zones)
                        st.success(f"Додано! ID: {new_id}")
                        time.sleep(1)
                        st.rerun()

# ВКЛАДКА 2: РЕДАГУВАННЯ
with tab2:
    st.header("🔍 Пошук і Редагування")
    search_query = st.text_input("🔍 Введи ID або Назву:", placeholder="Наприклад: ЦУМ")
    if search_query:
        search_str = str(search_query).lower()
        filtered_zones = [z for z in zones if search_str in z['name'].lower() or search_str in str(z.get('id', ''))]
        st.info(f"Знайдено: {len(filtered_zones)}")
    else:
        filtered_zones = zones

    for i, zone in enumerate(filtered_zones):
        icon = "⛔" if zone["type"] == "danger" else "✅"
        z_id = zone.get('id', '???')
        with st.expander(f"{icon} {zone['name']}  [ID: {z_id}]"):
            with st.form(key=f"edit_form_{z_id}"):
                col_edit_1, col_edit_2 = st.columns(2)
                with col_edit_1:
                    new_name = st.text_input("Назва", value=zone['name'])
                    type_index = 0 if zone['type'] == 'danger' else 1
                    new_type = st.selectbox("Тип", ["danger", "safe"], index=type_index, format_func=lambda x: "⛔ Заборона" if x == "danger" else "✅ Парковка")
                with col_edit_2:
                    new_info = st.text_input("Опис", value=zone.get('info', ''))
                    new_radius = zone.get('radius', 20)
                    if zone.get('shape') == 'circle':
                        new_radius = st.number_input("Радіус (метри)", value=zone.get('radius', 20))
                if st.form_submit_button("💾 ЗБЕРЕГТИ ЗМІНИ"):
                    for idx, z in enumerate(zones):
                        if z.get('id') == z_id:
                            zones[idx]['name'] = new_name
                            zones[idx]['type'] = new_type
                            zones[idx]['info'] = new_info
                            if z.get('shape') == 'circle':
                                zones[idx]['radius'] = new_radius
                            break
                    save_data(zones)
                    st.success("Дані оновлено!")
                    time.sleep(0.5)
                    st.rerun()
            if st.button("🗑️ Видалити цю зону", key=f"del_{z_id}"):
                zones = [z for z in zones if z.get('id') != z_id]
                save_data(zones)
                st.error("Зону видалено!")
                time.sleep(0.5)
                st.rerun()