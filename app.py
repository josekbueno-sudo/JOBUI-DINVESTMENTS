import io
from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Buscador I+D Futuro | JOBU Strategy", page_icon="🔬", layout="wide", initial_sidebar_state="expanded")
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "Buscador_ID_Futuro_JOBU.xlsx"
LOGO_FILE = BASE_DIR / "assets" / "jobu_strategy_logo.png"

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

@st.cache_data(show_spinner=False)
def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_excel(path, sheet_name="Screener_I+D")
    numeric_cols = ["Tecnología", "Catalizadores", "Caja", "Mercado", "Validación", "Control Dilución", "Momentum", "Score"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    if "Score" in df.columns:
        df = df.sort_values("Score", ascending=False)
    return df

def classify_score(score):
    if pd.isna(score): return "Sin clasificar"
    if score >= 80: return "I+D muy prometedor"
    if score >= 65: return "Candidata interesante"
    if score >= 50: return "Vigilar"
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

df = load_data(DATA_FILE)
if df.empty:
    st.error("No se ha encontrado la base de datos Excel en data/Buscador_ID_Futuro_JOBU.xlsx")
    st.stop()
if "Clasificación" not in df.columns and "Score" in df.columns:
    df["Clasificación"] = df["Score"].apply(classify_score)

with st.sidebar:
    if LOGO_FILE.exists():
        st.image(str(LOGO_FILE), use_container_width=True)
    st.markdown("## Modelo JOBU")
    st.markdown("**Buscador I+D Futuro**")
    st.caption("Screener de empresas con proyectos de I+D prometedores")
    st.divider()
    sectores = sorted(df["Sector"].dropna().unique().tolist()) if "Sector" in df.columns else []
    estados = sorted(df["Clasificación"].dropna().unique().tolist()) if "Clasificación" in df.columns else []
    selected_sectors = st.multiselect("Sectores", options=sectores, default=sectores)
    selected_status = st.multiselect("Clasificación", options=estados, default=estados)
    min_score = st.slider("Score mínimo", 0, 100, 60, 1)
    search = st.text_input("Buscar ticker o empresa", "")
    st.divider()
    st.markdown("### Pesos del modelo")
    st.caption("Referencia del score base")
    st.write("Tecnología: **25%**")
    st.write("Catalizadores: **20%**")
    st.write("Caja: **20%**")
    st.write("Mercado: **15%**")
    st.write("Validación: **10%**")
    st.write("Momentum: **10%**")

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

left, right = st.columns([.75, .25], vertical_alignment="center")
with left:
    st.markdown("""
    <div class="hero-title">BUSCADOR I+D FUTURO <span class="badge">Modelo JOBU</span></div>
    <div class="hero-subtitle">Screener de empresas con proyectos de I+D prometedores: tecnología, caja, catalizadores, validación, mercado y momentum.</div>
    """, unsafe_allow_html=True)
with right:
    st.download_button("⬇️ Descargar Excel filtrado", data=to_excel_bytes(filtered), file_name="Buscador_ID_Futuro_JOBU_filtrado.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
st.write("")

total = len(filtered)
score_medio = filtered["Score"].mean() if "Score" in filtered.columns and total else 0
top_score = filtered["Score"].max() if "Score" in filtered.columns and total else 0
top_row = filtered.iloc[0] if total else None
top_name = f"{top_row['Ticker']} · {top_row['Empresa']}" if top_row is not None and {"Ticker","Empresa"}.issubset(filtered.columns) else "-"
candidatas = int((filtered["Score"] >= 65).sum()) if "Score" in filtered.columns else 0

k1,k2,k3,k4 = st.columns(4)
with k1: render_kpi("Empresas filtradas", f"{total}", "Universo activo")
with k2: render_kpi("Score medio", f"{score_medio:.1f}/100", "Calidad media")
with k3: render_kpi("Candidatas ≥65", f"{candidatas}", "Interesantes o superiores")
with k4: render_kpi("Top score", f"{top_score:.0f}", top_name)
st.write("")

c1, c2 = st.columns([.58, .42])
with c1:
    st.markdown('<div class="section-title">Ranking de candidatas</div>', unsafe_allow_html=True)
    top_rank = filtered.head(15).copy()
    if not top_rank.empty:
        fig = px.bar(top_rank.sort_values("Score"), x="Score", y="Ticker", orientation="h", color="Score", color_continuous_scale="Blues", hover_data=[c for c in ["Empresa","Sector","Clasificación","Catalizador próximo"] if c in top_rank.columns], range_x=[0,100], title="Top 15 por Score I+D")
        fig.update_layout(height=430, margin=dict(l=10,r=20,t=55,b=10), coloraxis_showscale=False, plot_bgcolor="white", paper_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos con los filtros seleccionados.")
with c2:
    st.markdown('<div class="section-title">Composición del score</div>', unsafe_allow_html=True)
    weights = pd.DataFrame({"Criterio":["Tecnología","Catalizadores","Caja","Mercado","Validación","Momentum"], "Peso":[25,20,20,15,10,10]})
    fig = px.pie(weights, values="Peso", names="Criterio", hole=.58, title="Pesos del modelo JOBU")
    fig.update_layout(height=430, margin=dict(l=10,r=10,t=55,b=10), paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)
with c3:
    st.markdown('<div class="section-title">Sectores con mayor potencial</div>', unsafe_allow_html=True)
    if "Sector" in filtered.columns and "Score" in filtered.columns and not filtered.empty:
        sector_score = filtered.groupby("Sector", as_index=False).agg(Score_medio=("Score","mean"), Empresas=("Ticker","count")).sort_values("Score_medio", ascending=False)
        fig = px.bar(sector_score, x="Sector", y="Score_medio", color="Score_medio", color_continuous_scale="Blues", hover_data=["Empresas"], title="Score medio por sector", range_y=[0,100])
        fig.update_layout(height=390, margin=dict(l=10,r=20,t=55,b=90), xaxis_tickangle=-35, coloraxis_showscale=False, paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)
with c4:
    st.markdown('<div class="section-title">Riesgo vs potencial</div>', unsafe_allow_html=True)
    needed = {"Control Dilución","Tecnología","Mercado","Catalizadores","Validación","Score"}
    if needed.issubset(set(filtered.columns)) and not filtered.empty:
        scatter = filtered.copy()
        scatter["Riesgo"] = 100 - scatter["Control Dilución"]
        scatter["Potencial"] = scatter["Tecnología"]*.35 + scatter["Mercado"]*.35 + scatter["Catalizadores"]*.20 + scatter["Validación"]*.10
        fig = px.scatter(scatter, x="Riesgo", y="Potencial", size="Score", color="Clasificación" if "Clasificación" in scatter.columns else "Score", hover_name="Ticker", hover_data=[c for c in ["Empresa","Sector","Score","Catalizador próximo","Riesgo principal"] if c in scatter.columns], title="Mapa de riesgo financiero/dilución frente a potencial")
        fig.update_layout(height=390, margin=dict(l=10,r=20,t=55,b=10), paper_bgcolor="white", plot_bgcolor="white")
        st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">Perfil medio del universo filtrado</div>', unsafe_allow_html=True)
radar_cols = ["Tecnología","Catalizadores","Caja","Mercado","Validación","Momentum"]
available = [c for c in radar_cols if c in filtered.columns]
if available and not filtered.empty:
    radar = filtered[available].mean().reset_index(); radar.columns = ["Criterio","Valor"]
    fig = px.line_polar(radar, r="Valor", theta="Criterio", line_close=True, range_r=[0,100], title="Radar medio del modelo")
    fig.update_traces(fill="toself")
    fig.update_layout(height=430, margin=dict(l=10,r=10,t=55,b=10), paper_bgcolor="white")
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">Tabla principal del screener</div>', unsafe_allow_html=True)
show_cols = ["Ticker","Empresa","Sector","Proyecto I+D","Fase","Score","Clasificación","Caja / Runway","Riesgo Dilución","Catalizador próximo","Validación externa","Riesgo principal"]
show_cols = [c for c in show_cols if c in filtered.columns]
table_df = filtered[show_cols].copy()
if "Score" in table_df.columns:
    st.dataframe(table_df, use_container_width=True, hide_index=True, column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")})
else:
    st.dataframe(table_df, use_container_width=True, hide_index=True)

st.markdown('<div class="section-title">Alertas de seguimiento</div>', unsafe_allow_html=True)
alerts = []
for _, row in filtered.iterrows():
    ticker, empresa = row.get("Ticker",""), row.get("Empresa","")
    if "Caja" in row and pd.notna(row["Caja"]) and row["Caja"] < 60:
        alerts.append({"Ticker":ticker,"Empresa":empresa,"Alerta":"Caja / runway débil","Prioridad":"Alta","Acción":"Revisar posible dilución, deuda convertible o necesidad de financiación."})
    if "Control Dilución" in row and pd.notna(row["Control Dilución"]) and row["Control Dilución"] < 60:
        alerts.append({"Ticker":ticker,"Empresa":empresa,"Alerta":"Riesgo de dilución","Prioridad":"Alta","Acción":"Revisar ATM, warrants, ampliaciones o reverse split."})
    if "Catalizadores" in row and pd.notna(row["Catalizadores"]) and row["Catalizadores"] >= 80:
        alerts.append({"Ticker":ticker,"Empresa":empresa,"Alerta":"Catalizador relevante","Prioridad":"Media/Alta","Acción":"Vigilar datos clínicos, FDA/EMA, contratos o hitos comerciales."})
alerts_df = pd.DataFrame(alerts)
if not alerts_df.empty:
    st.dataframe(alerts_df, use_container_width=True, hide_index=True)
else:
    st.success("No se han detectado alertas con los filtros actuales.")

st.markdown('<div class="footer-note">Este dashboard es una herramienta de análisis cuantitativo y cualitativo. No constituye asesoramiento financiero ni recomendación de inversión.</div>', unsafe_allow_html=True)
