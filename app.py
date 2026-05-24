import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# =========================
# CONFIGURACIÓN GENERAL
# =========================

st.set_page_config(
    page_title="Buscador I+D Futuro | JOBU Strategy",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent

EXCEL_FILENAME = "Buscador_ID_Futuro_JOBU.xlsx"
LOGO_FILENAME = "jobu_strategy_logo.png"

# El Excel puede estar suelto junto a app.py o dentro de /data
POSSIBLE_DATA_FILES = [
    BASE_DIR / EXCEL_FILENAME,
    BASE_DIR / "data" / EXCEL_FILENAME,
    Path.cwd() / EXCEL_FILENAME,
    Path.cwd() / "data" / EXCEL_FILENAME,
]

# El logo puede estar dentro de /assets o suelto junto a app.py
POSSIBLE_LOGO_FILES = [
    BASE_DIR / "assets" / LOGO_FILENAME,
    BASE_DIR / LOGO_FILENAME,
    Path.cwd() / "assets" / LOGO_FILENAME,
    Path.cwd() / LOGO_FILENAME,
]


def find_first_existing_file(possible_files):
    """
    Devuelve el primer archivo existente de una lista de rutas posibles.
    Si no encuentra ninguno, devuelve None.
    """
    for file_path in possible_files:
        if file_path.exists():
            return file_path
    return None


DATA_FILE = find_first_existing_file(POSSIBLE_DATA_FILES)
LOGO_FILE = find_first_existing_file(POSSIBLE_LOGO_FILES)


# =========================
# ESTILOS
# =========================

st.markdown("""
<style>
.block-container {padding-top: 1.3rem; padding-bottom: 2rem;}
[data-testid="stSidebar"] {background: linear-gradient(180deg, #031633 0%, #071c3d 50%, #020914 100%);} 
[data-testid="stSidebar"] * {color: white;}
.jobu-card {background: white; border-radius: 18px; padding: 20px 22px; box-shadow: 0 8px 24px rgba(7,28,61,.08); border: 1px solid rgba(7,28,61,.06);} 
.jobu-kpi-title {color:#5b6470; font-size:.85rem; font-weight:600;}
.jobu-kpi-value {color:#071c3d; font-size:2.0rem; font-weight:800; line-height:1.05;}
.jobu-kpi-sub {color:#5b6470; font-size:.82rem; margin-top:.15rem;}
.hero-title {font-size:2.15rem; line-height:1.05; font-weight:900; color:#071c3d; margin-bottom:0;}
.hero-subtitle {color:#5b6470; font-size:1rem; margin-top:.25rem;}
.badge {display:inline-block; padding:.25rem .6rem; background:#0b3d91; color:white; border-radius:999px; font-size:.78rem; font-weight:700; margin-left:.5rem; vertical-align:middle;}
.section-title {color:#071c3d; font-size:1.25rem; font-weight:800; margin-top:.3rem; margin-bottom:.6rem;}
.footer-note {color:#5b6470; font-size:.76rem; text-align:center; margin-top:1rem;}
</style>
""", unsafe_allow_html=True)


# =========================
# FUNCIONES
# =========================

@st.cache_data(show_spinner=False)
def load_data_from_path(path: str) -> pd.DataFrame:
    """
    Carga el Excel desde una ruta local.
    """
    return read_excel_data(path)


@st.cache_data(show_spinner=False)
def load_data_from_upload(uploaded_file_bytes: bytes) -> pd.DataFrame:
    """
    Carga el Excel desde un archivo subido manualmente en Streamlit.
    """
    return read_excel_data(io.BytesIO(uploaded_file_bytes))


def read_excel_data(source) -> pd.DataFrame:
    """
    Lee el Excel intentando primero la hoja Screener_I+D.
    Si esa hoja no existe, lee la primera hoja disponible.
    """
    try:
        excel_file = pd.ExcelFile(source)

        if "Screener_I+D" in excel_file.sheet_names:
            df = pd.read_excel(source, sheet_name="Screener_I+D")
        else:
            df = pd.read_excel(source, sheet_name=excel_file.sheet_names[0])

        numeric_cols = [
            "Tecnología",
            "Catalizadores",
            "Caja",
            "Mercado",
            "Validación",
            "Control Dilución",
            "Momentum",
            "Score"
        ]

        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

        if "Score" in df.columns:
            df = df.sort_values("Score", ascending=False)

        return df

    except Exception as e:
        st.error(f"Error al leer el archivo Excel: {e}")
        return pd.DataFrame()


def classify_score(score):
    if pd.isna(score):
        return "Sin clasificar"
    if score >= 80:
        return "I+D muy prometedor"
    if score >= 65:
        return "Candidata interesante"
    if score >= 50:
        return "Vigilar"
    return "Descartar"


def render_kpi(title, value, sub=""):
    st.markdown(f"""
    <div class="jobu-card">
        <div class="jobu-kpi-title">{title}</div>
        <div class="jobu-kpi-value">{value}</div>
        <div class="jobu-kpi-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def to_excel_bytes(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Screener_filtrado")
    return output.getvalue()


# =========================
# CARGA DEL EXCEL
# =========================

uploaded_excel = None

if DATA_FILE is not None:
    df = load_data_from_path(str(DATA_FILE))
else:
    st.warning(
        "No se ha encontrado el archivo Excel automáticamente. "
        "Puedes subirlo manualmente aquí."
    )

    uploaded_excel = st.file_uploader(
        "Subir archivo Excel Buscador_ID_Futuro_JOBU.xlsx",
        type=["xlsx"]
    )

    if uploaded_excel is not None:
        df = load_data_from_upload(uploaded_excel.getvalue())
    else:
        st.error(
            "No se ha encontrado la base de datos Excel. "
            "Coloca el archivo 'Buscador_ID_Futuro_JOBU.xlsx' junto a app.py, "
            "o dentro de la carpeta /data, o súbelo manualmente desde este panel."
        )

        with st.expander("Rutas comprobadas"):
            for path in POSSIBLE_DATA_FILES:
                st.code(str(path))

        st.stop()


if df.empty:
    st.error(
        "El archivo Excel se ha encontrado, pero no contiene datos válidos "
        "o no se ha podido leer correctamente."
    )
    st.stop()


if "Clasificación" not in df.columns and "Score" in df.columns:
    df["Clasificación"] = df["Score"].apply(classify_score)


# =========================
# SIDEBAR
# =========================

with st.sidebar:
    if LOGO_FILE is not None:
        st.image(str(LOGO_FILE), use_container_width=True)

    st.markdown("## Modelo JOBU")
    st.markdown("**Buscador I+D Futuro**")
    st.caption("Screener de empresas con proyectos de I+D prometedores")

    if DATA_FILE is not None:
        st.success(f"Excel cargado: {DATA_FILE.name}")
    elif uploaded_excel is not None:
        st.success(f"Excel subido: {uploaded_excel.name}")

    st.divider()

    sectores = sorted(df["Sector"].dropna().unique().tolist()) if "Sector" in df.columns else []
    estados = sorted(df["Clasificación"].dropna().unique().tolist()) if "Clasificación" in df.columns else []

    selected_sectors = st.multiselect(
        "Sectores",
        options=sectores,
        default=sectores
    )

    selected_status = st.multiselect(
        "Clasificación",
        options=estados,
        default=estados
    )

    min_score = st.slider(
        "Score mínimo",
        0,
        100,
        60,
        1
    )

    search = st.text_input(
        "Buscar ticker o empresa",
        ""
    )

    st.divider()

    st.markdown("### Pesos del modelo")
    st.caption("Referencia del score base")
    st.write("Tecnología: **25%**")
    st.write("Catalizadores: **20%**")
    st.write("Caja: **20%**")
    st.write("Mercado: **15%**")
    st.write("Validación: **10%**")
    st.write("Momentum: **10%**")


# =========================
# FILTROS
# =========================

filtered = df.copy()

if selected_sectors and "Sector" in filtered.columns:
    filtered = filtered[filtered["Sector"].isin(selected_sectors)]

if selected_status and "Clasificación" in filtered.columns:
    filtered = filtered[filtered["Clasificación"].isin(selected_status)]

if "Score" in filtered.columns:
    filtered = filtered[filtered["Score"] >= min_score]

if search:
    s = search.lower()
    mask = pd.Series(False, index=filtered.index)

    if "Ticker" in filtered.columns:
        mask |= filtered["Ticker"].astype(str).str.lower().str.contains(s, na=False)

    if "Empresa" in filtered.columns:
        mask |= filtered["Empresa"].astype(str).str.lower().str.contains(s, na=False)

    filtered = filtered[mask]


# =========================
# CABECERA
# =========================

left, right = st.columns([.75, .25], vertical_alignment="center")

with left:
    st.markdown("""
    <div class="hero-title">
        BUSCADOR I+D FUTURO <span class="badge">Modelo JOBU</span>
    </div>
    <div class="hero-subtitle">
        Screener de empresas con proyectos de I+D prometedores: tecnología, caja, catalizadores, validación, mercado y momentum.
    </div>
    """, unsafe_allow_html=True)

with right:
    st.download_button(
        "⬇️ Descargar Excel filtrado",
        data=to_excel_bytes(filtered),
        file_name="Buscador_ID_Futuro_JOBU_filtrado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

st.write("")


# =========================
# KPIS
# =========================

total = len(filtered)

score_medio = filtered["Score"].mean() if "Score" in filtered.columns and total else 0
top_score = filtered["Score"].max() if "Score" in filtered.columns and total else 0
top_row = filtered.iloc[0] if total else None

if top_row is not None and {"Ticker", "Empresa"}.issubset(filtered.columns):
    top_name = f"{top_row['Ticker']} · {top_row['Empresa']}"
else:
    top_name = "-"

candidatas = int((filtered["Score"] >= 65).sum()) if "Score" in filtered.columns else 0

k1, k2, k3, k4 = st.columns(4)

with k1:
    render_kpi("Empresas filtradas", f"{total}", "Universo activo")

with k2:
    render_kpi("Score medio", f"{score_medio:.1f}/100", "Calidad media")

with k3:
    render_kpi("Candidatas ≥65", f"{candidatas}", "Interesantes o superiores")

with k4:
    render_kpi("Top score", f"{top_score:.0f}", top_name)

st.write("")


# =========================
# GRÁFICOS PRINCIPALES
# =========================

c1, c2 = st.columns([.58, .42])

with c1:
    st.markdown(
        '<div class="section-title">Ranking de candidatas</div>',
        unsafe_allow_html=True
    )

    top_rank = filtered.head(15).copy()

    if not top_rank.empty and "Score" in top_rank.columns and "Ticker" in top_rank.columns:
        fig = px.bar(
            top_rank.sort_values("Score"),
            x="Score",
            y="Ticker",
            orientation="h",
            color="Score",
            color_continuous_scale="Blues",
            hover_data=[
                c for c in [
                    "Empresa",
                    "Sector",
                    "Clasificación",
                    "Catalizador próximo"
                ]
                if c in top_rank.columns
            ],
            range_x=[0, 100],
            title="Top 15 por Score I+D"
        )

        fig.update_layout(
            height=430,
            margin=dict(l=10, r=20, t=55, b=10),
            coloraxis_showscale=False,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar el ranking.")

with c2:
    st.markdown(
        '<div class="section-title">Composición del score</div>',
        unsafe_allow_html=True
    )

    weights = pd.DataFrame({
        "Criterio": [
            "Tecnología",
            "Catalizadores",
            "Caja",
            "Mercado",
            "Validación",
            "Momentum"
        ],
        "Peso": [25, 20, 20, 15, 10, 10]
    })

    fig = px.pie(
        weights,
        values="Peso",
        names="Criterio",
        hole=.58,
        title="Pesos del modelo JOBU"
    )

    fig.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)


# =========================
# SECTORES Y RIESGO
# =========================

c3, c4 = st.columns(2)

with c3:
    st.markdown(
        '<div class="section-title">Sectores con mayor potencial</div>',
        unsafe_allow_html=True
    )

    if "Sector" in filtered.columns and "Score" in filtered.columns and not filtered.empty:
        sector_score = (
            filtered
            .groupby("Sector", as_index=False)
            .agg(
                Score_medio=("Score", "mean"),
                Empresas=("Ticker", "count") if "Ticker" in filtered.columns else ("Score", "count")
            )
            .sort_values("Score_medio", ascending=False)
        )

        fig = px.bar(
            sector_score,
            x="Sector",
            y="Score_medio",
            color="Score_medio",
            color_continuous_scale="Blues",
            hover_data=["Empresas"],
            title="Score medio por sector",
            range_y=[0, 100]
        )

        fig.update_layout(
            height=390,
            margin=dict(l=10, r=20, t=55, b=90),
            xaxis_tickangle=-35,
            coloraxis_showscale=False,
            paper_bgcolor="white",
            plot_bgcolor="white"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos suficientes para mostrar sectores.")

with c4:
    st.markdown(
        '<div class="section-title">Riesgo vs potencial</div>',
        unsafe_allow_html=True
    )

    needed = {
        "Control Dilución",
        "Tecnología",
        "Mercado",
        "Catalizadores",
        "Validación",
        "Score"
    }

    if needed.issubset(set(filtered.columns)) and not filtered.empty:
        scatter = filtered.copy()

        scatter["Riesgo"] = 100 - scatter["Control Dilución"]
        scatter["Potencial"] = (
            scatter["Tecnología"] * .35
            + scatter["Mercado"] * .35
            + scatter["Catalizadores"] * .20
            + scatter["Validación"] * .10
        )

        fig = px.scatter(
            scatter,
            x="Riesgo",
            y="Potencial",
            size="Score",
            color="Clasificación" if "Clasificación" in scatter.columns else "Score",
            hover_name="Ticker" if "Ticker" in scatter.columns else None,
            hover_data=[
                c for c in [
                    "Empresa",
                    "Sector",
                    "Score",
                    "Catalizador próximo",
                    "Riesgo principal"
                ]
                if c in scatter.columns
            ],
            title="Mapa de riesgo financiero/dilución frente a potencial"
        )

        fig.update_layout(
            height=390,
            margin=dict(l=10, r=20, t=55, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white"
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay columnas suficientes para mostrar el mapa de riesgo.")


# =========================
# RADAR
# =========================

st.markdown(
    '<div class="section-title">Perfil medio del universo filtrado</div>',
    unsafe_allow_html=True
)

radar_cols = [
    "Tecnología",
    "Catalizadores",
    "Caja",
    "Mercado",
    "Validación",
    "Momentum"
]

available = [c for c in radar_cols if c in filtered.columns]

if available and not filtered.empty:
    radar = filtered[available].mean().reset_index()
    radar.columns = ["Criterio", "Valor"]

    fig = px.line_polar(
        radar,
        r="Valor",
        theta="Criterio",
        line_close=True,
        range_r=[0, 100],
        title="Radar medio del modelo"
    )

    fig.update_traces(fill="toself")

    fig.update_layout(
        height=430,
        margin=dict(l=10, r=10, t=55, b=10),
        paper_bgcolor="white"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hay datos suficientes para mostrar el radar.")


# =========================
# TABLA PRINCIPAL
# =========================

st.markdown(
    '<div class="section-title">Tabla principal del screener</div>',
    unsafe_allow_html=True
)

show_cols = [
    "Ticker",
    "Empresa",
    "Sector",
    "Proyecto I+D",
    "Fase",
    "Score",
    "Clasificación",
    "Caja / Runway",
    "Riesgo Dilución",
    "Catalizador próximo",
    "Validación externa",
    "Riesgo principal"
]

show_cols = [c for c in show_cols if c in filtered.columns]
table_df = filtered[show_cols].copy()

if not table_df.empty:
    if "Score" in table_df.columns:
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn(
                    "Score",
                    min_value=0,
                    max_value=100,
                    format="%d"
                )
            }
        )
    else:
        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True
        )
else:
    st.info("No hay datos con los filtros seleccionados.")


# =========================
# ALERTAS
# =========================

st.markdown(
    '<div class="section-title">Alertas de seguimiento</div>',
    unsafe_allow_html=True
)

alerts = []

for _, row in filtered.iterrows():
    ticker = row.get("Ticker", "")
    empresa = row.get("Empresa", "")

    if "Caja" in row and pd.notna(row["Caja"]) and row["Caja"] < 60:
        alerts.append({
            "Ticker": ticker,
            "Empresa": empresa,
            "Alerta": "Caja / runway débil",
            "Prioridad": "Alta",
            "Acción": "Revisar posible dilución, deuda convertible o necesidad de financiación."
        })

    if "Control Dilución" in row and pd.notna(row["Control Dilución"]) and row["Control Dilución"] < 60:
        alerts.append({
            "Ticker": ticker,
            "Empresa": empresa,
            "Alerta": "Riesgo de dilución",
            "Prioridad": "Alta",
            "Acción": "Revisar ATM, warrants, ampliaciones o reverse split."
        })

    if "Catalizadores" in row and pd.notna(row["Catalizadores"]) and row["Catalizadores"] >= 80:
        alerts.append({
            "Ticker": ticker,
            "Empresa": empresa,
            "Alerta": "Catalizador relevante",
            "Prioridad": "Media/Alta",
            "Acción": "Vigilar datos clínicos, FDA/EMA, contratos o hitos comerciales."
        })

alerts_df = pd.DataFrame(alerts)

if not alerts_df.empty:
    st.dataframe(
        alerts_df,
        use_container_width=True,
        hide_index=True
    )
else:
    st.success("No se han detectado alertas con los filtros actuales.")


# =========================
# FOOTER
# =========================

st.markdown(
    '<div class="footer-note">Este dashboard es una herramienta de análisis cuantitativo y cualitativo. No constituye asesoramiento financiero ni recomendación de inversión.</div>',
    unsafe_allow_html=True
)
