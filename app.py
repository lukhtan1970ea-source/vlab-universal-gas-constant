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
st.header("Определение універсальної газової сталої методом відкачування")

# Ініціалізація стану стенду (Session State), щоб реалізувати динаміку приладів
if "pump_started" not in st.session_state:
    st.session_state.pump_started = False
if "current_pressure" not in st.session_state:
    st.session_state.current_pressure = 101325.0
if "current_mass" not in st.session_state:
    st.session_state.current_mass = 512.20
if "p1" not in st.session_state:
    st.session_state.p1 = None
if "m1" not in st.session_state:
    st.session_state.m1 = None

tab1, tab2, tab3 = st.tabs(["📚 Теорія та метод", "🛠️ Експериментальний стенд", "📊 Перевірка розрахунків"])

with tab1:
    st.subheader("Метод дослідження")
    st.markdown("""
    Метод ґрунтується на вимірюванні маси повітря, видаленого з посудини відомого об'єму, та викликаної цим зміни тиску.
    
    Якщо з балона об'ємом $V$ відкачати частину повітря, то зв'язок між зміною тиску $\\Delta P$ та зміною маси $\\Delta m$ за сталої температури $T$ описується рівнянням Менделєєва-Клапейрона:
    $$\\Delta P \\cdot V = \\frac{\\Delta m}{M} \\cdot R \\cdot T$$
    
    Звідси розрахункова формула для універсальної газової сталої:
    $$R = \\frac{\\Delta P \\cdot V \\cdot M}{\\Delta m \\cdot T}$$
    """)

with tab2:
    st.subheader("🖥️ Панель керування та віртуальні прилади")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### ⚙️ Параметри установки")
        seed = st.number_input("Номер вашого варіанта (ID):", min_value=1, max_value=100, value=1)
        np.random.seed(seed)
        
        # Конструкційні параметри
        V_liters = st.slider("Об'єм балона (V), л", 5.0, 20.0, 10.0, step=0.5)
        T_celsius = st.slider("Температура в лабораторії (t), °C", 18.0, 28.0, 22.0, step=0.5)
        
        V_m3 = V_liters / 1000.0
        T_kelvin = T_celsius + 273.15
        
        # Генеруємо початкові стабільні значення для конкретного варіанта
        P_start = 101325 + np.random.normal(0, 150)
        m_start = (P_start * V_m3 * M_AIR) / (R_TRUE * T_kelvin) + 500.0 # 500г - вага балона
        
        st.write("---")
        st.write("### 🕹️ Керування експериментом")
        
        # Крок 1: Зафіксувати початковий стан
        if st.button("📌 Зафіксувати початковий стан (P1, m1)"):
            st.session_state.p1 = P_start
            st.session_state.m1 = m_start + np.random.normal(0, 0.01) # похибка вагів
            st.session_state.current_pressure = P_start
            st.session_state.current_mass = st.session_state.m1
            st.success("Дані P1 та m1 успішно зафіксовані в журналі!")

        # Крок 2: Ввімкнення насоса
        pump_depth = st.slider("Встановити потужність відкачування (%)", 20, 70, 45)
        
        if st.button("🚀 УВІМКНУТИ ВАКУУМНИЙ НАСОС"):
            if st.session_state.p1 is None:
                st.error("Спочатку зафіксуйте початковий стан (натисніть кнопку вище)!")
            else:
                st.session_state.pump_started = True
                
                # Симуляція динамічного процесу відкачування (анімація приладів)
                P_target = st.session_state.p1 * (1 - pump_depth / 100.0)
                m_target = (P_target * V_m3 * M_AIR) / (R_TRUE * T_kelvin) + 500.0
                
                # Створюємо ефект "роботи" насоса (кілька кроків оновлення екрану)
                progress_bar = st.progress(0)
                for i in range(1, 11):
                    time.sleep(0.2)  # Пауза для ілюзії реального часу
                    factor = i / 10.0
                    st.session_state.current_pressure = st.session_state.p1 - (st.session_state.p1 - P_target) * factor + np.random.normal(0, 50)
                    st.session_state.current_mass = st.session_state.m1 - (st.session_state.m1 - m_target) * factor + np.random.normal(0, 0.005)
                    progress_bar.progress(i * 10)
                
                st.success("Відкачування завершено! Клапан перекритий. Система стабільна.")

    with col2:
        st.write("### 📺 Візуалізація віртуальних приладів")
        
        # Візуальні блоки під прилади (використовуємо st.metric як цифрові табло)
        metric_col1, metric_col2 = st.columns(2)
        
        with metric_col1:
            st.markdown("#### 📟 ЦИФРОВИЙ МАНОМЕТР")
            st.metric(
                label="Поточний тиск у балоні (P)", 
                value=f"{st.session_state.current_pressure:.0f} Па",
                delta=f"{(st.session_state.current_pressure - 101325):.0f} Па від атмосфери"
            )
            
        with metric_col2:
            st.markdown("#### ⚖️ ЕЛЕКТРОННІ ВАГИ")
            st.metric(
                label="Загальна маса балона (m)", 
                value=f"{st.session_state.current_mass:.2f} г"
            )
            
        st.info(f"🌡️ **Термометр навколишнього середовища:** {T_kelvin:.2f} К ({T_celsius}°C)")
        
        # Лабораторний журнал студента
        st.write("---")
        st.write("### 📝 Ваш лабораторний журнал")
        
        p1_val = f"{st.session_state.p1:.0f} Па" if st.session_state.p1 else "Не зафіксовано"
        m1_val = f"{st.session_state.m1:.2f} г" if st.session_state.m1 else "Не зафіксовано"
        
        p2_val = f"{st.session_state.current_pressure:.0f} Па" if st.session_state.pump_started else "Очікування відкачування"
        m2_val = f"{st.session_state.current_mass:.2f} г" if st.session_state.pump_started else "Очікування відкачування"
        
        journal_data = {
            "Параметр": ["Температура (T)", "Початковий тиск (P1)", "Кінцевий тиск (P2)", "Початкова маса (m1)", "Кінцева маса (m2)"],
            "Значення": [f"{T_kelvin:.2f} К", p1_val, p2_val, m1_val, m2_val]
        }
        st.table(pd.DataFrame(journal_data))

