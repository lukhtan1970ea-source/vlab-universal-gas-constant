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
if "p_curr" not in st.session_state:
    st.session_state.p_curr = None
if "m_curr" not in st.session_state:
    st.session_state.m_curr = None

tab1, tab2, tab3 = st.tabs(["📚 Методика експерименту", "🛠️ Експериментальний стенд", "📊 Перевірка результатів"])

with tab1:
    st.subheader("Метод екстраполяції для визначення маси повітря")
    st.markdown("""
    Визначити точну масу повітря в балоні прямим зважуванням неможливо, оскільки ваги завжди показують сумарну масу балона та повітря в ньому:
    $$m_{виміряна} = m_{скла} + m_{повітря}$$
    
    Для вирішення цієї проблеми мы використовуємо **метод екстраполяції**:
    1. З балона максимально відкачують повітря за допомогою вакуумного насоса (створюють глибоке розрідження).
    2. Після досягнення мінімального тиску насос вимикають, а у балон **порціями впускають повітря**, щоразу вимірюючи тиск $P$ та загальну масу $m$.
    3. Оскільки маса повітря лінійно залежить від тиску ($m_{повітря} = \\frac{M \\cdot V}{R \\cdot T} \\cdot P$), загальна маса балона описується рівнянням прямої лінії:
    $$m(P) = m_{скла} + \\left(\\frac{M \\cdot V}{R \\cdot T}\\right) \\cdot P$$
    4. Побудувавши графік залежності $m$ від $P$ і продовживши (екстраполювавши) пряму до точки **$P = 0$**, ми знаходимо точку перетину з віссю мас. Це значення і є **масою порожнього балона без повітря ($m_{скла}$)**.
    5. Знаючи $m_{скла}$, можна легко знайти масу повітря при атмосферному тиску: $\\Delta m = m_{атм} - m_{скла}$, і розрахувати універсальну газову сталу:
    $$R = \\frac{P_{атм} \\cdot V \\cdot M}{\\Delta m \\cdot T}$$
    """)

