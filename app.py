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
    st.session_state.vacuum_curr = 0.0 # Поточний вакуум у %
if "m_curr" not in st.session_state:
    st.session_state.m_curr = None

tab1, tab2, tab3 = st.tabs(["📚 Методика експерименту", "🛠️ Експериментальний стенд", "📊 Перевірка результатів"])

with tab1:
    st.subheader("Метод екстраполяції для визначення маси повітря")
    st.markdown("""
    Визначити точну масу повітря в балоні прямим зважуванням неможливо, оскільки ваги завжди показують сумарну масу балона та повітря в ньому:
    $$m_{виміряна} = m_{скла} + m_{повітря}$$
    
    Для вирішення цієї проблеми ми використовуємо **метод екстраполяції**:
    1. З балона максимально відкачують повітря за допомогою вакуумного насоса (створюють глибоке розрідження до 90%). Значення контролюється за **вакуумметром у відсотках**.
    2. Після досягнення мінімального тиску насос вимикають, а у балон **порціями впускають повітря**, щоразу вимірюючи вакуум та загальну масу $m$.
    3. Розрахунок тиску в колбі $P$ для кожної точки студент виконує самостійно за показаннями атмосферного тиску $P_{атм}$ та вакуумметра ($V_{\\%}$):
    $$P = P_{атм} \\cdot \\left(1 - \\frac{V_{\\%}}{100}\\right)$$
    4. Побудувавши графік залежності $m$ від $P$ і продовживши (екстраполювавши) пряму до точки **$P = 0$**, ми знаходимо **масу порожнього балона без повітря ($m_{скла}$)**.
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
        max_vacuum_possible = 90.0 # Межа відкачування за ТЗ
        
        # Ініціалізація початкового атмосферного стану системи
        if st.session_state.m_curr is None or st.button("🔄 Скинути стенд до початкового стану"):
            st.session_state.vacuum_curr = 0.0
            m_air_start = (P_atm_true * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
            st.session_state.m_curr = m_glass_true + m_air_start * 1000.0
            st.session_state.vlab_data = []
            st.session_state.stage = "init"

        st.write("---")
        st.write("### 🕹️ Керування установкою")
        
        # Етап 1: Відкачування (5 секунд з динамічним оновленням)
        st.write("**Крок 1: Попереднє відкачування повітря з колби**")
        btn_pump = st.button("🚀 УВІМКНУТИ ВАКУУМНИЙ НАСОС", disabled=(st.session_state.stage != "init"))
        
        if btn_pump:
            st.session_state.stage = "pumping"
            
            # Налаштування плавного бігу цифр: 50 кроків по 0.1 секунди = 5 секунд процесу
            steps = 50 
            progress_bar = st.progress(0)
            metric_placeholder = st.empty()
            
            for i in range(1, steps + 1):
                time.sleep(0.10)
                factor = i / float(steps)
                
                # Плавне зростання вакууму до 90%
                st.session_state.vacuum_curr = max_vacuum_possible * (1 - np.exp(-3 * factor)) / (1 - np.exp(-3))
                
                # Розрахунок поточної маси повітря в цей момент
                p_dynamic = P_atm_true * (1 - st.session_state.vacuum_curr / 100.0)
                m_air_dynamic = (p_dynamic * V_m3 * M_AIR) / (R_TRUE * T_kelvin)
                st.session_state.m_curr = m_glass_true + m_air_dynamic * 1000.0 + np.random.normal(0, 0.002)
                
                # Динамічно показуємо зміну параметрів прямо під час циклу
                progress_bar.progress(int(factor * 100))
                with metric_placeholder:
                    st.caption(f"💨 Робота насоса... Вакуум: {st.session_state.vacuum_curr:.1f}%, Маса: {st.session_state.m_curr:.3f} г")
            
            metric_placeholder.empty()
            st.session_state.stage = "ready_to_fill"
            # Фіксуємо першу точку (максимальний вакуум 90%)
            st.session_state.vlab_data.append({
                "№ досліду": 1,
                "Вакуум V (%)": round(st.session_state.vacuum_curr, 1),
                "Маса балона m (г)": round(st.session_state.m_curr, 3)
            })
            st.rerun()
        # Етап 2: Напуск порціями
        st.write("**Крок 2: Дослідження (Напуск повітря порціями)**")
        st.caption("Впускайте повітря невеликими порціями, щоразу фіксуючи масу та вакуум, аж поки система не повернеться до атмосферного тиску (0% вакууму).")
        
        is_fill_disabled = (st.session_state.stage != "ready_to_fill" and st.session_state.stage != "finished")
        btn_fill = st.button("📥 Впустити порцію повітря (відкрити клапан)", disabled=is_fill_disabled)
        
        if btn_fill:
            # Зменшуємо вакуум порціями (приблизно на 12-15%)
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

    with col2:
        st.write("### 📺 Показання приладів у лабораторії")
        
        # Віртуальні прилади
        m_col, v_col = st.columns(2)
        with m_col:
            st.metric(label="⚖️ Електронні ваги (m)", value=f"{st.session_state.m_curr:.3f} г")
        with v_col:
            st.metric(label="📉 Вакуумметр (V_%)", value=f"{st.session_state.vacuum_curr:.1f} %")
            
        # Панель метеостанції на стіні (манометр приховано, студент рахує сам!)
        st.info(f"🏛️ **Барометр на стіні ($P_{{атм}}$):** {P_atm_true:.0f} Па")
        st.caption(f"🌡️ **Кімнатний термометр (T):** {T_kelvin:.2f} К ({T_celsius} °C)")
        
        st.write("### 📝 Лабораторний журнал студента")
        if len(st.session_state.vlab_data) == 0:
            st.info("Журнал порожній. Увімкніть насос на 5 секунд, щоб почати вимірювання.")
        else:
            df_display = pd.DataFrame(st.session_state.vlab_data)
            st.dataframe(df_display, use_container_width=True)

        # Графік залежності маси від вакууму для контролю
        if len(st.session_state.vlab_data) > 1:
            fig, ax = plt.subplots(figsize=(6, 3.5))
            vv = [row["Вакуум V (%)"] if "Вакуум V (%)" in row else row.get("Вакуум V (%)", 0) for row in st.session_state.vlab_data]
            mm = [row["Маса балона m (г)"] for row in st.session_state.vlab_data]
            ax.scatter(vv, mm, color='darkblue', s=40, label="Точки з журналу")
            ax.set_xlabel("Вакуум V (%)")
            ax.set_ylabel("Маса m (г)")
            ax.invert_xaxis() # Інвертуємо, щоб графік йшов логічно від вакууму до атмосфери
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)

with tab3:
    st.subheader("📊 Перевірка результатів обробки даних")
    st.write("Переведіть відсотки вакууму в абсолютний тиск Па за формулою. Виконайте графічну екстраполяцію прямої $m(P)$ до значення $P = 0$ та розрахуйте константи.")
    
    col_inp1, col_inp2 = st.columns(2)
    with col_inp1:
        student_m_glass = st.number_input("1. Знайдена маса порожньої колби m_скла (г):", min_value=0.0, max_value=1000.0, value=500.0, step=0.001)
    with col_inp2:
        student_R = st.number_input("2. Розраховане значення R (Дж/(моль·К)):", min_value=0.0, max_value=20.0, value=8.0, step=0.001)
        
    if st.button("Надіслати звіт на перевірку"):
        if len(st.session_state.vlab_data) < 5:
            st.error("❌ Недостатньо вимірювань для точної екстраполяції. Проведіть дослід до кінця (6-8 точок)!")
        else:
            # Математичний перерахунок у тиск для перевірки МНК
            v_arr = np.array([row["Вакуум V (%)"] for row in st.session_state.vlab_data])
            mm_arr = np.array([row["Маса балона m (г)"] for row in st.session_state.vlab_data])
            pp_arr = P_atm_true * (1 - v_arr / 100.0) # Справжній тиск для перевірки
            
            slope, intercept = np.polyfit(pp_arr, mm_arr, 1)
            
            P_atm_measured = pp_arr[-1]
            m_atm_measured = mm_arr[-1]
            
            delta_m_calc = (m_atm_measured - intercept) / 1000.0 # в кг
            R_calc = (P_atm_measured * V_m3 * M_AIR) / (delta_m_calc * T_kelvin)
            
            error_m = abs(student_m_glass - intercept)
            error_R = abs(student_R - R_calc) / R_calc * 100
            
            st.write("### 📉 Еталонний графік екстраполяції для викладача:")
            
            fig_check, ax_check = plt.subplots(figsize=(8, 4))
            ax_check.scatter(pp_arr, mm_arr, color='darkblue', zorder=5, label="Точки студента")
            
            p_line = np.linspace(0, P_atm_measured, 100)
            m_line = slope * p_line + intercept
            ax_check.plot(p_line, m_line, color='red', linestyle='--', label="Лінія МНК")
            ax_check.scatter(0, intercept, color='red', s=50, zorder=6, label=f"Істинне m_скла = {intercept:.3f} г")
            
            ax_check.set_xlim(-5000, P_atm_measured * 1.05)
            ax_check.set_xlabel("Розрахований тиск P (Па)")
            ax_check.set_ylabel("Маса m (г)")
            ax_check.legend()
            ax_check.grid(True, alpha=0.4)
            st.pyplot(fig_check)
            
            if error_m <= 0.05 and error_R < 2.0:
                st.balloons()
                st.success(f"🎉 **Чудово!** Масу колби визначено вірно (відхилення {error_m:.3f} г). Значення R = {student_R} Дж/(моль·К) успішно підтверджено!")
            elif error_m > 0.05:
                st.error(f"❌ **Помилка в масі колби!** Ваше значення відрізняється від правильної екстраполяції більш ніж на 0.05 г. Перевірте правильність розрахунку тиску $P$ з відсотків вакууму та побудову тренду.")
            else:
                st.warning(f"⚠️ **Масу колби визначено правильно**, але фінальний розрахунок R має помилку {error_R:.2f}%. Перевірте формулу, переведення об'єму в $м^3$ та грамів у кг.")
