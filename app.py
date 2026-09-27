import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time

# Константи
R_TRUE = 8.314  # Дж/(моль*К)
M_AIR = 29.0e-3  # Молярна маса повітря, кг/моль

st.set_page_config(page_title="Лабораторна робота: Визначення R", layout="wide")

st.title("🔬 Віртуальна лабораторна робота")
st.header("Визначення універсальної газової сталої методом екстраполяції")

# Ініціалізація змінних сесії (Session State)
if "stage" not in st.session_state:
    st.session_state.stage = "init"  # Можливі стани: init, pumping, ready_to_fill, finished
if "vlab_data" not in st.session_state:
    st.session_state.vlab_data = []
if "vacuum_curr" not in st.session_state:
    st.session_state.vacuum_curr = 0.0  # Поточний вакуум у %
if "m_curr" not in st.session_state:
    st.session_state.m_curr = None
if "random_seed" not in st.session_state:
    st.session_state.random_seed = int(time.time() * 1000) % 100000

# Встановлюємо прихований сид для унікальності досвіду
np.random.seed(st.session_state.random_seed)

st.subheader("🖥️ Інтерактивний лабораторний стенд")

col1, col2 = st.columns(2)

with col1:
    st.write("### ⚙️ Геометричні та зовнішні параметри")
    V_liters = st.slider("Об'єм балона (V), л", 5.0, 20.0, 10.0, step=0.5)
    T_celsius = st.slider("Температура повітря (t), °C", 18.0, 28.0, 22.0, step=0.5)
    
    V_m3 = V_liters / 1000.0
    T_kelvin = T_celsius + 273.15
    
    # Справжні приховані параметри стенду (залежать від прихованого сиду)
    m_glass_true = 450.0 + np.random.uniform(10.0, 80.0)  # Маса скла
    P_atm_true = 101325 + np.random.normal(0, 150)  # Атмосферний тиск
    max_vacuum_possible = 90.0  # Межа відкачування
    
    # Ініціалізація початкового атмосферного стану системи
    if st.session_state.m_curr is None:
        st.session_state.vacuum_curr = 0.0
        m_air_start = (P_atm_true * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
        st.session_state.m_curr = m_glass_true + m_air_start * 1000.0
        st.session_state.vlab_data = []
        st.session_state.stage = "init"

    if st.button("🔄 Скинути стенд до початкового стану"):
        st.session_state.vacuum_curr = 0.0
        m_air_start = (P_atm_true * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
        st.session_state.m_curr = m_glass_true + m_air_start * 1000.0
        st.session_state.vlab_data = []
        st.session_state.stage = "init"
        st.session_state.random_seed = int(time.time() * 1000) % 100000
        st.rerun()

    st.write("---")
    st.write("### 🕹️ Керування установкою")
    
    # --- КРОК 1 ---
    st.write("**Крок 1: Попереднє відкачування повітря з колби**")
    btn_pump = st.button("🚀 УВІМКНУТИ ВАКУУМНИЙ НАСОС", disabled=(st.session_state.stage != "init"))
    
    if btn_pump:
        st.session_state.stage = "pumping"
        steps = 50 
        progress_bar = st.progress(0)
        metric_placeholder = st.empty()
        
        for i in range(1, steps + 1):
            time.sleep(0.10)
            factor = i / float(steps)
            st.session_state.vacuum_curr = max_vacuum_possible * (1 - np.exp(-3 * factor)) / (1 - np.exp(-3))
            p_dynamic = P_atm_true * (1 - st.session_state.vacuum_curr / 100.0)
            m_air_dynamic = (p_dynamic * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
            st.session_state.m_curr = m_glass_true + m_air_dynamic * 1000.0 + np.random.normal(0, 0.002)
            progress_bar.progress(int(factor * 100))
            with metric_placeholder:
                st.caption(f"💨 Робота насоса... Вакуум: {st.session_state.vacuum_curr:.1f}%, Маса: {st.session_state.m_curr:.3f} г")
        
        metric_placeholder.empty()
        st.session_state.stage = "ready_to_fill"
        st.session_state.vlab_data.append({
            "№ досліду": 1,
            "Вакуум V (%)": round(st.session_state.vacuum_curr, 1),
            "Маса балона m (г)": round(st.session_state.m_curr, 3)
        })
        st.rerun()

    # --- КРОК 2 ---
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
            st.toast("Система повернулася до атмосферного тиску! Напуск завершено.", icon="🎉")
            
        p_dynamic = P_atm_true * (1 - next_vacuum / 100.0)
        next_m_air = (p_dynamic * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
        next_m = m_glass_true + next_m_air * 1000.0 + np.random.normal(0, 0.002)
        
        st.session_state.vacuum_curr = next_vacuum
        st.session_state.m_curr = next_m
        
        next_num = len(st.session_state.vlab_data) + 1
        st.session_state.vlab_data.append({
            "№ досліду": next_num,
            "Вакуум V (%)": round(next_vacuum, 1),
            "Маса балона m (г)": round(next_m, 3)
        })
        st.rerun()

with col2:
    st.write("### 📺 Показання приладів у лабораторії")
    
    m_col, v_col = st.columns(2)
    with m_col:
        st.metric(label="⚖️ Електронні ваги (m)", value=f"{st.session_state.m_curr:.3f} г")
    with v_col:
        st.metric(label="📉 Вакуумметр (V_%)", value=f"{st.session_state.vacuum_curr:.1f} %")
        
    st.info(f"🏛️ **Барометр на стіні ($P_{{атм}}$):** {P_atm_true:.0f} Па")
    st.caption(f"🌡️ **Кімнатний термометр (T):** {T_kelvin:.2f} К ({T_celsius} °C)")
    
    st.write("### 📝 Лабораторний журнал студента")
    if len(st.session_state.vlab_data) == 0:
        st.info("Журнал порожній. Увімкніть насос на 5 секунд, щоб почати вимірювання.")
    else:
        df_display = pd.DataFrame(st.session_state.vlab_data)
        st.dataframe(df_display, use_container_width=True)

    if len(st.session_state.vlab_data) > 1:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        vv = [row["Вакуум V (%)"] for row in st.session_state.vlab_data]
        mm = [row["Маса балона m (г)"] for row in st.session_state.vlab_data]
        
        ax.scatter(vv, mm, color='darkblue', s=40, label="Точки з журналу")
        ax.set_xlabel("Вакуум V (%)")
        ax.set_ylabel("Маса m (г)")
        ax.invert_xaxis()  
        ax.grid(True, alpha=0.3)
        st.pyplot(fig)
