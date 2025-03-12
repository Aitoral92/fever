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

client_secret_json = st.secrets["GCP"]["CLIENT_SECRET_JSON"]
client_config = json.loads(client_secret_json)["web"]

# Ajusta la URL real de tu aplicación:
REDIRECT_URI = "https://gsc-bulk-analysis.streamlit.app"


def get_authorization_url():
    """
    Construye la URL de autorización de OAuth con Google.
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
    Gráfica general con google_updates.csv (superposición de actualizaciones).
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
        fig_big.add_trace(go.Scatter(
            x=[date_released + width / 2],
            y=[max_clicks],
            text=[value],
            mode="text",
            showlegend=False
        ))

    fig_big.update_layout(
        title=f'Line Plot de Clicks por Día.<br>Total Clicks: {total_clicks:.0f} '
              f' - Daily clicks AVG: {average_daily_clicks:.2f}',
        xaxis_title='Fecha',
        yaxis_title='Suma Total de Clicks',
        width=1200,
        height=600
    )
    st.plotly_chart(fig_big)


def show_plot(df_aggregated: pd.DataFrame, regex_value: str, window: int, rplog: pd.DataFrame):
    """
    Gráfica individual para cada patrón (regex_value). Con superposición de google_updates y repost_log.
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

    # Rolling window
    fig.add_trace(go.Scatter(
        x=df_aggregated['date'],
        y=df_aggregated['clicks'].rolling(window).mean(),
        mode='lines',
        name=f'Trend last {window} days'
    ))

    # rplog
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

    # google updates
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
        
