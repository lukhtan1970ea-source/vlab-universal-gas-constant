import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Константи
R_TRUE = 8.314  # Дж/(моль*К)
M_AIR = 29.0e-3  # Молярна маса повітря, кг/моль

st.set_page_config(page_title="Лабораторна робота: Визначення R", layout="wide")

st.title("🔬 Віртуальна лабораторна робота")
st.header("Визначення універсальної газової сталої методом відкачування")

tab1, tab2, tab3 = st.tabs(["📚 Теорія та метод", "🛠️ Експеримент", "📊 Перевірка розрахунків"])

with tab1:
    st.subheader("Метод дослідження")
    st.markdown("""
    Метод ґрунтується на вимірюванні маси повітря, видаленого з посудини відомого об'єму, та викликаної цим зміни тиску.
    
    Якщо з балона об'ємом $V$ відкачати частину повітря, то зв'язок між зміною тиску $\Delta P$ та зміною маси $\Delta m$ за сталої температури $T$ описується рівнянням Менделєєва-Клапейрона:
    $$\Delta P \cdot V = \frac{\Delta m}{M} \cdot R \cdot T$$
    
    Звідси розрахункова формула для універсальної газової сталої:
    $$R = \frac{\Delta P \cdot V \cdot M}{\Delta m \cdot T}$$
    
    **Порядок виконання на симуляторі:**
    1. Встановіть параметри експерименту та номер вашого варіанта.
    2. Зафіксуйте початковий тиск і масу балона.
    3. Проведіть відкачування повітря за допомогою насоса.
    4. Запишіть кінцеві показання тиску, маси та температури.
    """)

with tab2:
    st.subheader("Віртуальний стенд відкачування газу")
    
    col1, col2 = st.columns(2)  # Теперь всё будет работать правильно

    
    with col1:
        st.write("### Налаштування установки")
        seed = st.number_input("Номер вашого варіанта (ID):", min_value=1, max_value=100, value=1)
        np.random.seed(seed)
        
        # Параметри установки
        V_liters = st.slider("Об'єм балона (л)", 5.0, 20.0, 10.0, step=0.5)
        T_celsius = st.slider("Температура в лабораторії (°C)", 18.0, 28.0, 22.0, step=0.5)
        
        # Симуляція процесу відкачування
        st.write("---")
        st.write("### Керування насосом")
        pump_power = st.slider("Глибина відкачування (інтенсивність насоса)", 10, 80, 40, step=5)
        
    with col2:
        st.write("### Показання приладів та графіки")
        
        # Переведення в СІ
        V_m3 = V_liters / 1000.0
        T_kelvin = T_celsius + 273.15
        
        # Початковий стан (атмосферний тиск із легким шумом від варіанта)
        P_start = 101325 + np.random.normal(0, 100) 
        m_start = (P_start * V_m3 * M_AIR) / (R_TRUE * T_kelvin) + 500.0 # 500г - умовна вага порожнього балона
        
        # Кінцевий стан після відкачування
        P_end = P_start * (1 - pump_power / 100.0)
        # Додаємо випадкову похибку манометра (0.5%) та вагів (0.01 г)
        P_end_measured = P_end + np.random.normal(0, 0.005 * P_end)
        
        m_end_ideal = (P_end * V_m3 * M_AIR) / (R_TRUE * T_kelvin) + 500.0
        m_end_measured = m_end_ideal + np.random.normal(0, 0.01)
        
        # Виведення даних у таблицю для студента
        data = {
            "Параметр": ["Температура (T)", "Початковий тиск (P1)", "Кінцевий тиск (P2)", "Початкова маса (m1)", "Кінцева маса (m2)"],
            "Значення": [f"{T_kelvin:.2f} К", f"{P_start:.0f} Па", f"{P_end_measured:.0f} Па", f"{m_start:.2f} г", f"{m_end_measured:.2f} г"]
        }
        df = pd.DataFrame(data)
        st.table(df)
        
        # Графік падіння тиску
        time_steps = np.linspace(0, 10, 100)
        p_dynamic = P_start - (P_start - P_end_measured) * (1 - np.exp(-time_steps/3)) / (1 - np.exp(-10/3))
        
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(time_steps, p_dynamic / 1000, color='#1f77b4', lw=2)
        ax.set_title("Динаміка тиску в балоні під час відкачування")
        ax.set_xlabel("Час роботи насоса (с)")
        ax.set_ylabel("Тиск (кПа)")
        ax.grid(True, linestyle='--', alpha=0.6)
        
        st.pyplot(fig)

with tab3:
    st.subheader("Перевірка результатів")
    st.write("Використовуючи дані з таблиці, розрахуйте $\Delta P$, $\Delta m$ та знайдіть універсальну газову сталу $R$.")
    
    student_R = st.number_input("Введіть ваше розраховане значення R (Дж/(моль·К)):", min_value=0.0, max_value=20.0, value=8.0, step=0.001)
    
    if st.button("Перевірити"):
        delta_P = P_start - P_end_measured
        delta_m = (m_start - m_end_measured) / 1000.0 # в кг
        
        R_calc = (delta_P * V_m3 * M_AIR) / (delta_m * T_kelvin)
        rel_error = abs(student_R - R_calc) / R_calc * 100
        
        if rel_error < 1.5:
            st.balloons()
            st.success(f"🎉 Відмінно! Ваше значення збіглося з розрахунковим. Похибка: {rel_error:.2f}%.")
        elif rel_error < 5.0:
            st.warning(f"Прийнято, але точність могла бути вищою. Відхилення: {rel_error:.2f}%. Можливо, ви округлили проміжні значення.")
        else:
            st.error(f"Помилка занадто велика (відхилення {rel_error:.2f}%). Перевірте: чи перевели ви масу в кг, об'єм у $м^3$, а також чи правильно знайшли різницю величин.")

