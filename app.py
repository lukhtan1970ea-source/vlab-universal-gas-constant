import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
import base64

# Константи
R_TRUE = 8.314  # Дж/(моль*К)
M_AIR = 29.0e-3  # Молярна маса повітря, кг/моль

st.set_page_config(page_title="Лабораторна робота: Визначення R", layout="wide")

st.title("🔬 Віртуальна лабораторна робота")
st.header("Визначення універсальної газової сталої методом екстраполяції")

# Оптимальне зчитування аудіо з пам'яті (кешування)
@st.cache_data
def load_audio_b64(file_path):
    try:
        with open(file_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except FileNotFoundError:
        return None

pump_b64 = load_audio_b64("pump.mp3")
hiss_b64 = load_audio_b64("hiss.mp3")

# Ініціалізація змінних сесії (Session State)
if "stage" not in st.session_state:
    st.session_state.stage = "init"  # Можливі стани: init, pumping, ready_to_fill, finished
if "vlab_data" not in st.session_state:
    st.session_state.vlab_data = []
if "vacuum_curr" not in st.session_state:
    st.session_state.vacuum_curr = 0.0  # Поточний вакуум у %
if "m_curr" not in st.session_state:
    st.session_state.m_curr = None
if "m_start" not in st.session_state:
    st.session_state.m_start = None  # Еталонна початкова маса
if "random_seed" not in st.session_state:
    st.session_state.random_seed = int(time.time() * 1000) % 100000
if "audio_on" not in st.session_state:
    st.session_state.audio_on = False


# Встановлюємо прихований сид для унікальності досвіду
np.random.seed(st.session_state.random_seed)

# --- АУДІО-РУШІЙ ТА ІН'ЄКЦІЯ В КНОПКИ ---
# Перемикач аудіосупроводу в стилі Windows
icon = "🔊" if st.session_state.audio_on else "🔇"
st.session_state.audio_on = st.toggle(
    label=f"{icon} Звуковий супровід стенду", 
    value=st.session_state.audio_on
)

# Передаємо стан тумблера в JavaScript-рушій кнопок
audio_is_active = "true" if st.session_state.audio_on else "false"

audio_html = f"""
<script>
    if (!window.audioPumpObj) window.audioPumpObj = new Audio("data:audio/mp3;base64,{pump_b64 or ''}");
    if (!window.audioHissObj) window.audioHissObj = new Audio("data:audio/mp3;base64,{hiss_b64 or ''}");

    window.clickPlayPump = function() {{
        // Звук грає тільки якщо тумблер увімкнено (active)
        if ({audio_is_active} && window.audioPumpObj) {{
            window.audioPumpObj.currentTime = 0;
            window.audioPumpObj.play().catch(e => console.log(e));
            setTimeout(function() {{
                if(window.audioPumpObj) {{ window.audioPumpObj.pause(); window.audioPumpObj.currentTime = 0; }}
            }}, 5400); // Синхронізовано під розгін 0.4с + 5с анімації
        }}
    }};

    window.clickPlayHiss = function() {{
        if ({audio_is_active} && window.audioHissObj) {{
            window.audioHissObj.currentTime = 0;
            window.audioHissObj.play().catch(e => console.log(e));
        }}
    }};

    function ИньекцияЗвука() {{
        const buttons = window.parent.document.querySelectorAll("button");
        buttons.forEach(btn => {{
            const txt = btn.innerText || "";
            if (txt.includes("УВІМКНУТИ ВАКУУМНИЙ НАСОС") && !btn.hasPumpSound) {{
                btn.addEventListener("click", window.clickPlayPump);
                btn.hasPumpSound = true;
            }}
            if (txt.includes("Впустити порцію повітря") && !btn.hasHissSound) {{
                btn.addEventListener("click", window.clickPlayHiss);
                btn.hasHissSound = true;
            }}
        }});
    }}
    setInterval(ИньекцияЗвука, 300);
</script>
"""
st.components.v1.html(audio_html, height=0, width=0)


st.subheader("🖥️ Інтерактивний лабораторний стенд")
col1, col2 = st.columns(2)
with col2:
    st.write("### 📺 Показання приладів у лабораторії")
    instruments_placeholder = st.empty()

with col1:
    st.write("### ⚙️ Геометричні та зовнішні параметри")
    V_liters = st.slider("Об'єм балона (V), л", 5.0, 20.0, 10.0, step=0.5)
    T_celsius = st.slider("Температура повітря (t), °C", 18.0, 28.0, 22.0, step=0.5)
    
    V_m3 = V_liters / 1000.0
    T_kelvin = T_celsius + 273.15
    
    m_glass_true = 450.0 + np.random.uniform(10.0, 80.0)  # Маса скла
    P_atm_true = 101325 + np.random.normal(0, 150)  # Атмосферний тиск
    max_vacuum_possible = 90.0  # Межа відкачування
    
    if st.session_state.m_curr is None:
        st.session_state.vacuum_curr = 0.0
        m_air_start = (P_atm_true * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
        st.session_state.m_start = m_glass_true + m_air_start * 1000.0
        st.session_state.m_curr = st.session_state.m_start
        st.session_state.vlab_data = []
        st.session_state.stage = "init"

    if st.button("🔄 Скинути стенд до початкового стану"):
        st.session_state.vacuum_curr = 0.0
        st.session_state.random_seed = int(time.time() * 1000) % 100000
        np.random.seed(st.session_state.random_seed)
        
        m_glass_true = 450.0 + np.random.uniform(10.0, 80.0)
        P_atm_true = 101325 + np.random.normal(0, 150)
        
        m_air_start = (P_atm_true * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
        st.session_state.m_start = m_glass_true + m_air_start * 1000.0
        st.session_state.m_curr = st.session_state.m_start
        st.session_state.vlab_data = []
        st.session_state.stage = "init"
        st.rerun()

    st.write("---")
    st.write("### 🕹️ Керування установкою")
    
    # --- КРОК 1: ВІДКАЧУВАННЯ ---
    st.write("**Крок 1: Попереднє відкачування повітря з колби**")
    btn_pump = st.button("🚀 УВІМКНУТИ ВАКУУМНИЙ НАСОС", disabled=(st.session_state.stage != "init"))
    
    if btn_pump:
        st.session_state.stage = "pumping"
        st.rerun()

    if st.session_state.stage == "pumping":
        steps = 54  # 4 кроки розгону + 50 кроків анімації = 5.4 секунд загального часу
        progress_bar = st.progress(0)
        
        for i in range(1, steps + 1):
            time.sleep(0.10)
            
            # Лише перші 4 кроки (0.4 секунди) насос гуде, стрілки на місці
            if i <= 4:
                factor = 0.0
                progress_bar.progress(0)
            else:
                # Наступні 50 кроків (5 секунд) плавно знижуємо тиск
                factor = (i - 4) / 50.0
                progress_bar.progress(int(factor * 100))
                
                st.session_state.vacuum_curr = max_vacuum_possible * (1 - np.exp(-3 * factor)) / (1 - np.exp(-3))
                p_dynamic = P_atm_true * (1 - st.session_state.vacuum_curr / 100.0)
                m_air_dynamic = (p_dynamic * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
                st.session_state.m_curr = m_glass_true + m_air_dynamic * 1000.0 + np.random.normal(0, 0.001)

            
            # Оновлюємо табло приладів без стрибків екрана
            with instruments_placeholder.container():
                m_col, v_col = st.columns(2)
                with m_col:
                    st.metric(label="⚖️ Електронні ваги (m)", value=f"{st.session_state.m_curr:.3f} г")
                with v_col:
                    st.metric(label="📉 Вакуумметр (V_%)", value=f"{st.session_state.vacuum_curr:.1f} %")
                st.info(f"🏛️ **Барометр на стіні ($P_{{атм}}$):** {P_atm_true:.0f} Па")
                st.caption(f"🌡️ **Кімнатний термометр (T):** {T_kelvin:.2f} К ({T_celsius} °C)")
        
        st.session_state.stage = "ready_to_fill"
        st.session_state.vlab_data.append({
            "№ досліду": 1,
            "Вакуум V (%)": round(st.session_state.vacuum_curr, 1),
            "Маса балона m (г)": round(st.session_state.m_curr, 3)
        })
        st.rerun()

    # --- КРОК 2: НАПУСК ---
    st.write(" ")
    st.write("**Крок 2: Дослідження (Напуск повітря порціями)**")
    st.caption("Впускайте повітря невеликими порціями, щоразу фіксуючи масу та вакуум, аж поки система не повернеться до атмосферного тиску (0% вакууму).")
    
    is_fill_disabled = (st.session_state.stage != "ready_to_fill" and st.session_state.stage != "finished")
    btn_fill = st.button("📥 Впустити порцію повітря (відкрити клапан)", disabled=is_fill_disabled)
    
    if btn_fill:
        vac_step = np.random.uniform(12.0, 16.0)
        next_vacuum = st.session_state.vacuum_curr - vac_step
        
        if next_vacuum <= 0.0:
            next_vacuum = 0.0
            st.session_state.stage = "finished"
            st.session_state.m_curr = st.session_state.m_start
            st.toast("Система повернулася до атмосферного тиску! Напуск завершено.", icon="🎉")
        else:
            p_dynamic = P_atm_true * (1 - next_vacuum / 100.0)
            next_m_air = (p_dynamic * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
            st.session_state.m_curr = m_glass_true + next_m_air * 1000.0 + np.random.normal(0, 0.001)
        
        st.session_state.vacuum_curr = next_vacuum
        
        next_num = len(st.session_state.vlab_data) + 1
        st.session_state.vlab_data.append({
            "№ досліду": next_num,
            "Вакуум V (%)": round(next_vacuum, 1),
            "Маса балона m (г)": round(st.session_state.m_curr, 3)
        })
        st.rerun()

# Статичне відображення приладів
if st.session_state.stage != "pumping":
    with instruments_placeholder.container():
        m_col, v_col = st.columns(2)
        with m_col:
            st.metric(label="⚖️ Електронні ваги (m)", value=f"{st.session_state.m_curr:.3f} г")
        with v_col:
            st.metric(label="📉 Вакуумметр (V_%)", value=f"{st.session_state.vacuum_curr:.1f} %")
        st.info(f"🏛️ **Барометр на стіні ($P_{{атм}}$):** {P_atm_true:.0f} Па")
        st.caption(f"🌡️ **Кімнатний термометр (T):** {T_kelvin:.2f} К ({T_celsius} °C)")

# Журнал та графік
with col2:
    st.write("### 📝 Лабораторний журнал студента")
    if len(st.session_state.vlab_data) == 0:
        st.info("Журнал порожній. Увімкніть насос на 5 секунд, щоб почати вимірювання.")
    else:
        df_display = pd.DataFrame(st.session_state.vlab_data)
        st.dataframe(df_display, use_container_width=True)

    

