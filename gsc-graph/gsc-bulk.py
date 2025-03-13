import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import re
import json
from datetime import date, timedelta

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


# ==========================
# 1) CONFIGURACIÓN GENERAL
# ==========================
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

client_secret_json = st.secrets["GCP"]["CLIENT_SECRET_JSON"]
client_config_web = json.loads(client_secret_json)["web"]

# Este método "copy & paste" requiere credenciales de tipo "installed",
# así que convertimos la sección "web" a una "installed" adaptada.
# (Lo esencial es usar un redirect_uri "urn:ietf:wg:oauth:2.0:oob" o similar)
manual_installed_config = {
    "installed": {
        "client_id": client_config_web["client_id"],
        "client_secret": client_config_web["client_secret"],
        "auth_uri": client_config_web["auth_uri"],
        "token_uri": client_config_web["token_uri"],
        "redirect_uris": [
            "urn:ietf:wg:oauth:2.0:oob", 
            "http://localhost"
        ]
    }
}

def build_webmasters_service(creds: Credentials):
    """Construye el cliente de la Search Console API con las credenciales dadas."""
    return build('webmasters', 'v3', credentials=creds)


# ==========================
# 2) FUNCIONES PARA GRÁFICAS
# ==========================

def show_plot_all(resultados: pd.DataFrame):
    """Genera y muestra en Streamlit la gráfica 'general' con todas las URLs agregadas,
       incluyendo el overlay con 'google_updates.csv'.
    """
    df_google = pd.read_csv('google_updates.csv')
    df_google['Date_Released'] = pd.to_datetime(df_google['Date_Released'])
    df_google['Date_Completed'] = pd.to_datetime(df_google['Date_Completed'])
    df_google['End_Date'] = df_google['Date_Completed']

    df_aggregated = resultados.groupby('date')['clicks'].sum().reset_index()
    total_clicks = df_aggregated['clicks'].sum()
    df_aggregated['daily_click_rate'] = df_aggregated['clicks'] / (df_aggregated['date'].diff().dt.days + 1)
    average_daily_clicks = df_aggregated['daily_click_rate'].mean()

    fig_big = make_subplots(specs=[[{"secondary_y": True}]])
    fig_big.add_trace(
        go.Scatter(
            x=df_aggregated['date'],
            y=df_aggregated['clicks'],
            mode='lines',
            name='Clicks'
        ),
        secondary_y=False
    )

    max_clicks = df_aggregated['clicks'].max() if len(df_aggregated) else 0
    for _, row in df_google.iterrows():
        date_released = row['Date_Released']
        end_date = row['End_Date']
        value = row['Name']
        fig_big.add_shape(
            type="line",
            x0=date_released, y0=0,
            x1=date_released, y1=max_clicks,
            line=dict(dash="dash", color="red"),
            secondary_y=False
        )
        fig_big.add_shape(
            type="line",
            x0=end_date, y0=0,
            x1=end_date, y1=max_clicks,
            line=dict(dash="dash", color="red"),
            secondary_y=False
        )
        width = end_date - date_released
        fig_big.add_shape(
            type="rect",
            x0=date_released, y0=0,
            x1=end_date, y1=max_clicks,
            fillcolor="red", opacity=0.3,
            line=dict(width=0),
            secondary_y=False
        )
        fig_big.add_trace(go.Scatter(
            x=[date_released + width/2],
            y=[max_clicks],
            text=[value],
            mode="text",
            showlegend=False
        ))

    fig_big.update_layout(
        title=f'Line Plot de Clicks por Día.<br>Total Clicks: {total_clicks:.0f}.<br>Daily clicks AVG: {average_daily_clicks:.2f}',
        xaxis_title='Fecha',
        yaxis_title='Suma Total de Clicks',
        width=1200,
        height=600,
    )
    st.plotly_chart(fig_big)


