import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import re
import json
from datetime import date, timedelta

from google_auth_oauthlib.flow import Flow
from google.oauth2 import credentials as google_oauth_creds
from googleapiclient.discovery import build


# ==========================
# 1) CONFIGURACIÓN GENERAL
# ==========================
SCOPES = ["https://www.googleapis.com/auth/webmasters.readonly"]

# Cargamos desde secrets el JSON de credenciales de tipo "web application"
client_secret_json = st.secrets["GCP"]["CLIENT_SECRET_JSON"]
client_config = json.loads(client_secret_json)["web"]

# Ajusta con la URL real de tu aplicación (la misma que diste en Google Cloud Console)
REDIRECT_URI = "https://gsc-bulk-analysis.streamlit.app"


def get_authorization_url():
    """
    Construye la URL a la que el usuario debe ir para loguearse con Google.
    Devuelve también un 'state' que usaremos para prevenir ataques CSRF.
    """
    flow = Flow.from_client_config(
        {"web": client_config},
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    # Guardar en session_state para usarlo tras el redirect
    st.session_state["oauth_flow"] = flow
    st.session_state["oauth_state"] = state
    return authorization_url


def exchange_code_for_credentials(code, state):
    """
    Intercambia el 'code' que Google devuelve tras el login por credenciales.
    """
    flow = st.session_state["oauth_flow"]
    flow.fetch_token(code=code)
    creds = flow.credentials
    return creds


def build_webmasters_service(creds: google_oauth_creds.Credentials):
    """
    Construye el cliente de la Search Console API con las credenciales dadas.
    """
    return build('webmasters', 'v3', credentials=creds)


# ==========================
# 2) FUNCIONES PARA GRÁFICAS
# ==========================

def show_plot_all(resultados: pd.DataFrame):
    """
    Genera y muestra en Streamlit la gráfica "general" con todas las URLs agregadas,
    incluyendo el overlay con 'google_updates.csv'.
    """
    df_google = pd.read_csv('google_updates.csv')
    df_google['Date_Released'] = pd.to_datetime(df_google['Date_Released'])
    df_google['Date_Completed'] = pd.to_datetime(df_google['Date_Completed'])
    df_google['End_Date'] = df_google['Date_Completed']  # para evitar confusiones

    # Agregamos clicks por fecha
    df_aggregated = resultados.groupby('date')['clicks'].sum().reset_index()
    total_clicks = df_aggregated['clicks'].sum()

    # Tasa diaria (opcional)
    df_aggregated['daily_click_rate'] = df_aggregated['clicks'] / (df_aggregated['date'].diff().dt.days + 1)
    average_daily_clicks = df_aggregated['daily_click_rate'].mean()

    fig_big = make_subplots(specs=[[{"secondary_y": True}]])
    # Línea principal de clicks
    fig_big.add_trace(
        go.Scatter(
            x=df_aggregated['date'],
            y=df_aggregated['clicks'],
            mode='lines',
            name='Clicks'
        ),
        secondary_y=False
    )

    # Añadir intervalos de "updates" de Google
    max_clicks = df_aggregated['clicks'].max() if len(df_aggregated) else 0

    for _, row in df_google.iterrows():
        date_released = row['Date_Released']
        end_date = row['End_Date']
        value = row['Name']

        fig_big.add_shape(
            type="line",
            x0=date_released,
            y0=0,
            x1=date_released,
            y1=max_clicks,
            line=dict(dash="dash", color="red"),
            secondary_y=False,
        )
        fig_big.add_shape(
            type="line",
            x0=end_date,
            y0=0,
            x1=end_date,
            y1=max_clicks,
            line=dict(dash="dash", color="red"),
            secondary_y=False,
        )
        width = end_date - date_released
        fig_big.add_shape(
            type="rect",
            x0=date_released,
            y0=0,
            x1=end_date,
            y1=max_clicks,
            fillcolor="red",
            opacity=0.3,
            line=dict(width=0),
            secondary_y=False,
        )
        # Texto/tooltip
        fig_big.add_trace(go.Scatter(
            x=[date_released + width/2],
            y=[max_clicks],
            text=[value],
            mode="text",
            showlegend=False
        ))

    fig_big.update_layout(
        title=f'Line Plot de Clicks por Día.<br>Total Clicks: {total_clicks:.0f}.<br>'
              f'Daily clicks AVG: {average_daily_clicks:.2f}',
        xaxis_title='Fecha',
        yaxis_title='Suma Total de Clicks',
        width=1200,
        height=600,
    )

    st.plotly_chart(fig_big)


def show_plot(df_aggregated: pd.DataFrame, regex_value: str, window: int, rplog: pd.DataFrame):
    """
    Genera y muestra en Streamlit el gráfico individual de una URL (o grupo de URLs),
    más las líneas verticales de 'repost_log' y overlay con 'google_updates.csv'.
    """
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

    # Línea de tendencia (rolling)
    fig.add_trace(go.Scatter(
        x=df_aggregated['date'],
        y=df_aggregated['clicks'].rolling(window).mean(),
        mode='lines',
        name=f'Trend last {window} days'
    ))

    # Añadir líneas verticales por rplog
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

    # Añadir intervalos de actualizaciones Google
    for _, row in df_google.iterrows():
        date_released = row['Date_Released']
        end_date = row['End_Date']
        value = row['Name']
        width = end_date - date_released

        fig.add_shape(
            type="line",
            x0=date_released,
            y0=0,
            x1=date_released,
            y1=max_clicks,
            line=dict(color="red", dash="dash"),
        )
        fig.add_shape(
            type="line",
            x0=end_date,
            y0=0,
            x1=end_date,
            y1=max_clicks,
            line=dict(color="red", dash="dash"),
        )
        fig.add_shape(
            type="rect",
            x0=date_released,
            y0=0,
            x1=end_date,
            y1=max_clicks,
            fillcolor="red",
            opacity=0.3,
            line=dict(width=0),
        )
        fig.add_trace(go.Scatter(
            x=[date_released + width / 2],
            y=[max_clicks],
            text=[value],
            mode="text",
            showlegend=False
        ))

    # Cálculo de media diaria
    df_aggregated['daily_click_rate'] = (
        df_aggregated['clicks'] / (df_aggregated['date'].diff().dt.days + 1)
    )
    average_daily_clicks = df_aggregated['daily_click_rate'].mean()

    fig.update_layout(
        title=f'URL - {regex_value}.<br>Total Clicks: {total_clicks}.<br>'
              f'Daily clicks AVG: {average_daily_clicks:.2f}',
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
    """
    Esta función se ejecuta solo cuando el usuario ya está autenticado en Google.
    """
    st.title("Análisis de Clicks por Día (Google Search Console)")

    # Cargamos repost_log
    rplog = pd.read_csv("repost_log.csv")
    rplog = rplog[rplog["DS_POSTING_TYPE"] == "Repost"].drop(columns=[
        'ID_WPS_ARTICLE', 'ID_WPS_PAGE', 'AUTHOR',
        'ID_CALENDAR_DAY_POSTING', 'DT_DATE_POSTING_NEXT',
        'ID_CALENDAR_DAY_POSTING_NEXT'
    ], errors='ignore')

    # Ajustar formato de fechas en rplog
    # Ajusta format='%B %d, %Y' si tu CSV viene con mes en texto
    rplog['DT_DATE_POSTING'] = pd.to_datetime(rplog['DT_DATE_POSTING'], errors='coerce')
    rplog['DT_DATE_POSTING'] = rplog['DT_DATE_POSTING'].dt.strftime('%Y-%m-%d')  # re-stringify en YYYY-mm-dd

    st.write("Ingresa las URLs separadas por espacio:")
    url_input = st.text_area("", value="", key="urls_input")
    url_list = url_input.split()

    # Pide la URL del sitio web (property) en Search Console
    website = st.text_input(
        "Inserta la URL del sitio web (formato: https://tusitio.com/)",
        value=""
    )

    # Parámetro para ventana de rolling average
    window = st.number_input(
        "Window for moving avg:",
        min_value=1,
        value=28
    )

    # Fechas por defecto
    default_end = date.today() - timedelta(days=3)
    default_start = default_end - timedelta(days=365)

    # Inputs de fecha
    start_date = st.date_input('Fecha de inicio', default_start)
    end_date = st.date_input('Fecha final', default_end)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Filtrar rplog según rango
    rplog = rplog[
        (rplog['DT_DATE_POSTING'] >= start_date_str) &
        (rplog['DT_DATE_POSTING'] <= end_date_str)
    ]

    # Expresión regular para extraer (por ejemplo) "/algo/" de la URL
    pattern = r"https?://[^/]+/([^/]+)/"
    rplog['URL_SHRT'] = rplog['CD_WPS_URL'].apply(
        lambda url: "/" + re.search(pattern, url).group(1) + "/" if re.search(pattern, url) else None
    )

    if not website:
        st.warning("Por favor, ingresa la URL del sitio web para Search Console.")
        st.stop()

    # Extraer partes de las URLs que el usuario ha ingresado
    extracted_parts = []
    for url in url_list:
        match = re.search(pattern, url)
        if match:
            extracted_parts.append("/" + match.group(1) + "/")
    regex = "|".join(extracted_parts)

    if not extracted_parts:
        st.warning("No se encontraron patrones en las URLs ingresadas.")
        st.stop()

    # Construye el servicio de Search Console con las credenciales del usuario
    creds = st.session_state["google_creds"]
    webmasters_service = build_webmasters_service(creds)

    # Dividir en trozos si la regex es muy larga (como hacías antes).
    regex_list = []
    if len(regex) > 8192:
        # ...
        # (Aquí tendrías tu lógica de trocear la string en 3 partes.)
        pass
    elif len(regex) > 4096:
        # ...
        # (Tu lógica de trocear en 2 partes.)
        pass
    else:
        regex_list.append(regex)

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
            siteUrl=website,
            body=body
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

    # MOSTRAR GRÁFICO GENERAL
    show_plot_all(resultados)

    # MOSTRAR GRÁFICOS INDIVIDUALES
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
        response = webmasters_service.searchanalytics().query(siteUrl=website, body=body).execute()
        rows = response.get('rows', [])

        if not rows:
            st.warning(f"No se encontraron datos para la URL (o subregex): {regex_value}")
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
    Entry point de la app. Controla la lógica de autenticación:
     - Si el usuario ya está autenticado -> run_analysis_app()
     - Si no, le muestra el botón/link para hacer login
     - Si Google redirige con ?code=... -> canjea el token y almacena en session_state
    """
    st.set_page_config(page_title="Análisis Search Console", layout="wide")

    # Leer parámetros de la URL para ver si Google nos ha devuelto 'code'
    query_params = st.query_params

    # 1) Si ya tenemos credenciales en session_state, vamos directos a la app
    if "google_creds" in st.session_state:
        try:
            # Verificar si las credenciales son válidas, etc.
            run_analysis_app()
            if st.button("Cerrar sesión"):
                del st.session_state["google_creds"]
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Error usando credenciales: {e}")
            if st.button("Forzar Logout"):
                del st.session_state["google_creds"]
                st.experimental_rerun()

    # 2) Si no hay credenciales todavía
    else:
        # Ver si Google nos devolvió ?code=...&state=...
        if "code" in query_params and "state" in query_params:
            code = query_params["code"][0]
            state = query_params["state"][0]

            if state != st.session_state.get("oauth_state"):
                st.error("State inválido o expirado. Intenta de nuevo.")
            else:
                # Canjear el code por credenciales
                try:
                    creds = exchange_code_for_credentials(code, state)
                    st.session_state["google_creds"] = creds
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Error al intercambiar code: {e}")

            else:
                st.title("Login con Google para Search Console")
                auth_url = get_authorization_url()
            
                # Enlace HTML con target="_self" para que abra en la MISMA pestaña
                st.markdown(
                    f"""
                    <a href="{auth_url}" target="_self"
                       style="font-size:18px; font-weight:bold;
                              text-decoration:none; background-color:#4CAF50;
                              color:white; padding:10px; border-radius:5px;">
                       Iniciar sesión con Google
                    </a>
                    """,
                    unsafe_allow_html=True
                )
            
                # Detenemos aquí para no seguir renderizando nada adicional
                st.stop()



if __name__ == "__main__":
    main()
