import os
from pathlib import Path
import base64
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from shiny import App, render, ui, reactive

import tempfile

# Configuración de Matplotlib para alta resolución y compatibilidad multiplataforma (Windows / Posit Linux)
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "mpl_cache"))
matplotlib.use("Agg")
plt.rcParams.update({
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "axes.edgecolor": "#cbd5e1",
    "axes.linewidth": 1.0,
})

# -----------------------------------------------------------------------------
# 0. Carga del Logo, Datos y Catálogos
# -----------------------------------------------------------------------------
DIRECTORIO_ACTUAL = Path(__file__).parent
RUTA_LOGO = DIRECTORIO_ACTUAL / "logo_chevere.png"
RUTA_CSV = DIRECTORIO_ACTUAL / "chevere_datos.csv"

LOGO_DATA_URI = (
    f"data:image/png;base64,{base64.b64encode(RUTA_LOGO.read_bytes()).decode('ascii')}"
    if RUTA_LOGO.exists()
    else ""
)

def cargar_datos_base() -> pd.DataFrame:
    """Carga y limpia el dataset con los 273 registros del estudio."""
    df = pd.read_csv(RUTA_CSV)
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip()

    df["Total Gastado"] = pd.to_numeric(df["Total Gastado"], errors="coerce")
    for col in ["Máximo Gastar", "Ingresos"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["Edad"] = pd.to_numeric(df["Edad"], errors="coerce").fillna(df["Edad"].median())
    return df

DATOS_CHEVERE = cargar_datos_base()
EDAD_MIN, EDAD_MAX = int(DATOS_CHEVERE["Edad"].min()), int(DATOS_CHEVERE["Edad"].max())

def crear_opciones(columna: str, etiqueta_todos: str, clave_todos: str = "todos", orden: list | None = None) -> dict:
    """Genera diccionarios de opciones para selectores sin repetir bucles."""
    valores = orden if orden else sorted(DATOS_CHEVERE[columna].unique())
    return {clave_todos: etiqueta_todos, **{v: v for v in valores}}

OPCIONES_GRAFICAS = {
    "pref_genero": "1. 🎯 Preferencias de Mujeres vs. Hombres (Música, Lugar, Precio, Menú)",
    "gasto_genero": "2. 💰 ¿Quién Gasta Más? Presupuesto Declarado vs. Gasto Real Promedio",
    "ingresos_reales": "3. 💵 Ingreso Real Acumulado en Canjes ($ MXN) por Género",
    "tasa_canje": "4. 🎟️ Tasa de Conversión / Canje de Cupones por Género (% Sí vs % No)",
    "bar_favorito": "5. 🍺 Preferencia de Bares Locales (Chévere vs. Competencia)",
    "frecuencia_visita": "6. 📅 Frecuencia de Asistencia a Bares (Regular, Frecuente, Raramente)",
    "ocasiones_visita": "7. 🎉 Ocasiones de Asistencia al Bar según Género (Amigos, Eventos, Cumpleaños)",
    "ticket_bar": "8. 🏷️ Ticket Promedio de Gasto Real por Bar Favorito",
    "ocupacion_clientes": "9. 👔 Composición de Clientes por Ocupación",
    "edad_presupuesto": "10. 📈 Relación entre Edad del Cliente y Presupuesto Máximo",
}

OPCIONES_BAR = crear_opciones("Bar Favorito", "Todos los Bares", "todos")
OPCIONES_OCUPACION = crear_opciones("Ocupación", "Todas las Ocupaciones", "todas")
OPCIONES_FRECUENCIA = crear_opciones("Frecuencia Visita", "Todas las Frecuencias", "todas", ["Frecuente", "Regular", "Raramente"])
OPCIONES_OCASION = crear_opciones("Ocasiones", "Todas las Ocasiones", "todas")

# Mapeo declarativo de filtros (input_id, columna_df, valor_por_defecto)
MAPA_FILTROS = [
    ("filtro_genero", "Género", "todos"),
    ("filtro_bar", "Bar Favorito", "todos"),
    ("filtro_frecuencia", "Frecuencia Visita", "todas"),
    ("filtro_ocupacion", "Ocupación", "todas"),
    ("filtro_ocasion", "Ocasiones", "todas"),
    ("filtro_canje", "Canje Cupón", "todos"),
]

# Textos de insights estáticos por gráfica
INSIGHTS_ESTATICOS = {
    "pref_genero": (
        "📌 Hallazgo Central de Preferencias:\n"
        "• Mujeres (152): Prefieren en primer lugar la Música (39.5%, 60 clientes) y en segundo el Lugar/Ambiente (36.2%, 55 clientes), sumando el 75.7%. Prácticamente no eligen por Menú (solo 2.0%).\n"
        "• Hombres (121): Priorizan el Lugar (32.2%, 39 clientes) y la Música (27.3%, 33 clientes), pero tienen un marcado interés en el Menú (17.4%, 21 clientes) — una valoración casi 9 veces mayor que las mujeres.\n"
        "• Recomendación: Para el público masculino conviene ofrecer paquetes de cerveza con snacks/alimentos, mientras que para el público femenino el enfoque debe centrarse en el ambiente y la propuesta musical."
    ),
    "gasto_genero": (
        "📌 Hallazgo Central de Gasto Promedio:\n"
        "• Gasto Real en Canjes: Los hombres gastan un promedio de $459.28 MXN por visita al canjear el cupón, frente a $250.33 MXN de las mujeres (los hombres gastan 83.5% más en caja).\n"
        "• Presupuesto Declarado: Los hombres reportan un presupuesto promedio de $474.05 MXN vs. $354.57 MXN de las mujeres.\n"
        "• Conclusión: Los hombres tienen un ticket promedio y una disposición al gasto considerablemente más alta."
    ),
    "tasa_canje": (
        "📌 Conversión del Cupón de Regalo:\n"
        "• Hombres: Tasa de canje extraordinariamente alta del 68.6% (83 de 121 hombres redimieron su cupón).\n"
        "• Mujeres: Tasa de canje baja del 19.7% (solo 30 de 152 mujeres redimieron su cupón).\n"
        "• Oportunidad: Existe un gran potencial de crecimiento al diseñar dinámicas de cupones grupales o para cumpleaños enfocadas en el público femenino."
    ),
    "bar_favorito": (
        "📌 Posicionamiento de CHÉVERE frente a Competidores:\n"
        "• Chévere ocupa la 3ª posición global con 45 clientes (16.5%), muy cerca del líder Irish (53, 19.4%) y 47 pub (47, 17.2%).\n"
        "• Entre las mujeres, Chévere es el 2° bar favorito con 28 menciones (detrás de 47 pub con 33).\n"
        "• Capturando solo un 3% adicional del mercado local, Chévere se posicionará como el bar líder de la ciudad."
    ),
}

SECCIONES_RESUMEN_EJECUTIVO = [
    (
        "🎯 1. ¿Cuáles son las preferencias de las mujeres y qué prefieren los hombres?",
        "primary",
        "• Mujeres (152 encuestadas — 55.7% del mercado):\n"
        "  - Su máxima prioridad es la Música (39.5%, 60 clientes) y el Lugar / Ambiente (36.2%, 55 clientes), sumando el 75.7% de su interés.\n"
        "  - El Precio es tercer lugar (22.4%, 34 clientes). El Menú casi no influye en su decisión (solo 2.0%, 3 clientes).\n"
        "• Hombres (121 encuestados — 44.3% del mercado):\n"
        "  - Priorizan el Lugar / Ambiente (32.2%, 39 clientes) y la Música (27.3%, 33 clientes).\n"
        "  - A diferencia de las mujeres, los hombres muestran una alta valoración por el Menú (17.4%, 21 clientes) — una preferencia casi 9 veces mayor que la femenina.",
    ),
    (
        "💰 2. ¿Quién gasta más: los hombres o las mujeres?",
        "success",
        "• Los HOMBRES gastan significativamente más que las mujeres en todas las métricas analizadas:\n"
        "  - Gasto Real en Canjes de Cupón (Ingresos en Caja):\n"
        "    * Hombres: Generaron $38,120.00 MXN (83.5% del ingreso total de la campaña), con 83 cupones canjeados (tasa de conversión de 68.6%) y un ticket promedio de $459.28 MXN.\n"
        "    * Mujeres: Generaron $7,510.00 MXN (16.5% del ingreso total), con solo 30 cupones canjeados (tasa de conversión de 19.7%) y un ticket promedio de $250.33 MXN.\n"
        "  - Presupuesto Máximo Declarado:\n"
        "    * Hombres: $474.05 MXN en promedio (hasta $3,500 MXN).\n"
        "    * Mujeres: $354.57 MXN en promedio (hasta $3,000 MXN).",
    ),
    (
        "🚀 3. Recomendaciones Estratégicas para los Inversionistas de CHÉVERE",
        "warning",
        "• Posicionamiento Competitivo: CHÉVERE ocupa el 3er lugar general del mercado local (45 clientes, 16.5%), muy cerca de 47 pub (47) e Irish (53). Además, es el 2° bar favorito entre las mujeres (28 votos).\n"
        "• Ocasiones Clave: El 58.6% asiste con Amigos y el 24.9% por Eventos. La gran mayoría (81.0%) son clientes regulares o frecuentes.\n"
        "• Plan de Acción para Incrementar Ganancias:\n"
        "  1. Paquetes de Menú + Cerveza Artesanal: Dado el alto gasto de los hombres y su marcado interés en el menú, crear combos de alimentos y bebidas para grupos impulsará el ticket promedio sobre los $500 MXN.\n"
        "  2. Activar el Mercado Femenino: Las mujeres frecuentan Chévere por su ambiente y música, pero solo el 19.7% canjeó el cupón individual. Diseñar promociones musicales (noches acústicas, DJ) y paquetes de cumpleaños para grupos de amigas multiplicará su asistencia y consumo en barra.",
    ),
]


# -----------------------------------------------------------------------------
# 1. Estilos CSS Personalizados
# -----------------------------------------------------------------------------
ESTILOS_CSS = ui.tags.style("""
    body {
        background-color: #f8fafc;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .navbar {
        background-color: #ffffff !important;
        border-bottom: 2px solid #e2e8f0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        padding: 0.6rem 1.25rem;
    }
    .card {
        border-radius: 12px !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 1.5rem;
        background-color: #ffffff;
    }
    .card-header {
        background-color: #f8fafc !important;
        border-bottom: 1px solid #e2e8f0 !important;
        font-weight: 700;
        font-size: 1.05rem;
        color: #0f172a;
        padding: 0.85rem 1.25rem;
    }
    .nav-tabs .nav-link {
        font-weight: 600;
        font-size: 0.95rem;
        color: #475569;
        padding: 0.75rem 1.25rem;
    }
    .nav-tabs .nav-link.active {
        color: #0f172a !important;
        background-color: #ffffff !important;
        border-bottom: 3px solid #d97706 !important;
        font-weight: 700;
    }
    .bslib-value-box {
        border-radius: 12px !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        margin-bottom: 1.25rem;
    }
    .sidebar {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
        padding: 1.25rem 1rem;
    }
    .selector-destacado {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
        border: 2px solid #f59e0b !important;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1.25rem;
    }
""")


# -----------------------------------------------------------------------------
# 2. Funciones Auxiliares de Graficación (DRY)
# -----------------------------------------------------------------------------
def configurar_ejes(ax, pos, etiquetas, eje_valor: str, max_lim: float, orientacion: str, titulo: str):
    """Configura etiquetas, límites, grilla y título para gráficas verticales u horizontales."""
    if orientacion == "horizontal":
        ax.set_yticks(pos)
        ax.set_yticklabels(etiquetas, fontsize=11.5, fontweight="bold")
        ax.set_xlabel(eje_valor, fontsize=12, fontweight="bold")
        ax.set_xlim(0, max_lim)
        ax.grid(axis="x", linestyle="--", alpha=0.6, zorder=0)
    else:
        ax.set_xticks(pos)
        ax.set_xticklabels(etiquetas, fontsize=11.5, fontweight="bold")
        ax.set_ylabel(eje_valor, fontsize=12, fontweight="bold")
        ax.set_ylim(0, max_lim)
        ax.grid(axis="y", linestyle="--", alpha=0.6, zorder=0)
    ax.set_title(titulo, fontsize=14, fontweight="bold", pad=15)


def dibujar_barras_simples(
    ax, etiquetas, valores, orientacion: str, titulo: str, eje_valor: str,
    colores, bordes, fmt_fn, factor_lim: float = 1.28, ancho: float = 0.48
):
    """Dibuja gráficas de barras simples (verticales u horizontales) con anotaciones."""
    pos = np.arange(len(etiquetas))
    max_val = max(list(valores) + [1])
    es_horiz = orientacion == "horizontal"

    barras = (
        ax.barh(pos, valores, ancho, color=colores, edgecolor=bordes, alpha=0.9, zorder=3)
        if es_horiz
        else ax.bar(pos, valores, ancho, color=colores, edgecolor=bordes, alpha=0.9, zorder=3)
    )

    for b, val in zip(barras, valores):
        texto = fmt_fn(val, es_horiz)
        if es_horiz:
            ax.text(val + max_val * 0.02, b.get_y() + b.get_height() / 2, texto, va="center", fontsize=11, fontweight="bold")
        else:
            ax.text(b.get_x() + b.get_width() / 2, val + max_val * 0.02, texto, ha="center", va="bottom", fontsize=11, fontweight="bold")

    configurar_ejes(ax, pos, etiquetas, eje_valor, max_val * factor_lim, orientacion, titulo)


def dibujar_barras_agrupadas(
    ax, etiquetas, series: list[dict], orientacion: str, titulo: str, eje_valor: str,
    loc_leyenda: str = "upper right", ancho: float = 0.35
):
    """Dibuja gráficas de 2 series agrupadas (verticales u horizontales) con leyenda."""
    pos = np.arange(len(etiquetas))
    es_horiz = orientacion == "horizontal"
    max_val = max([max(s["valores"], default=0) for s in series] + [1])
    offsets = [-ancho / 2, ancho / 2]

    for offset, s in zip(offsets, series):
        barras = (
            ax.barh(pos + offset, s["valores"], ancho, label=s["label"], color=s["color"], edgecolor=s["edge"], alpha=0.9, zorder=3)
            if es_horiz
            else ax.bar(pos + offset, s["valores"], ancho, label=s["label"], color=s["color"], edgecolor=s["edge"], alpha=0.9, zorder=3)
        )
        if "fmt_fn" in s:
            for b, val in zip(barras, s["valores"]):
                texto = s["fmt_fn"](val, es_horiz)
                if es_horiz:
                    ax.text(val + max_val * 0.02, b.get_y() + b.get_height() / 2, texto, va="center", fontsize=11, fontweight="bold")
                else:
                    ax.text(b.get_x() + b.get_width() / 2, val + max_val * 0.02, texto, ha="center", va="bottom", fontsize=11, fontweight="bold")

    configurar_ejes(ax, pos, etiquetas, eje_valor, max_val * 1.26, orientacion, titulo)
    ax.legend(fontsize=11, frameon=True, facecolor="white", edgecolor="#cbd5e1", loc=loc_leyenda)


# -----------------------------------------------------------------------------
# 3. Interfaz de Usuario (UI)
# -----------------------------------------------------------------------------
KPI_CARDS_CONFIG = [
    ("Encuestados Filtrados", "kpi_total_encuestados", "kpi_sub_genero", "👥", "primary"),
    ("Tasa de Canje de Cupones", "kpi_tasa_canje", "kpi_sub_canje", "🎟️", "info"),
    ("Gasto Real en Canjes", "kpi_gasto_real", "kpi_sub_gasto_real", "💵", "success"),
    ("Presupuesto Promedio Declarado", "kpi_max_gastar", "kpi_sub_preferencia", "📊", "warning"),
]

app_ui = ui.page_sidebar(
    # --- PANEL LATERAL (SIDEBAR) ---
    ui.sidebar(
        # 1. CONFIGURACIÓN DE GRÁFICA (DESTACADO)
        ui.div(
            ui.h6("📊 Gráfica a Utilizar:", class_="fw-bold text-dark mb-2", style="font-size: 0.88rem;"),
            ui.input_select("grafica_seleccionada", None, OPCIONES_GRAFICAS, selected="pref_genero", width="100%"),
            ui.div(
                ui.input_radio_buttons(
                    "tipo_orientacion",
                    "Orientación de Barras:",
                    {"vertical": "Barras Verticales (Columnas)", "horizontal": "Barras Horizontales"},
                    selected="vertical",
                ),
                class_="mt-2",
            ),
            ui.div(
                ui.input_select(
                    "tamano_grafica",
                    "Tamaño de la Gráfica:",
                    {"grande": "Grande (Pantalla Completa - 560px)", "extragrande": "Extra Grande (Presentación - 680px)"},
                    selected="grande",
                ),
                class_="mt-2",
            ),
            class_="selector-destacado mb-3",
        ),

        # 2. FILTROS INTERACTIVOS
        ui.div(
            ui.h6("Filtros de Datos:", class_="fw-bold text-secondary text-uppercase mb-2", style="font-size: 0.75rem; letter-spacing: 1px;"),
            ui.input_radio_buttons(
                "filtro_genero",
                "Género:",
                {"todos": "Todos (Ambos)", "Mujer": "Mujeres (152)", "Hombre": "Hombres (121)"},
                selected="todos",
            ),
            ui.input_select("filtro_bar", "Bar Favorito:", OPCIONES_BAR, selected="todos"),
            ui.input_select("filtro_frecuencia", "Frecuencia de Visita:", OPCIONES_FRECUENCIA, selected="todas"),
            ui.input_select("filtro_ocupacion", "Ocupación:", OPCIONES_OCUPACION, selected="todas"),
            ui.input_select("filtro_ocasion", "Ocasión:", OPCIONES_OCASION, selected="todas"),
            ui.input_radio_buttons(
                "filtro_canje",
                "Canje de Cupón:",
                {"todos": "Todos los Encuestados", "Si": "Solo Canjeados (Sí)", "No": "No Canjeados (No)"},
                selected="todos",
            ),
            ui.input_slider("rango_edad", "Rango de Edad:", min=EDAD_MIN, max=EDAD_MAX, value=[EDAD_MIN, EDAD_MAX], step=1),
        ),
        width=330,
    ),

    ESTILOS_CSS,

    # --- SUBTÍTULO CONTEXTUAL ---
    ui.p(
        "Resultados del estudio de mercado (Mayo 2020) para la toma de decisiones e incremento de ganancias de los inversionistas.",
        class_="text-muted mb-3 pt-1",
        style="font-size: 0.95rem;",
    ),

    # --- TARJETAS DE INDICADORES (VALUE BOXES) ---
    ui.layout_columns(
        *[
            ui.value_box(
                titulo,
                ui.output_text(id_valor),
                ui.output_text(id_sub),
                showcase=ui.div(icono, style="font-size: 2.2rem;"),
                theme=tema,
            )
            for titulo, id_valor, id_sub, icono, tema in KPI_CARDS_CONFIG
        ],
        col_widths=[3, 3, 3, 3],
        class_="mb-2",
    ),

    # --- PESTAÑAS PRINCIPALES ---
    ui.navset_card_tab(
        # PESTAÑA 1: VISOR PRINCIPAL DE GRÁFICA
        ui.nav_panel(
            "📈 1. Visor de Gráfica en Pantalla Completa",
            ui.div(
                ui.card(
                    ui.card_header(
                        ui.output_text("titulo_grafica_activa"),
                        class_="d-flex justify-content-between align-items-center",
                    ),
                    ui.output_plot("grafico_principal", height="560px"),
                ),
                ui.card(
                    ui.card_header("💡 Análisis Ejecutivo y Conclusiones del Gráfico Actual"),
                    ui.output_ui("insight_grafica_activa"),
                ),
                class_="pt-2",
            ),
        ),

        # PESTAÑA 2: RESPUESTAS DIRECTAS A LOS INVERSIONISTAS
        ui.nav_panel(
            "📋 2. Respuestas a Preguntas Clave para Inversionistas",
            ui.div(
                ui.card(
                    ui.card_header("🎯 Conclusiones del Estudio de Mercado para Toma de Decisiones"),
                    ui.output_ui("resumen_ejecutivo_html"),
                ),
                class_="pt-2",
            ),
        ),

        # PESTAÑA 3: EXPLORADOR DE DATOS
        ui.nav_panel(
            "🔍 3. Explorador de Registros del Estudio",
            ui.div(
                ui.card(
                    ui.card_header("Muestra Detallada de los 273 Encuestados (Formato Interactivo)"),
                    ui.output_data_frame("tabla_datos"),
                ),
                class_="pt-2",
            ),
        ),
    ),

    # TÍTULO DE LA PÁGINA (CON LOGO ÚNICO EN LA BARRA DE NAVEGACIÓN SUPERIOR)
    title=ui.div(
        ui.img(
            src=LOGO_DATA_URI,
            alt="Logo Chévere",
            style="height: 40px; width: auto; margin-right: 12px; object-fit: contain; vertical-align: middle;",
        ),
        ui.span("CHÉVERE CERVEZA Y MÚSICA", style="font-weight: 800; font-size: 1.15rem; letter-spacing: 1px; color: #0f172a;"),
        class_="d-flex align-items-center",
    ),
    fillable=False,
)


# -----------------------------------------------------------------------------
# 4. Lógica del Servidor (Server)
# -----------------------------------------------------------------------------
def server(input, output, session):

    @reactive.calc
    def filtrar_datos() -> pd.DataFrame:
        df = DATOS_CHEVERE
        for input_id, columna, valor_todos in MAPA_FILTROS:
            val = getattr(input, input_id)()
            if val != valor_todos:
                df = df[df[columna] == val]

        edad_min, edad_max = input.rango_edad()
        return df[(df["Edad"] >= edad_min) & (df["Edad"] <= edad_max)]

    @reactive.calc
    def canjes_filtrados() -> pd.Series:
        df = filtrar_datos()
        return df[df["Canje Cupón"] == "Si"]["Total Gastado"].dropna()

    # --- KPIs REACTIVOS ---
    @render.text
    def kpi_total_encuestados():
        return f"{len(filtrar_datos())} clientes"

    @render.text
    def kpi_sub_genero():
        df = filtrar_datos()
        if df.empty:
            return "Sin datos"
        m = (df["Género"] == "Mujer").sum()
        h = (df["Género"] == "Hombre").sum()
        return f"Mujeres: {m} ({m / len(df) * 100:.0f}%) · Hombres: {h} ({h / len(df) * 100:.0f}%)"

    @render.text
    def kpi_tasa_canje():
        df = filtrar_datos()
        return "0.0%" if df.empty else f"{(df['Canje Cupón'] == 'Si').mean() * 100:.1f}%"

    @render.text
    def kpi_sub_canje():
        df = filtrar_datos()
        return f"{(df['Canje Cupón'] == 'Si').sum()} de {len(df)} cupones canjeados"

    @render.text
    def kpi_gasto_real():
        canjes = canjes_filtrados()
        return "$0 MXN" if canjes.empty else f"${canjes.sum():,.0f} MXN"

    @render.text
    def kpi_sub_gasto_real():
        canjes = canjes_filtrados()
        return "Ticket prom.: $0" if canjes.empty else f"Ticket promedio: ${canjes.mean():,.2f}"

    @render.text
    def kpi_max_gastar():
        df = filtrar_datos()
        return "$0.00 MXN" if df.empty else f"${df['Máximo Gastar'].mean():,.2f} MXN"

    @render.text
    def kpi_sub_preferencia():
        df = filtrar_datos()
        return "Factor top: N/A" if df.empty else f"Preferencia principal: {df['Preferencia'].mode().iloc[0]}"

    @render.text
    def titulo_grafica_activa():
        return OPCIONES_GRAFICAS.get(input.grafica_seleccionada(), "Gráfica Seleccionada")

    # --- GRÁFICO PRINCIPAL EN PANTALLA COMPLETA ---
    @render.plot
    def grafico_principal():
        df = filtrar_datos()
        opcion = input.grafica_seleccionada()
        orientacion = input.tipo_orientacion()
        figsize = (12.5, 6.2) if input.tamano_grafica() == "extragrande" else (11.5, 5.4)

        fig, ax = plt.subplots(figsize=figsize, dpi=120)

        if df.empty:
            ax.text(0.5, 0.5, "No hay registros disponibles con los filtros aplicados", ha="center", va="center", color="#64748b", fontsize=14, fontweight="bold")
            ax.axis("off")
            return fig

        # 1. PREFERENCIAS POR GÉNERO
        if opcion == "pref_genero":
            factores = ["Musica", "Lugar", "Precio", "Menu"]
            nombres = ["Música", "Lugar / Ambiente", "Precio", "Menú (Comida/Bebida)"]
            mujeres = [len(df[(df["Género"] == "Mujer") & (df["Preferencia"] == f)]) for f in factores]
            hombres = [len(df[(df["Género"] == "Hombre") & (df["Preferencia"] == f)]) for f in factores]
            tot_m, tot_h = sum(mujeres), sum(hombres)

            fmt_pct = lambda tot: (lambda v, h: f"{int(v)} ({v / tot * 100 if tot else 0:.1f}%)" if h else f"{int(v)}\n({v / tot * 100 if tot else 0:.1f}%)")
            dibujar_barras_agrupadas(
                ax, nombres,
                [
                    {"valores": mujeres, "label": f"Mujeres ({tot_m})", "color": "#ec4899", "edge": "#9d174d", "fmt_fn": fmt_pct(tot_m)},
                    {"valores": hombres, "label": f"Hombres ({tot_h})", "color": "#2563eb", "edge": "#1e40af", "fmt_fn": fmt_pct(tot_h)},
                ],
                orientacion,
                "Factores Preferidos al Asistir al Bar por Género",
                "Número de Clientes",
            )

        # 2. COMPARATIVA DE GASTO: PRESUPUESTO VS GASTO REAL
        elif opcion == "gasto_genero":
            generos = ["Mujer", "Hombre"]
            prom_max = [df[df["Género"] == g]["Máximo Gastar"].mean() if not df[df["Género"] == g].empty else 0 for g in generos]
            prom_real = [
                df[(df["Género"] == g) & (df["Canje Cupón"] == "Si")]["Total Gastado"].mean()
                if not df[(df["Género"] == g) & (df["Canje Cupón"] == "Si")].empty else 0
                for g in generos
            ]
            fmt_moneda = lambda v, _: f"${v:.2f} MXN"
            dibujar_barras_agrupadas(
                ax, ["Mujeres", "Hombres"],
                [
                    {"valores": prom_max, "label": "Presupuesto Máx. Declarado", "color": "#f59e0b", "edge": "#b45309", "fmt_fn": fmt_moneda},
                    {"valores": prom_real, "label": "Gasto Real Promedio en Canjes", "color": "#10b981", "edge": "#047857", "fmt_fn": fmt_moneda},
                ],
                orientacion,
                "Comparativa: Presupuesto Declarado vs. Gasto Real Promedio por Género",
                "Monto Promedio ($ MXN)",
                loc_leyenda="upper left",
                ancho=0.32,
            )

        # 3. INGRESOS REALES ACUMULADOS EN CANJES
        elif opcion == "ingresos_reales":
            canjes = df[df["Canje Cupón"] == "Si"]
            totales = [canjes[canjes["Género"] == g]["Total Gastado"].sum() for g in ["Mujer", "Hombre"]]
            gran_total = sum(totales)

            dibujar_barras_simples(
                ax, ["Mujeres", "Hombres"], totales, orientacion,
                "Ingresos Reales Recaudados en Canjes de Cupón por Género",
                "Total Gastado Acumulado ($ MXN)",
                colores=["#ec4899", "#2563eb"], bordes=["#9d174d", "#1e40af"],
                fmt_fn=lambda v, h: (
                    f"${v:,.0f} MXN ({v / gran_total * 100 if gran_total else 0:.1f}% del total)"
                    if h else f"${v:,.0f} MXN\n({v / gran_total * 100 if gran_total else 0:.1f}% del total)"
                ),
            )

        # 4. TASA DE CANJE / CONVERSIÓN DE CUPONES
        elif opcion == "tasa_canje":
            ct = (pd.crosstab(df["Género"], df["Canje Cupón"], normalize="index") * 100).reindex(index=["Mujer", "Hombre"], columns=["Si", "No"], fill_value=0.0)
            pct_si, pct_no = ct["Si"].values, ct["No"].values
            pos = np.arange(2)
            es_horiz = orientacion == "horizontal"

            if es_horiz:
                ax.barh(pos, pct_si, 0.45, label="Canjeado (Sí)", color="#10b981", edgecolor="#047857", alpha=0.9, zorder=3)
                ax.barh(pos, pct_no, 0.45, left=pct_si, label="No Canjeado", color="#e2e8f0", edgecolor="#94a3b8", alpha=0.85, zorder=3)
            else:
                ax.bar(pos, pct_si, 0.45, label="Canjeado (Sí)", color="#10b981", edgecolor="#047857", alpha=0.9, zorder=3)
                ax.bar(pos, pct_no, 0.45, bottom=pct_si, label="No Canjeado", color="#e2e8f0", edgecolor="#94a3b8", alpha=0.85, zorder=3)

            for i, (si, no) in enumerate(zip(pct_si, pct_no)):
                if si > 8:
                    coords = (si / 2, i) if es_horiz else (i, si / 2)
                    ax.text(*coords, f"{si:.1f}% Canjeó", ha="center", va="center", color="white", fontweight="bold", fontsize=11)
                if no > 8:
                    coords = (si + no / 2, i) if es_horiz else (i, si + no / 2)
                    ax.text(*coords, f"{no:.1f}% No", ha="center", va="center", color="#334155", fontweight="bold", fontsize=11)

            configurar_ejes(ax, pos, ["Mujeres", "Hombres"], "Porcentaje (%)", 108, orientacion, "Efectividad del Cupón: Tasa de Canje / Conversión por Género")
            ax.legend(fontsize=11, frameon=True, facecolor="white", edgecolor="#cbd5e1", loc="upper right")

        # 5. COMPETENCIA DE BARES LOCALES
        elif opcion == "bar_favorito":
            ct = pd.crosstab(df["Bar Favorito"], df["Género"]).reindex(columns=["Mujer", "Hombre"], fill_value=0)
            ct["Total"] = ct["Mujer"] + ct["Hombre"]
            ct = ct.sort_values("Total", ascending=True)

            y = np.arange(len(ct))
            ax.barh(y, ct["Mujer"], 0.55, label="Mujeres", color="#ec4899", edgecolor="#9d174d", alpha=0.9, zorder=3)
            ax.barh(y, ct["Hombre"], 0.55, left=ct["Mujer"], label="Hombres", color="#2563eb", edgecolor="#1e40af", alpha=0.9, zorder=3)

            max_tot = max(ct["Total"].max(), 1)
            for idx, (bar_name, row) in enumerate(ct.iterrows()):
                es_chevere = bar_name.lower() == "chevere"
                etiqueta = f"{int(row['Total'])} ({row['Total'] / len(df) * 100:.1f}%)" + (" ⭐ [CHÉVERE]" if es_chevere else "")
                ax.text(row["Total"] + max_tot * 0.02, idx, etiqueta, va="center", fontsize=11, fontweight="bold", color="#b45309" if es_chevere else "#1e293b")

            configurar_ejes(ax, y, ct.index, "Número de Clientes", max_tot * 1.35, "horizontal", "Preferencia de Bares Locales (Chévere vs. Competencia)")
            ax.legend(fontsize=11, frameon=True, facecolor="white", edgecolor="#cbd5e1", loc="lower right")

        # 6. FRECUENCIA DE ASISTENCIA A BARES
        elif opcion == "frecuencia_visita":
            orden = [f for f in ["Regular", "Frecuente", "Raramente"] if f in df["Frecuencia Visita"].unique()]
            conteo = df["Frecuencia Visita"].value_counts().reindex(orden, fill_value=0)
            colores = ["#3b82f6", "#10b981", "#f97316"][:len(conteo)]

            if orientacion == "horizontal":
                dibujar_barras_simples(
                    ax, conteo.index, conteo.values, "horizontal",
                    "Frecuencia de Asistencia a Bares de los Clientes", "Cantidad de Clientes",
                    colores=colores, bordes="#1e293b",
                    fmt_fn=lambda v, _: f"{v} clientes ({v / len(df) * 100:.1f}%)",
                )
            else:
                _, texts, autotexts = ax.pie(
                    conteo.values, labels=conteo.index, autopct="%1.1f%%", startangle=130, colors=colores,
                    wedgeprops={"width": 0.45, "edgecolor": "white", "linewidth": 3}, pctdistance=0.75,
                )
                plt.setp(autotexts, color="white", fontweight="bold", fontsize=12)
                plt.setp(texts, fontsize=12.5, fontweight="bold")
                ax.set_title("Frecuencia de Asistencia a Bares de los Clientes", fontsize=14, fontweight="bold", pad=15)

        # 7. OCASIONES DE ASISTENCIA SEGÚN GÉNERO
        elif opcion == "ocasiones_visita":
            ct = pd.crosstab(df["Ocasiones"], df["Género"]).reindex(columns=["Mujer", "Hombre"], fill_value=0)
            ct["Total"] = ct["Mujer"] + ct["Hombre"]
            ct = ct.sort_values("Total", ascending=(orientacion == "horizontal"))

            dibujar_barras_agrupadas(
                ax, ct.index,
                [
                    {"valores": ct["Mujer"].values, "label": "Mujeres", "color": "#ec4899", "edge": "#9d174d"},
                    {"valores": ct["Hombre"].values, "label": "Hombres", "color": "#2563eb", "edge": "#1e40af"},
                ],
                orientacion,
                "Motivo u Ocasión de Asistencia al Bar Desglosado por Género",
                "Número de Clientes",
            )
            max_tot = max(ct["Total"].max(), 1)
            for idx, (_, row) in enumerate(ct.iterrows()):
                if orientacion == "horizontal":
                    ax.text( max(row["Mujer"], row["Hombre"]) + max_tot * 0.02, idx, f"Total: {row['Total']} ({row['Total'] / len(df) * 100:.1f}%)", va="center", fontsize=11, fontweight="bold")
                else:
                    ax.text(idx, max(row["Mujer"], row["Hombre"]) + max_tot * 0.02, f"Total: {row['Total']}\n({row['Total'] / len(df) * 100:.1f}%)", ha="center", va="bottom", fontsize=11, fontweight="bold")

        # 8. TICKET PROMEDIO POR BAR FAVORITO
        elif opcion == "ticket_bar":
            canjes = df[df["Canje Cupón"] == "Si"]
            if canjes.empty:
                ax.text(0.5, 0.5, "No hay canjes de cupón en esta selección", ha="center", va="center", color="#64748b", fontsize=13)
                ax.axis("off")
                return fig

            prom = canjes.groupby("Bar Favorito")["Total Gastado"].mean().sort_values(ascending=True)
            colores = ["#f59e0b" if b.lower() == "chevere" else "#3b82f6" for b in prom.index]
            bordes = ["#b45309" if b.lower() == "chevere" else "#1d4ed8" for b in prom.index]

            dibujar_barras_simples(
                ax, prom.index, prom.values, "horizontal",
                "Consumo Real Promedio por Visita según Bar Favorito",
                "Ticket Promedio de Gasto Real en Canjes ($ MXN)",
                colores=colores, bordes=bordes,
                fmt_fn=lambda v, _: f"${v:.2f} MXN", ancho=0.55,
            )

        # 9. OCUPACIÓN DE LOS CLIENTES
        elif opcion == "ocupacion_clientes":
            conteo = df["Ocupación"].value_counts()
            dibujar_barras_simples(
                ax, conteo.index, conteo.values, orientacion,
                "Distribución de Clientes por Ocupación", "Cantidad de Clientes",
                colores="#6366f1", bordes="#4338ca",
                fmt_fn=lambda v, h: f"{v} ({v / len(df) * 100:.1f}%)" if h else f"{v}\n({v / len(df) * 100:.1f}%)",
            )

        # 10. RELACIÓN EDAD VS PRESUPUESTO
        elif opcion == "edad_presupuesto":
            for gen, color, edge in [("Mujer", "#ec4899", "#9d174d"), ("Hombre", "#2563eb", "#1e40af")]:
                sub = df[df["Género"] == gen]
                if not sub.empty:
                    ax.scatter(
                        sub["Edad"], sub["Máximo Gastar"],
                        label=f"{gen}s ({len(sub)} clientes)",
                        color=color, edgecolor=edge, alpha=0.8, s=80, zorder=3,
                    )
            ax.set_xlabel("Edad del Cliente (Años)", fontsize=12, fontweight="bold")
            ax.set_ylabel("Presupuesto Máximo Dispuesto a Gastar ($ MXN)", fontsize=12, fontweight="bold")
            ax.set_title("Dispersión: Edad vs. Presupuesto Máximo Declarado", fontsize=14, fontweight="bold", pad=15)
            ax.legend(fontsize=11, frameon=True, facecolor="white", edgecolor="#cbd5e1", loc="upper left")
            ax.grid(True, linestyle="--", alpha=0.6, zorder=0)

        plt.tight_layout()
        return fig

    # --- INSIGHT DINÁMICO DE LA GRÁFICA ACTIVA ---
    @render.ui
    def insight_grafica_activa():
        opcion = input.grafica_seleccionada()
        if opcion == "ingresos_reales":
            canjes = filtrar_datos()
            canjes = canjes[canjes["Canje Cupón"] == "Si"]
            tot_h = canjes[canjes["Género"] == "Hombre"]["Total Gastado"].sum()
            tot_m = canjes[canjes["Género"] == "Mujer"]["Total Gastado"].sum()
            gran_tot = tot_h + tot_m
            pct_h = (tot_h / gran_tot * 100) if gran_tot else 0
            pct_m = (tot_m / gran_tot * 100) if gran_tot else 0
            texto = (
                f"📌 Total Acumulado en Caja por Canjes de Cupón:\n"
                f"• Hombres: Generaron ${tot_h:,.0f} MXN ({pct_h:.1f}% de la recaudación total de la campaña).\n"
                f"• Mujeres: Generaron ${tot_m:,.0f} MXN ({pct_m:.1f}% de la recaudación total).\n"
                f"• Total Global: ${gran_tot:,.0f} MXN en ventas directas generadas a través de la estrategia de cupones."
            )
        else:
            texto = INSIGHTS_ESTATICOS.get(
                opcion,
                "📌 Este gráfico refleja el comportamiento de los clientes del estudio de mercado según los filtros activos. "
                "Modifica los filtros en la barra lateral para observar variaciones por ocupación, bar favorito, edad o asistencia.",
            )

        return ui.p(texto, class_="mb-0", style="white-space: pre-line; line-height: 1.5;")

    # --- RESUMEN EJECUTIVO PARA INVERSIONISTAS ---
    @render.ui
    def resumen_ejecutivo_html():
        return ui.div(
            *[
                ui.div(
                    ui.h5(titulo, class_=f"fw-bold text-{color} mb-2"),
                    ui.p(contenido, class_="mb-0", style="white-space: pre-line; line-height: 1.5;"),
                    class_=f"p-3 mb-3 bg-light rounded border-start border-4 border-{color}",
                )
                for titulo, color, contenido in SECCIONES_RESUMEN_EJECUTIVO
            ]
        )

    # --- TABLA DE DATOS INTERACTIVA ---
    @render.data_frame
    def tabla_datos():
        df = filtrar_datos().copy()
        df["Total Gastado"] = df["Total Gastado"].fillna(0).map(lambda x: f"${x:,.0f}" if x > 0 else "—")
        for col in ["Máximo Gastar", "Ingresos"]:
            df[col] = df[col].map(lambda x: f"${x:,.0f}")

        cols = [
            "FormID", "Fecha", "Género", "Edad", "Ocupación", "Ingresos",
            "Bar Favorito", "Preferencia", "Frecuencia Visita", "Ocasiones",
            "Máximo Gastar", "Canje Cupón", "Total Gastado",
        ]
        return render.DataGrid(df[cols], height="440px")


# -----------------------------------------------------------------------------
# 5. Inicialización de la Aplicación
# -----------------------------------------------------------------------------
app = App(app_ui, server)

if __name__ == "__main__":
    app.run(port=8003)