def show_plot(df_aggregated: pd.DataFrame, regex_value: str, window: int, rplog: pd.DataFrame):
    """Genera y muestra en Streamlit el gráfico individual de una URL (o grupo de URLs)."""
    df_google = pd.read_csv('google_updates.csv')
    df_google['Date_Released'] = pd.to_datetime(df_google['Date_Released'])
    df_google['Date_Completed'] = pd.to_datetime(df_google['Date_Completed'])
    df_google['End_Date'] = df_google['Date_Completed']

    total_clicks = df_aggregated['clicks'].sum()
    max_clicks = df_aggregated['clicks'].max() if len(df_aggregated) else 0

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_aggregated['date'],
        y=df_aggregated['clicks'],
        mode='lines',
        name=f'Clicks {regex_value}',
        hovertemplate='%{x|%Y-%m-%d} <br>Total de Clicks: %{y}'
    ))
    fig.add_trace(go.Scatter(
        x=df_aggregated['date'],
        y=df_aggregated['clicks'].rolling(window).mean(),
        mode='lines',
        name=f'Trend last {window} days'
    ))

    for _, row in rplog.iterrows():
        if row['URL_SHRT'] == regex_value:
            post_date = row['DT_DATE_POSTING']
            fig.add_trace(go.Scatter(
                x=[post_date, post_date],
                y=[0, max_clicks],
                mode="lines",
                line=dict(color="black"),
                hovertext=f"Repost {post_date}",
                name="Repost"
            ))

    for _, row in df_google.iterrows():
        date_released = row['Date_Released']
        end_date = row['End_Date']
        value = row['Name']
        width = end_date - date_released

        fig.add_shape(
            type="line",
            x0=date_released, y0=0,
            x1=date_released, y1=max_clicks,
            line=dict(color="red", dash="dash"),
        )
        fig.add_shape(
            type="line",
            x0=end_date, y0=0,
            x1=end_date, y1=max_clicks,
            line=dict(color="red", dash="dash"),
        )
        fig.add_shape(
            type="rect",
            x0=date_released, y0=0,
            x1=end_date, y1=max_clicks,
            fillcolor="red", opacity=0.3,
            line=dict(width=0),
        )
        fig.add_trace(go.Scatter(
            x=[date_released + width / 2],
            y=[max_clicks],
            text=[value],
            mode="text",
            showlegend=False
        ))

    df_aggregated['daily_click_rate'] = df_aggregated['clicks'] / (df_aggregated['date'].diff().dt.days + 1)
    average_daily_clicks = df_aggregated['daily_click_rate'].mean()

    fig.update_layout(
        title=f'URL - {regex_value}.<br>Total Clicks: {total_clicks}.<br>Daily clicks AVG: {average_daily_clicks:.2f}',
        xaxis_title='Fecha',
        yaxis_title='Suma Total de Clicks',
        width=800,
        height=400
    )
    st.plotly_chart(fig)


# ==========================
# 3) LÓGICA PRINCIPAL DE LA APP
# ==========================

