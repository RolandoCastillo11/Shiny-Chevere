# 🍺 Dashboard Ejecutivo: Estudio de Mercado — CHÉVERE Cerveza y Música

Aplicación interactiva desarrollada en **Shiny for Python** para la materia de **Programación para Ciencia de Datos (Unidad 3)** del **Instituto Tecnológico de Ciudad Madero (TecNM)**.

Presenta los resultados del estudio de mercado realizado del **01 al 31 de mayo de 2020** (273 encuestados y seguimiento de canje de cupones en mayo–junio 2020) para apoyar la toma de decisiones de los inversionistas de **Chévere Cerveza y Música**.

---

## 🚀 Cómo Ejecutar Localmente

Desde la terminal en esta carpeta (`Dashboard_Chevere_Shiny`):

```bash
shiny run --reload --port 8003 app.py
```

O ejecutando directamente con Python:

```bash
python app.py
```

Abre tu navegador en:
👉 **`http://127.0.0.1:8003`**

---

## 📊 Preguntas Clave Respondidas a los Inversionistas

1. **¿Cuáles son las preferencias de las mujeres y qué prefieren los hombres?**
   - **Mujeres (152 encuestadas — 55.7%)**: Prefieren en primer lugar la **Música (39.5%, 60)** y en segundo lugar el **Lugar/Ambiente (36.2%, 55)**, seguidos del **Precio (22.4%, 34)** y en último lugar el **Menú (2.0%, 3)**.
   - **Hombres (121 encuestados — 44.3%)**: Prefieren en primer lugar el **Lugar/Ambiente (32.2%, 39)** y en segundo lugar la **Música (27.3%, 33)**, seguidos del **Precio (23.1%, 28)** y muestran una preferencia mucho mayor por el **Menú (17.4%, 21)**.

2. **¿Quién gasta más: los hombres o las mujeres?**
   - **Los Hombres gastan significativamente más** tanto en el consumo real al canjear el cupón como en el presupuesto máximo declarado:
     - **Gasto Real en Canjes (`Total Gastado`)**: Los hombres canjearon **83 de 121 cupones (68.6%)**, generando **\$38,120 MXN (83.5% del ingreso total)** con un **ticket promedio de \$459.28 MXN** (mediana \$460). Las mujeres canjearon **30 de 152 cupones (19.7%)**, generando **\$7,510 MXN (16.5% del ingreso)** con un **ticket promedio de \$250.33 MXN** (mediana \$115).
     - **Presupuesto Máximo Dispuesto a Gastar (`Máximo Gastar`)**: Los hombres reportan un promedio de **\$474.05 MXN** (máximo \$3,500) frente a **\$354.57 MXN** de las mujeres (máximo \$3,000).

3. **Posicionamiento frente a la Competencia (`Bar Favorito`)**:
   - A nivel general, **Chévere** ocupa el **3er lugar del mercado (16.5%, 45 clientes)**, muy cerca de **47 pub (17.2%, 47)** e **Irish (19.4%, 53)**.
   - En el segmento femenino, **Chévere es el 2° bar favorito (28 mujeres)**, solo detrás de *47 pub* (33).

