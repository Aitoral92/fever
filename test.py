import streamlit as st
import requests

st.title("Test de acceso a Google desde el servidor")

try:
    resp = requests.get("https://accounts.google.com", timeout=10)
    st.write(f"Status code: {resp.status_code}")
    st.write("Conexión exitosa a https://accounts.google.com")
except Exception as e:
    st.error(f"ERROR al conectar: {e}")