with tab2:
    st.subheader("🖥️ Інтерактивний лабораторний стенд")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### ⚙️ Початкові налаштування")
        seed = st.number_input("Номер вашого варіанта (ID):", min_value=1, max_value=100, value=1)
        np.random.seed(seed)
        
        V_liters = st.slider("Об'єм балона (V), л", 5.0, 20.0, 10.0, step=0.5)
        T_celsius = st.slider("Температура повітря (t), °C", 18.0, 28.0, 22.0, step=0.5)
        
        V_m3 = V_liters / 1000.0
        T_kelvin = T_celsius + 273.15
        
        # Справжні "приховані" параметри для цього варіанта
        m_glass_true = 450.0 + np.random.uniform(10.0, 80.0) # Маса скла
        P_atm_true = 101325 + np.random.normal(0, 150) # Атмосферний тиск
        P_min_vacuum = 2000.0 + np.random.uniform(0, 1000) # Граничний вакуум насоса
        
        # Ініціалізація початкового атмосферного стану системи
        if st.session_state.p_curr is None or st.button("🔄 Скинути стенд до початкового стану"):
            st.session_state.p_curr = P_atm_true
            m_air_start = (P_atm_true * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
            st.session_state.m_curr = m_glass_true + m_air_start * 1000.0
            st.session_state.vlab_data = []
            st.session_state.stage = "init"

        st.write("---")
        st.write("### 🕹️ Керування установкою")
        
        # Етап 1: Відкачування
        st.write("**Крок 1: Попереднє відкачування повітря з колби**")
        btn_pump = st.button("🚀 УВІМКНУТИ ВАКУУМНИЙ НАСОС", disabled=(st.session_state.stage != "init"))
        
        if btn_pump:
            st.session_state.stage = "pumping"
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Анімація процесу відкачування
            steps = 15
            for i in range(1, steps + 1):
                time.sleep(0.15)
                factor = i / float(steps)
                # Експоненціальне падіння тиску
                st.session_state.p_curr = P_atm_true - (P_atm_true - P_min_vacuum) * (1 - np.exp(-3 * factor)) / (1 - np.exp(-3))
                m_air_dynamic = (st.session_state.p_curr * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
                st.session_state.m_curr = m_glass_true + m_air_dynamic * 1000.0 + np.random.normal(0, 0.002)
                
                progress_bar.progress(int(factor * 100))
                status_text.text(f"Відкачування... Поточний тиск: {st.session_state.p_curr:.0f} Па")
            
            st.session_state.stage = "ready_to_fill"
            # Автоматично заносимо першу точку (максимальний вакуум)
            st.session_state.vlab_data.append({
                "№ досліду": 1,
                "Тиск P (Па)": round(st.session_state.p_curr),
                "Маса балона m (г)": round(st.session_state.m_curr, 3)
            })
            st.rerun()
        # Етап 2: Напуск порціями
        st.write("**Крок 2: Дослідження (Напуск повітря порціями)**")
        st.caption("Впускайте повітря невеликими порціями, щоразу фіксуючи масу та тиск, аж поки система не повернеться до атмосферного тиску.")
        
        is_fill_disabled = (st.session_state.stage != "ready_to_fill" and st.session_state.stage != "finished")
        btn_fill = st.button("📥 Впустити порцію повітря (відкрити клапан)", disabled=is_fill_disabled)
        
        if btn_fill:
            p_step = np.random.uniform(12000, 16000)
            next_P = st.session_state.p_curr + p_step
            
            if next_P >= P_atm_true:
                next_P = P_atm_true
                st.session_state.stage = "finished"
                st.toast("Тиск зрівнявся з атмосферним! Експеримент завершено.", icon="🎉")
                
            next_m_air = (next_P * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
            next_m = m_glass_true + next_m_air * 1000.0 + np.random.normal(0, 0.002)
            
            st.session_state.p_curr = next_P
            st.session_state.m_curr = next_m
            
            next_num = len(st.session_state.vlab_data) + 1
            st.session_state.vlab_data.append({
                "№ досліду": next_num,
                "Тиск P (Па)": round(next_P),
                "Маса балона m (г)": round(next_m, 3)
            })

    with col2:
        st.write("### 📺 Показання цифрових приладів")
        
        m_col, p_col = st.columns(2)
        with m_col:
            st.metric(label="⚖️ Електронні ваги (m)", value=f"{st.session_state.m_curr:.3f} г")
        with p_col:
            st.metric(label="📟 Цифровий манометр (P)", value=f"{st.session_state.p_curr:.0f} Па")
            
        st.caption(f"🌡️ **Термометр у лабораторії (T):** {T_kelvin:.2f} К")
        
        st.write("### 📝 Лабораторний журнал студента")
        if len(st.session_state.vlab_data) == 0:
            st.info("Журнал порожній. Увімкніть насос, щоб почати вимірювання.")
        else:
            df_display = pd.DataFrame(st.session_state.vlab_data)
            st.dataframe(df_display, use_container_width=True)

        # Графік точок вимірювання
        if len(st.session_state.vlab_data) > 1:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            pp = [row["Тиск P (Па)"] for row in st.session_state.vlab_data]
            mm = [row["Маса балона m (г)"] for row in st.session_state.vlab_data]
            ax.scatter(pp, mm, color='darkblue', s=40, label="Точки з журналу")
            ax.set_xlabel("Тиск P (Па)")
            ax.set_ylabel("Маса m (г)")
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

with tab3:
    st.subheader("📊 Перевірка результатів обробки даних")
    st.write("Виконайте графічну екстраполяцію отриманої прямої до значення $P = 0$ та розрахуйте константи.")
    
    col_inp1, col_inp2 = st.columns(2)
    with col_inp1:
        student_m_glass = st.number_input("1. Знайдена маса порожньої колби m_скла (г):", min_value=0.0, max_value=1000.0, value=500.0, step=0.001)
    with col_inp2:
        student_R = st.number_input("2. Розраховане значення R (Дж/(моль·К)):", min_value=0.0, max_value=20.0, value=8.0, step=0.001)
        
    if st.button("Надіслати звіт на перевірку"):
        if len(st.session_state.vlab_data) < 5:
            st.error("❌ Недостатньо вимірювань для точної екстраполяції. Проведіть дослід до кінця (6-8 точок)!")
        else:
            # МНК розрахунок для перевірки
            pp_arr = np.array([row["Тиск P (Па)"] for row in st.session_state.vlab_data])
            mm_arr = np.array([row["Маса балона m (г)"] for row in st.session_state.vlab_data])
            
            slope, intercept = np.polyfit(pp_arr, mm_arr, 1)
            
            P_atm_measured = pp_arr[-1]
            m_atm_measured = mm_arr[-1]
            
            delta_m_calc = (m_atm_measured - intercept) / 1000.0 # в кг
            R_calc = (P_atm_measured * V_m3 * M_AIR) / (delta_m_calc * T_kelvin)
            
            error_m = abs(student_m_glass - intercept)
            error_R = abs(student_R - R_calc) / R_calc * 100
            
            st.write("### 📉 Result:")
            
            # Графік перевірки МНК з екстраполяцією
            fig_check, ax_check = plt.subplots(figsize=(8, 4))
            ax_check.scatter(pp_arr, mm_arr, color='darkblue', zorder=5, label="Ваші точки")
            
            p_line = np.linspace(0, P_atm_measured, 100)
            m_line = slope * p_line + intercept
            ax_check.plot(p_line, m_line, color='red', linestyle='--', label="Екстраполяція лінії до P=0")
            ax_check.scatter(0, intercept, color='red', s=50, zorder=6, label=f"Істинне m_скла = {intercept:.3f} г")
            
            ax_check.set_xlim(-5000, P_atm_measured * 1.05)
            ax_check.set_xlabel("Тиск P (Па)")
            ax_check.set_ylabel("Маса m (г)")
            ax_check.legend()
            ax_check.grid(True, alpha=0.4)
            st.pyplot(fig_check)
            
            # Вердикт системи
            if error_m <= 0.05 and error_R < 2.0:
                st.balloons()
                st.success(f"🎉 **Чудово!** Маса колби визначена абсолютно правильно (відхилення {error_m:.3f} г). Значення R = {student_R} Дж/(моль·К) підтверджено!")
            elif error_m > 0.05:
                st.error(f"❌ **Помилка в масі колби!** Ваше значення відрізняється від правильної екстраполяції більш ніж на 0.05 г (50 мг). Перевірте побудову графіка в Excel/Origin.")
            else:
                st.warning(f"⚠️ **Масу колби визначено правильно**, але фінальний розрахунок R має помилку {error_R:.2f}%. Перевірте формулу, переведення літрів у $м^3$ та грамів у кг.")
