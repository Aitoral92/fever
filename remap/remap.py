from io import StringIO
import streamlit as st
from bs4 import BeautifulSoup, SoupStrainer
from polyfuzz import PolyFuzz
import concurrent.futures
import csv
import pandas as pd
import requests

def get_content(url_argument):
    page_source = requests.get(url_argument, timeout=5).text
    strainer = SoupStrainer('p')
    soup = BeautifulSoup(page_source, 'html.parser', parse_only=strainer)
    paragraph_list = [element.text for element in soup.find_all(strainer)]
    content = " ".join(paragraph_list)
    return content

def get_input_urls_from():
    st.write(f"Ingrese las URLs para redirigir:")
    clipboard_content_from = st.text_area(f"Pegue el contenido aquí (from):")
    elements_from = clipboard_content_from.split()
    return elements_from

def get_input_urls_to():
    st.write(f"Ingrese las URLs para redirigir:")
    clipboard_content_to = st.text_area(f"Pegue el contenido aquí (to):")
    elements_to = clipboard_content_to.split()
    return elements_to 

def main():
    st.title("Análisis de Contenido Web")

    url_list_a = get_input_urls_from()
    url_list_b = get_input_urls_to()

    if (not url_list_a) or (not url_list_b):
        st.info('The calculations will run, once you entered two inputs.')
        st.stop()

    with st.spinner('Obteniendo contenido de las URLs...'):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            content_list_a = list(executor.map(get_content, url_list_a))
            content_list_b = list(executor.map(get_content, url_list_b))

    content_dictionary = dict(zip(url_list_b, content_list_b))


    model = PolyFuzz("TF-IDF")
    model.match(content_list_a, content_list_b)
    data = model.get_matches()

    def get_key(argument):
        for key, value in content_dictionary.items():
            if argument == value:
                return key
        return key

    with concurrent.futures.ThreadPoolExecutor() as executor:
        result = list(executor.map(get_key, data["To"]))

    to_zip = list(zip(url_list_a, result, data["Similarity"]))
    df = pd.DataFrame(to_zip)
    df.columns = ["From URL", "To URL", "% Identical"]

    st.subheader("Resultados")
    st.write(df)

    # Guardar los resultados en un archivo CSV
    output_filename = st.text_input("Ingrese el nombre del archivo CSV para guardar los resultados:", "resultados")
    if st.button("Descargar CSV"):
        # Crear un archivo CSV en memoria utilizando StringIO
        output_csv = StringIO()
        writer = csv.writer(output_csv)
        columns = ["From URL", "To URL", "% Identical"]
        writer.writerow(columns)
        for row in to_zip:
            writer.writerow(row)
        
        # Descargar el archivo CSV como un archivo descargable en el navegador del usuario
        st.download_button(
            label="Haga clic aquí para descargar",
            data=output_csv.getvalue(),
            file_name=output_filename + ".csv",
            mime="text/csv"
        )
        st.success(f"Los resultados se han descargado como '{output_filename}.csv' satisfactoriamente.")

        #esto no es más que una prueba

if __name__ == "__main__":
    main()