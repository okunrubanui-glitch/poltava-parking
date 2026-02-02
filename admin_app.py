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

# --- CSS: СТИЛІ ІНТЕРФЕЙСУ ---
st.markdown("""
    <style>
        /* 1. Хедер прозорий */
        [data-testid="stHeader"] {
            background-color: transparent !important;
            height: 0px;
        }
        [data-testid="stToolbar"] {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* 2. 🔥 КНОПКА АДМІНА (КЛЮЧ) 🔥 */
        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            background-color: white !important;
            color: #333 !important;
            border: 2px solid rgba(0,0,0,0.2) !important;
            border-radius: 4px !important;
            box-shadow: 0 1px 5px rgba(0,0,0,0.4) !important;
            width: 34px !important;
            height: 34px !important;
            
            /* 📍 ПОЗИЦІЯ: Опускаємо ще нижче (під зум і локацію) */
            /* Зум і локація займуть десь 150px зверху після зсуву */
            /* Тому ставимо адміна на 200px */
            top: 220px !important; 
            left: 10px !important;
            z-index: 99999 !important;
        }
        
        /* Іконка ключа */
        [data-testid="stSidebarCollapsedControl"]::after {
            content: "🔑";
            font-size: 18px;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -55%);
        }
        [data-testid="stSidebarCollapsedControl"] svg { display: none !important; }
        
        /* 3. Прибираємо відступи */
        .block-container { padding: 0 !important; max-width: 100% !important; }
        
        /* 4. Кнопка "Додати зону" знизу */
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

# --- САЙДБАР ---
with st.sidebar:
    st.title("🔐 Вхід для адміна")
    password = st.text_input("Введи пароль", type="password")

# ==========================================
# 🌍 РЕЖИМ 1: ПУБЛІЧНА КАРТА
# ==========================================
if password != ADMIN_PASSWORD:
    
    m = folium.Map(location=POLTAVA_COORDS, zoom_start=15, tiles='CartoDB positron', control_scale=False, zoom_control=True)
    
    # 🔥 ХАК: Опускаємо кнопки ЗУМУ та ГЕОЛОКАЦІЇ вниз на 100px
    # Це CSS, який вставляється прямо всередину карти
    css_fix = """
    <style>
    .leaflet-top.leaflet-left {
        top: 100px !important;
    }
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
            <a href="{link}" target="_blank" style="color:#d9534f;">⚠️ Помилка</a>
        </div>
        """
        
        if spot.get("shape") == "polygon":
            folium.Polygon(locations=spot["points"], color=col, fill=True, fill_color=fill, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=200)).add_to(grp)
        else:
            folium.Circle(location=spot["coords"], radius=spot.get("radius", 20), color=col, fill=True, fill_color=fill, fill_opacity=0.4, popup=folium.Popup(popup_html, max_width=200)).add_to(grp)

    danger_group.add_to(m)
    safe_group.add_to(m)
    
    # Геолокація (теж опуститься завдяки css_fix)
    LocateControl(auto_start=True).add_to(m)

    st_folium(m, width="100%", height=850, returned_objects=[])

    st.markdown(f"""
        <a href="https://t.me/{TG_BOT_USERNAME}" target="_blank" class="floating-btn">
            <span>📢</span> Додати зону
        </a>
    """, unsafe_allow_html=True)

# ==========================================
# ⚙️ АДМІНКА
# ==========================================
else:
    st.markdown("<div style='padding-top: 50px;'></div>", unsafe_allow_html=True)
    st.success("🔓 Режим Адміністратора")
    
    tab1, tab2 = st.tabs(["🖌️ МАЛЮВАТИ", "✏️ РЕДАГУВАННЯ"])
    
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
        st.subheader("🔍 Пошук і Редагування")
        search_query = st.text_input("Введи назву або ID:", placeholder="Наприклад: ЦУМ")
        
        if search_query:
            filtered_zones = [z for z in zones if search_query.lower() in z['name'].lower() or str(search_query) in str(z.get('id', ''))]
        else:
            filtered_zones = zones
        
        st.write(f"Знайдено: {len(filtered_zones)}")
        
        for i, zone in enumerate(filtered_zones):
            real_index = zones.index(zone)
            icon = "⛔" if zone["type"] == "danger" else "✅"
            with st.expander(f"{icon} {zone['name']} (ID: {zone.get('id', '')})"):
                with st.form(key=f"edit_{zone.get('id')}_{i}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        new_name = st.text_input("Назва", value=zone['name'])
                        type_idx = 0 if zone['type'] == "danger" else 1
                        new_type = st.selectbox("Тип", ["danger", "safe"], index=type_idx)
                    with col2:
                        new_info = st.text_input("Опис", value=zone.get('info', ''))
                        new_radius = zone.get('radius', 20)
                        if zone.get('shape') != 'polygon':
                            new_radius = st.number_input("Радіус", value=int(zone.get('radius', 20)))

                    if st.form_submit_button("💾 ЗБЕРЕГТИ ЗМІНИ"):
                        zones[real_index]['name'] = new_name
                        zones[real_index]['type'] = new_type
                        zones[real_index]['info'] = new_info
                        if zone.get('shape') != 'polygon': zones[real_index]['radius'] = new_radius
                        save_data(zones)
                        st.rerun()
                if st.button("🗑️ Видалити", key=f"del_btn_{zone.get('id')}"):
                    zones.pop(real_index)
                    save_data(zones)
                    st.rerun()