def run_analysis_app():
    """Se ejecuta cuando ya tenemos credenciales."""
    st.title("Análisis de Clicks por Día (Google Search Console)")

    # Lee repost_log
    rplog = pd.read_csv("repost_log.csv")
    rplog = rplog[rplog["DS_POSTING_TYPE"] == "Repost"].drop(columns=[
        'ID_WPS_ARTICLE', 'ID_WPS_PAGE', 'AUTHOR',
        'ID_CALENDAR_DAY_POSTING', 'DT_DATE_POSTING_NEXT',
        'ID_CALENDAR_DAY_POSTING_NEXT'
    ], errors='ignore')

    rplog['DT_DATE_POSTING'] = pd.to_datetime(rplog['DT_DATE_POSTING'], errors='coerce')
    rplog['DT_DATE_POSTING'] = rplog['DT_DATE_POSTING'].dt.strftime('%Y-%m-%d')

    st.write("Ingresa las URLs separadas por espacio:")
    url_input = st.text_area("", value="", key="urls_input")
    url_list = url_input.split()

    website = st.text_input("Inserta la URL del sitio web (formato: https://tusitio.com/)", value="")
    window = st.number_input("Window for moving avg:", min_value=1, value=28)

    default_end = date.today() - timedelta(days=3)
    default_start = default_end - timedelta(days=365)
    start_date = st.date_input('Fecha de inicio', default_start)
    end_date = st.date_input('Fecha final', default_end)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    rplog = rplog[
        (rplog['DT_DATE_POSTING'] >= start_date_str) &
        (rplog['DT_DATE_POSTING'] <= end_date_str)
    ]

    pattern = r"https?://[^/]+/([^/]+)/"
    rplog['URL_SHRT'] = rplog['CD_WPS_URL'].apply(
        lambda url: "/" + re.search(pattern, url).group(1) + "/" if re.search(pattern, url) else None
    )

    if not website:
        st.warning("Por favor, ingresa la URL del sitio web para Search Console.")
        st.stop()

    # Construimos el servicio
    creds = st.session_state["google_creds"]
    webmasters_service = build_webmasters_service(creds)

    # Extraer partes de la URL
    extracted_parts = []
    for url in url_list:
        match = re.search(pattern, url)
        if match:
            extracted_parts.append("/" + match.group(1) + "/")
    if not extracted_parts:
        st.warning("No se encontraron patrones en las URLs ingresadas.")
        st.stop()

    regex = "|".join(extracted_parts)
    regex_list = [regex]  # Simplificado, omite la lógica de trocear

    result_dfs = []
    for sub_regex in regex_list:
        body = {
            'startDate': start_date_str,
            'endDate': end_date_str,
            'dimensions': ["date", "page"],
            "dimensionFilterGroups": [
                {
                    "groupType": "and",
                    "filters": [
                        {
                            "dimension": "page",
                            "operator": "includingRegex",
                            "expression": sub_regex
                        }
                    ]
                }
            ],
            'rowLimit': 25000,
            'startRow': 0
        }
        response = webmasters_service.searchanalytics().query(
            siteUrl=website, body=body
        ).execute()

        rows = response.get('rows', [])
        if not rows:
            st.warning(f"No se encontraron datos para sub-regex: {sub_regex}")
            continue

        df_data = []
        for r in rows:
            date_x = r['keys'][0]
            page_x = r['keys'][1]
            df_data.append({
                'date': date_x,
                'page': page_x,
                'clicks': r['clicks'],
                'impressions': r['impressions'],
                'ctr': r['ctr'],
                'position': r['position']
            })
        sub_df = pd.DataFrame(df_data)
        result_dfs.append(sub_df)

    if not result_dfs:
        st.warning("No se encontraron datos con ninguna de las expresiones regulares.")
        return

    resultados = pd.concat(result_dfs, ignore_index=True)
    resultados['date'] = pd.to_datetime(resultados['date'])
    resultados.sort_values('date', inplace=True)

    # Gráfico global
    show_plot_all(resultados)

    # Gráficos individuales
    for regex_value in extracted_parts:
        body = {
            'startDate': start_date_str,
            'endDate': end_date_str,
            'dimensions': ["date", "page"],
            "dimensionFilterGroups": [
                {
                    "filters": [
                        {
                            "dimension": "page",
                            "operator": "includingRegex",
                            "expression": regex_value
                        }
                    ]
                }
            ],
            'rowLimit': 25000,
            'startRow': 0
        }
        response = webmasters_service.searchanalytics().query(
            siteUrl=website, body=body
        ).execute()
        rows = response.get('rows', [])
        if not rows:
            st.warning(f"No se encontraron datos para la URL (subregex): {regex_value}")
            continue

        df_data = []
        for r in rows:
            date_x = r['keys'][0]
            page_x = r['keys'][1]
            df_data.append({
                'date': date_x,
                'page': page_x,
                'clicks': r['clicks'],
                'impressions': r['impressions'],
                'ctr': r['ctr'],
                'position': r['position']
            })
        df = pd.DataFrame(df_data)
        df['date'] = pd.to_datetime(df['date'])
        df_aggregated = df.groupby('date')['clicks'].sum().reset_index()

        show_plot(df_aggregated, regex_value, window, rplog)


def main():
    """
    Usamos el "copy/paste" method:
      1) Generamos la URL de Auth con Flow (tipo 'installed').
      2) Usuario la abre, copia el 'code'.
      3) Usuario pega el 'code' y canjeamos el token.
      4) Una vez tenemos 'google_creds', llamamos a run_analysis_app().
    """
    st.set_page_config(page_title="Análisis Search Console - Copy/Paste OAuth")

    if "google_creds" in st.session_state:
        # Ya tenemos credenciales => ejecutamos la app
        run_analysis_app()
        if st.button("Cerrar sesión"):
            del st.session_state["google_creds"]
            st.experimental_rerun()

    else:
        st.title("Login manual con Google (Copy/Paste de code)")

        # 1) Botón para generar la URL de autorización
        if "manual_flow" not in st.session_state:
            # Creación del Flow "instalado"
            flow = Flow.from_client_config(
                manual_installed_config,
                scopes=SCOPES
            )
            st.session_state["manual_flow"] = flow

        # Creamos un botón para generar el auth_url cada vez que se desee
        if st.button("Generar URL de autenticación"):
            flow = st.session_state["manual_flow"]
            # prompt="consent" para forzar mostrar la pantalla de consentimiento
            auth_url, _ = flow.authorization_url(prompt='consent')
            st.session_state["manual_auth_url"] = auth_url

        # 2) Mostramos la URL para que el usuario la copie
        if "manual_auth_url" in st.session_state:
            st.write("Abre este enlace en tu navegador, autoriza, y Google te mostrará un 'code':")
            st.write(st.session_state["manual_auth_url"])

            st.write("Copia ese 'code' de Google y pégalo aquí:")
            code_input = st.text_input("Introduce aquí el 'code':", value="")
            if st.button("Intercambiar code por credenciales"):
                # 3) Canjear el code
                flow = st.session_state["manual_flow"]
                try:
                    flow.fetch_token(code=code_input)
                    creds = flow.credentials
                    st.session_state["google_creds"] = creds
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error al canjear el code: {e}")


if __name__ == "__main__":
    main()