with tab3:
    st.subheader("📊 Модуль автоматичної перевірки звіту")
    st.write("Обчисліть різниці тисків і мас за формулою та введіть отримане значення експериментальної газової сталої.")
    
    student_R = st.number_input("Введіть ваше розраховане значення R (Дж/(моль·К)):", min_value=0.0, max_value=20.0, value=8.0, step=0.001)
    
    if st.button("Надіслати на перевірку"):
        if st.session_state.p1 is None or not st.session_state.pump_started:
            st.error("Ви не провели експеримент у вкладці 'Експериментальний стенд'!")
        else:
            delta_P = st.session_state.p1 - st.session_state.current_pressure
            delta_m = (st.session_state.m1 - st.session_state.current_mass) / 1000.0 # в кг
            
            # Істинне розрахункове значення для конкретного зашумленого досвіду студента
            R_calc = (delta_P * V_m3 * M_AIR) / (delta_m * T_kelvin)
            rel_error = abs(student_R - R_calc) / R_calc * 100
            
            if rel_error < 1.5:
                st.balloons()
                st.success(f"🎉 Чудово! Розрахунок абсолютно точний. Відхилення від експерименту: {rel_error:.2f}%.")
            elif rel_error < 5.0:
                st.warning(f"Звіт прийнято, але є невелика арифметична похибка: {rel_error:.2f}%. Можливо, ви занадто сильно округлили значення Δm чи ΔP.")
            else:
                st.error(f"❌ Помилка занадто велика (відхилення {rel_error:.2f}%). Перевірте формулу: тиск має бути в Па, об'єм у м³, маса в кг!")
