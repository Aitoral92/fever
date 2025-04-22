import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter
from urllib.parse import urlparse
from urllib.request import urlopen as uReq
import streamlit as st
import json
import requests_html
from requests_html import AsyncHTMLSession
import os

# def count_hyphens_and_digits_in_url(url):
#     hyphen_count = url.count("-")
#     has_digit = any(char.isdigit() for char in url)
#     url_len = len(url)
#     return hyphen_count, has_digit, url_len

def h2_counter(soup):
    all_content = soup.find("section", class_="article__body col-md-8")

    h2_count = 0
    # h2_list = []
    for h2 in all_content.find_all('h2'):
        h2_count +=1

    return h2_count

def get_seo_title_length(soup):
    seot = soup.find('title')
    lenseot = len(seot.text)
    return seot.text, lenseot

def get_meta_description_length(soup):
    metad = soup.find("meta", attrs={"name":"description"})
    len_metad = len(metad["content"]) if metad else 0
    return metad["content"] if metad else "No meta description given", len_metad

def get_secondary_title_length(soup):
    secondary = soup.find("p", class_="single__subtitle")
    len_secondary = len(secondary.text) if secondary else 0
    return secondary.text if secondary else "No secondary title given", len_secondary

def kw_in_first_par(soup):
    all_content = soup.find("section", class_="article__body col-md-8")

    p = all_content.find('p')
    p_cln = p.get_text()

    # Imprime el texto completo
    # print(p_cln)

    # Imprime el texto completo
    return p_cln

def kw_density (soup, stopwords):
    # kw_cln = ' '.join(word for word in kw.split() if word.lower() not in stopwords)
    all_content = soup.find("section", class_="article__body col-md-8")
    text_elements = all_content.find_all(['p', 'figcaption'])
    script = soup.find('script', type='application/ld+json')
    data = script.string
    # Analizar el JSON
    json_data = json.loads(data)
    # Extraer word count
    word_count = json_data['@graph'][0]['wordCount']
    # Extraer texto
    text = json_data['@graph'][0]['articleBody']
    # words_in_keyword = kw_cln.split()
    # find = kw_cln.lower()
    blacklist = [
    '[document]',
    'noscript',
    'header',
    'html',
    'meta',
    'head', 
    'input',
    'script',
    'style',
    'input'
]
    cleaned_text = ''
    for element in text_elements:
        if element.parent.name not in blacklist:
            # Eliminar texto dentro de las etiquetas <figcaption>
            if element.name == 'figcaption':
                continue
            cleaned_text += element.get_text().replace("\n", "").replace("\t", "") + ' '
    # Eliminar stopwords
    cleaned_text = ' '.join(word for word in cleaned_text.split() if word.lower() not in stopwords)
    word_list = cleaned_text.lower()

    return word_list, word_count

    # find = kw_cln.lower()
    # words_in_keyword = kw_cln.split()
    # if find in word_list:
    #     kw_count = word_list.count(find)
    #     words_in_keyword = kw_cln.split()
    #     # a = word_count
    #     kw_len = len(words_in_keyword)
        # b = kw_len
        # while True:
        #     try:
        #         c = round(a//b,4)
        #         d = round(kw_count / c,4)
        #         e = round(d,4)
        #         f = e * 100
        #         kw_den = str(round(f,3))
        #         # print('\nThe keyword appears ' + str(density) + ' times in the page.')
        #         break
        #     except ZeroDivisionError:
        #         print('\nDivision by Zero Error, Please input a valid keyword')
        #         break
    # return kw_count, word_count, kw_len

def get_internal_links_count(soup, base_url):
    soup_copy = BeautifulSoup(str(soup), "html.parser")
    all_content = soup_copy.find("section", class_="article__body col-md-8")
    art_count = 0
    art_list = []

    base_domain = urlparse(base_url).netloc

    for a in all_content.find_all('a', href=True):
        link = a['href']
        parsed_link = urlparse(link)
        if parsed_link.netloc == base_domain and "/wp-content/" not in parsed_link.path:
            # Check if the URL already exists in art_list
            url_exists = False
            for existing_url in art_list:
                if existing_url == link:
                    url_exists = True
                    break

            if not url_exists:
                art_count += 1
                art_list.append(link)

            # art_count += 1
            # art_list.add(link)
    
    # art_list = list(art_list)  # Convert to set and back to list to remove duplicates
    art_ucount = len(art_list)
    return art_ucount, art_count, art_list

def feverup_plans_check (soup, art_count):
    soup_copy_fever = BeautifulSoup(str(soup), "html.parser")
    all_content = soup_copy_fever.find("section", class_="article__body col-md-8")

    # Encuentra el div con class 'recommender-container' si existe
    recommender_div = all_content.find("div", class_="recommender-container")

    # Lista para almacenar los enlaces a excluir si existe el div
    exclude_links = []

    # Si el div existe, almacena los enlaces dentro de él en la lista de exclusión
    if recommender_div:
        for a in recommender_div.find_all('a', href=True):
            link = a['href'].strip()  # Eliminar espacios en blanco
            exclude_links.append(link)

    # # Contadores para artículos del dominio base y enlaces de feverup.com
    # art_count = 0
    # art_list = []

    feverup_links = []  # Lista para almacenar enlaces de feverup.com
    exp_plans = []  # Lista para almacenar enlaces que contienen el mensaje de plan expirado

    # Dominio base del sitio analizado
    # base_domain = urlparse(base_url).netloc

    # Itera sobre todos los enlaces en la sección principal
    for a in all_content.find_all('a', href=True):
        link = a['href']  # Eliminar espacios en blanco
        
        
        parsed_link = urlparse(link)
        
        # Excluir enlaces en /wp-content/ o dentro del div recommender-container
        if "/wp-content/" not in parsed_link.path and link not in exclude_links:
        
        # # Contar artículos del dominio base
        # if parsed_link.netloc == base_domain:
        #     if link not in art_list:
        #         art_count += 1
        #         art_list.append(link)
        
        # Almacenar enlaces de feverup.com
            if link.startswith("https://feverup.com/"):
                if link not in feverup_links:
                    feverup_links.append(link)

    # Recorre la lista de enlaces feverup y busca el div de plan expirado
    for feverup_link in feverup_links:
        feverup_page = requests.get(feverup_link)
        feverup_soup = BeautifulSoup(feverup_page.text, "html.parser")
        
        # Busca el div con data-testid="plan-expired-message"
        expired_message_div = feverup_soup.find("div", {"data-testid": "plan-expired-message", "class": "plan-unavailable-message"})
        
        # Si el div existe, añade el enlace a la lista exp_plans
        if expired_message_div:
            # Extraer la URL desde https hasta el primer ?
            clean_url = feverup_link.split('?')[0]
            exp_plans.append(clean_url)

    # Cálculo del porcentaje de enlaces que empiezan con "https://feverup.com/"
    feverup_count = len(feverup_links)
    if art_count > 0:
        feverup_percentage = (feverup_count / art_count) * 100
    else:
        feverup_percentage = 0

    # h2_count = h2_counter(soup)
    # if h2_count:
    #     feverup_percentage = (feverup_count*100)/h2_count
    
    
    h2_count = 0
    # h2_list = []
    for h2 in all_content.find_all('h2'):
        h2_count +=1

    if h2_count:
        feverup_percentage = (feverup_count*100)/h2_count

    feverup_percentage = round(feverup_percentage, 2)
        

    # Muestra la lista de enlaces expirados (si no está vacía)
    # if exp_plans:
    #     print("\nEnlaces con planes expirados encontrados:")
    #     for exp_link in exp_plans:
    #         print(exp_link)

    return feverup_count, feverup_percentage, exp_plans

def check_cta(soup):
    cta_count = 0
    cta_list = []

    try:
        all_content_cta = soup.find_all("div", class_="smn-tracklink-cta")
        if not all_content_cta:
            st.warning("There is no final CTA.", icon="⚠️")
            return 0, []

        all_content_last_cta = all_content_cta[-1]
        for a in all_content_last_cta.find_all('a', href=True):
            cta_count += 1
            cta_list.append(a['href'])

        if cta_count == 0:
            st.warning("Final CTA found but has no valid <a> tags.", icon="⚠️")

    except Exception as e:
        st.warning(f"Unexpected issue while checking CTA: {e}", icon="⚠️")

    return cta_count, cta_list

def get_categories_count(soup):
    all_content = soup.find("div", class_="post-list-view-home__category-wrapper")
    cat_count = 0
    cat_list = []
    for a in all_content.find_all('a', href=True):
        cat_count += 1
        cat_list.append(a['href'])
    cat_ucount = len(Counter(cat_list).keys())
    return cat_ucount, cat_count

def get_featured_image_width(soup):

    # Obtener el ancho de la imagen desde "og:image:width"
    ft_img_width_meta = soup.find("meta", property="og:image:width")
    script = soup.find('script', type='application/ld+json')
    if ft_img_width_meta and 'content' in ft_img_width_meta.attrs:
        og_width = int(ft_img_width_meta['content'])
        if og_width >= 1200:
            return og_width
        else:
            # Extraer el contenido JSON del script
            data = script.string

            # Analizar el JSON
            json_data = json.loads(data)

            # Extraer el valor del "width"
            # width_value = json_data['@graph'][0]['thumbnail']['width']
            # if width_value is not None:
            #     return width_value
            
            width_value = json_data['@graph'][2]['width']
            return width_value

def get_featured_image_alt(soup):
    all_content = soup.find("section", class_="article__body col-md-8")
    alt_text = all_content.find("img", alt=True)
    if alt_text:
        return alt_text["alt"]
    else:
        return None

def get_total_image_count(soup):
    all_content = soup.find("section", class_="article__body col-md-8")

    img_count = 0
    alt_count = 0
    alt_list = []
    ig_count = 0

    # Contar imagenes normales

    for img in all_content.find_all('img', alt=True):
        # Verificar si la etiqueta 'img' tiene la clase "emoji" o está dentro de <noscript></noscript>
        if "emoji" in img.get("class", []) or img.find_parent("noscript"):
            continue  # Ignorar esta etiqueta 'img' y pasar a la siguiente
        img_count += 1
        if len(img["alt"]) > 0:
            alt_count += 1
            alt_list.append(img["alt"])
       
    
    # Contar imagenes embedadas
  
    for img in all_content.find_all('blockquote', class_=True):
        ig_count += 1
    
    total=img_count+ig_count
    
    return img_count, alt_count, alt_list, ig_count, total


def main():
    st.title("SEO Checker")
    url = st.text_input("Paste the URL and press 'Analyze' button:")
    kw = st.text_input("Insert the keyword to check:")

    # stopwords in ES, EN, FR and PT so far.
    stopwords = [
    "a", "actualmente", "adelante", "además", "afirmó", "agregó", "ahora", "ahí", "al", "algo", "alguna", 
    "algunas", "alguno", "algunos", "algún", "alrededor", "ambos", "ampleamos", "ante", "anterior", "antes", 
    "apenas", "aproximadamente", "aquel", "aquellas", "aquellos", "aqui", "aquí", "arriba", "aseguró", "así", 
    "atras", "aunque", "ayer", "añadió", "aún", "bajo", "bastante", "bien", "buen", "buena", "buenas", "bueno", 
    "buenos", "cada", "casi", "cerca", "cierta", "ciertas", "cierto", "ciertos", "cinco", "comentó", "como", 
    "con", "conocer", "conseguimos", "conseguir", "considera", "consideró", "consigo", "consigue", "consiguen", 
    "consigues", "contra", "cosas", "creo", "cual", "cuales", "cualquier", "cuando", "cuanto", "cuatro", 
    "cuenta", "cómo", "da", "dado", "dan", "dar", "de", "debe", "deben", "debido", "decir", "dejó", "del", 
    "demás", "dentro", "desde", "después", "dice", "dicen", "dicho", "dieron", "diferente", "diferentes", 
    "dijeron", "dijo", "dio", "donde", "dos", "durante", "e", "ejemplo", "el", "ella", "ellas", "ello", "ellos", 
    "embargo", "empleais", "emplean", "emplear", "empleas", "empleo", "en", "encima", "encuentra", "entonces", 
    "entre", "era", "erais", "eramos", "eran", "eras", "eres", "es", "esa", "esas", "ese", "eso", "esos", 
    "esta", "estaba", "estabais", "estaban", "estabas", "estad", "estada", "estadas", "estado", "estados", 
    "estais", "estamos", "estan", "estando", "estar", "estaremos", "estará", "estarán", "estarás", "estaré", 
    "estaréis", "estaría", "estaríais", "estaríamos", "estarían", "estarías", "estas", "este", "estemos", 
    "esto", "estos", "estoy", "estuve", "estuviera", "estuvierais", "estuvieran", "estuvieras", "estuvieron", 
    "estuviese", "estuvieseis", "estuviesen", "estuvieses", "estuvimos", "estuviste", "estuvisteis", 
    "estuviéramos", "estuviésemos", "estuvo", "está", "estábamos", "estáis", "están", "estás", "esté", "estéis", 
    "estén", "estés", "ex", "existe", "existen", "explicó", "expresó", "fin", "fue", "fuera", "fuerais", 
    "fueran", "fueras", "fueron", "fuese", "fueseis", "fuesen", "fueses", "fui", "fuimos", "fuiste", 
    "fuisteis", "fuéramos", "fuésemos", "gran", "grandes", "gueno", "ha", "haber", "habida", "habidas", 
    "habido", "habidos", "habiendo", "habremos", "habrá", "habrán", "habrás", "habré", "habréis", "habría", 
    "habríais", "habríamos", "habrían", "habrías", "habéis", "había", "habíais", "habíamos", "habían", 
    "habías", "hace", "haceis", "hacemos", "hacen", "hacer", "hacerlo", "haces", "hacia", "haciendo", 
    "hago", "han", "has", "hasta", "hay", "haya", "hayamos", "hayan", "hayas", "hayáis", "he", "hecho", 
    "hemos", "hicieron", "hizo", "hoy", "hube", "hubiera", "hubierais", "hubieran", "hubieras", "hubieron", 
    "hubiese", "hubieseis", "hubiesen", "hubieses", "hubimos", "hubiste", "hubisteis", "hubiéramos", 
    "hubiésemos", "hubo", "igual", "incluso", "indicó", "informó", "intenta", "intentais", "intentamos", 
    "intentan", "intentar", "intentas", "intento", "ir", "junto", "la", "lado", "largo", "las", "le", 
    "les", "llegó", "lleva", "llevar", "lo", "los", "luego", "lugar", "manera", "manifestó", "mayor", 
    "me", "mediante", "mejor", "mencionó", "menos", "mi", "mientras", "mio", "mis", "misma", "mismas", 
    "mismo", "mismos", "modo", "momento", "mucha", "muchas", "mucho", "muchos", "muy", "más", "mí", 
    "mía", "mías", "mío", "míos", "nada", "nadie", "ni", "ninguna", "ningunas", "ninguno", "ningunos", 
    "ningún", "no", "nos", "nosotras", "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "nueva", 
    "nuevas", "nuevo", "nuevos", "nunca", "o", "ocho", "os", "otra", "otras", "otro", "otros", "para", 
    "parece", "parte", "partir", "pasada", "pasado", "pero", "pesar", "poca", "pocas", "poco", "pocos", 
    "podeis", "podemos", "poder", "podria", "podriais", "podriamos", "podrian", "podrias", "podrá", 
    "podrán", "podría", "podrían", "poner", "por", "por qué", "porque", "posible", "primer", "primera", 
    "primero", "primeros", "principalmente", "propia", "propias", "propio", "propios", "próximo", 
    "próximos", "pudo", "pueda", "puede", "pueden", "puedo", "pues", "que", "quedó", "queremos", 
    "quien", "quienes", "quiere", "quién", "qué", "realizado", "realizar", "realizó", "respecto", 
    "sabe", "sabeis", "sabemos", "saben", "saber", "sabes", "se", "sea", "seamos", "sean", "seas", 
    "segunda", "segundo", "según", "seis", "ser", "seremos", "será", "serán", "serás", "seré", "seréis", 
    "sería", "seríais", "seríamos", "serían", "serías", "seáis", "señaló", "si", "sido", "siempre", 
    "siendo", "siete", "sigue", "siguiente", "sin", "sino", "sobre", "sois", "sola", "solamente", 
    "solas", "solo", "solos", "somos", "son", "soy", "su", "sus", "suya", "suyas", "suyo", "suyos", 
    "sí", "sólo", "tal", "también", "tampoco", "tan", "tanto", "te", "tendremos", "tendrá", "tendrán", 
    "tendrás", "tendré", "tendréis", "tendría", "tendríais", "tendríamos", "tendrían", "tendrías", 
    "tened", "teneis", "tenemos", "tener", "tenga", "tengamos", "tengan", "tengas", "tengo", "tengáis", 
    "tenida", "tenidas", "tenido", "tenidos", "teniendo", "tenéis", "tenía", "teníais", "teníamos", 
    "tenían", "tenías", "tercera", "ti", "tiempo", "tiene", "tienen", "tienes", "toda", "todas", 
    "todavía", "todo", "todos", "total", "trabaja", "trabajais", "trabajamos", "trabajan", "trabajar", 
    "trabajas", "trabajo", "tras", "trata", "través", "tres", "tu", "tus", "tuve", "tuviera", "tuvierais", 
    "tuvieran", "tuvieras", "tuvieron", "tuviese", "tuvieseis", "tuviesen", "tuvieses", "tuvimos", 
    "tuviste", "tuvisteis", "tuviéramos", "tuviésemos", "tuvo", "tuya", "tuyas", "tuyo", "tuyos", 
    "tú", "ultimo", "un", "una", "unas", "uno", "unos", "usa", "usais", "usamos", "usan", "usar", 
    "usas", "uso", "usted", "va", "vais", "valor", "vamos", "van", "varias", "varios", "vaya", 
    "veces", "ver", "verdad", "verdadera", "verdadero", "vez", "vosotras", "vosotros", "voy", 
    "vuestra", "vuestras", "vuestro", "vuestros", "y", "ya", "yo", "él", "éramos", "ésta", 
    "éstas", "éste", "éstos", "última", "últimas", "último", "últimos", "0o", "0s", "3a", "3b",
    "3d", "6b", "6o", "a", "a1", "a2", "a3", "a4", "ab", "able", "about", "above", "abst", "ac",
    "accordance", "according", "accordingly", "across", "act", "actually", "ad", "added", "adj",
    "ae", "af", "affected", "affecting", "affects", "after", "afterwards", "ag", "again", "against",
    "ah", "ain", "ain't", "aj", "al", "all", "allow", "allows", "almost", "alone", "along", "already",
    "also", "although", "always", "am", "among", "amongst", "amoungst", "amount", "an", "and", "announce",
    "another", "any", "anybody", "anyhow", "anymore", "anyone", "anything", "anyway", "anyways", "anywhere",
    "ao", "ap", "apart", "apparently", "appear", "appreciate", "appropriate", "approximately", "ar", "are",
    "aren", "arent", "aren't", "arise", "around", "as", "a's", "aside", "ask", "asking", "associated", "at",
    "au", "auth", "av", "available", "aw", "away", "awfully", "ax", "ay", "az", "b", "b1", "b2", "b3", "ba",
    "back", "bc", "bd", "be", "became", "because", "become", "becomes", "becoming", "been", "before", "beforehand",
    "begin", "beginning", "beginnings", "begins", "behind", "being", "believe", "below", "beside", "besides",
    "best", "better", "between", "beyond", "bi", "bill", "biol", "bj", "bk", "bl", "bn", "both", "bottom", "bp",
    "br", "brief", "briefly", "bs", "bt", "bu", "but", "bx", "by", "c", "c1", "c2", "c3", "ca", "call", "came",
    "can", "cannot", "cant", "can't", "cause", "causes", "cc", "cd", "ce", "certain", "certainly", "cf", "cg",
    "ch", "changes", "ci", "cit", "cj", "cl", "clearly", "cm", "c'mon", "cn", "co", "com", "come", "comes", "con", 
    "concerning", "consequently", "consider", "considering", "contain", "containing", "contains", "corresponding",
    "could", "couldn", "couldnt", "couldn't", "course", "cp", "cq", "cr", "cry", "cs", "c's", "ct", "cu", "currently",
    "cv", "cx", "cy", "cz", "d", "d2", "da", "date", "dc", "dd", "de", "definitely", "describe", "described",
    "despite", "detail", "df", "di", "did", "didn", "didn't", "different", "dj", "dk", "dl", "do", "does", "doesn",
    "doesn't", "doing", "don", "done", "don't", "down", "downwards", "dp", "dr", "ds", "dt", "du", "due", "during",
    "dx", "dy", "e", "e2", "e3", "ea", "each", "ec", "ed", "edu", "ee", "ef", "effect", "eg", "ei", "eight", "eighty",
    "either", "ej", "el", "eleven", "else", "elsewhere", "em", "empty", "en", "end", "ending", "enough", "entirely",
    "eo", "ep", "eq", "er", "es", "especially", "est", "et", "et-al", "etc", "eu", "ev", "even", "ever", "every",
    "everybody", "everyone", "everything", "everywhere", "ex", "exactly", "example", "except", "ey", "f", "f2", "fa",
    "far", "fc", "few", "ff", "fi", "fifteen", "fifth", "fify", "fill", "find", "fire", "first", "five", "fix",
    "fj", "fl", "fn", "fo", "followed", "following", "follows", "for", "former", "formerly", "forth", "forty",
    "found", "four", "fr", "from", "front", "fs", "ft", "fu", "full", "further", "furthermore", "fy", "g", "ga",
    "gave", "ge", "get", "gets", "getting", "gi", "give", "given", "gives", "giving", "gj", "gl", "go", "goes",
    "going", "gone", "got", "gotten", "gr", "greetings", "gs", "gy", "h", "h2", "h3", "had", "hadn", "hadn't",
    "happens", "hardly", "has", "hasn", "hasnt", "hasn't", "have", "haven", "haven't", "having", "he", "hed",
    "he'd", "he'll", "hello", "help", "hence", "her", "here", "hereafter", "hereby", "herein", "heres", "here's",
    "hereupon", "hers", "herself", "hes", "he's", "hh", "hi", "hid", "him", "himself", "his", "hither", "hj", "ho",
    "home", "hopefully", "how", "howbeit", "however", "how's", "hr", "hs", "http", "hu", "hundred", "hy", "i", "i2",
    "i3", "i4", "i6", "i7", "i8", "ia", "ib", "ibid", "ic", "id", "i'd", "ie", "if", "ig", "ignored", "ih", "ii", "ij",
    "il", "i'll", "im", "i'm", "immediate", "immediately", "importance", "important", "in", "inasmuch", "inc", "indeed",
    "index", "indicate", "indicated", "indicates", "information", "inner", "insofar", "instead", "interest", "into",
    "invention", "inward", "io", "ip", "iq", "ir", "is", "isn", "isn't", "it", "itd", "it'd", "it'll", "its", "it's",
    "itself", "iv", "i've", "ix", "iy", "iz", "j", "jj", "jr", "js", "jt", "ju", "just", "k", "ke", "keep", "keeps", "kept",
    "kg", "kj", "km", "know", "known", "knows", "ko", "l", "l2", "la", "largely", "last", "lately", "later", "latter", "latterly",
    "lb", "lc", "le", "least", "les", "less", "lest", "let", "lets", "let's", "lf", "like", "liked", "likely", "line",
    "little", "lj", "ll", "ll", "ln", "lo", "look", "looking", "looks", "los", "lr", "ls", "lt", "ltd", "m", "m2", "ma",
    "made", "mainly", "make", "makes", "many", "may", "maybe", "me", "mean", "means", "meantime", "meanwhile", "merely", "mg",
    "might", "mightn", "mightn't", "mill", "million", "mine", "miss", "ml", "mn", "mo", "more", "moreover", "most", "mostly",
    "move", "mr", "mrs", "ms", "mt", "mu", "much", "mug", "must", "mustn", "mustn't", "my", "myself", "n", "n2", "na", "name",
    "namely", "nay", "nc", "nd", "ne", "near", "nearly", "necessarily", "necessary", "need", "needn", "needn't", "needs",
    "neither", "never", "nevertheless", "new", "next", "ng", "ni", "nine", "ninety", "nj", "nl", "nn", "no", "nobody", "non",
    "none", "nonetheless", "noone", "nor", "normally", "nos", "not", "noted", "nothing", "novel", "now", "nowhere", "nr", "ns",
    "nt", "ny", "o", "oa", "ob", "obtain", "obtained", "obviously", "oc", "od", "of", "off", "often", "og", "oh", "oi", "oj",
    "ok", "okay", "ol", "old", "om", "omitted", "on", "once", "one", "ones", "only", "onto", "oo", "op", "oq", "or", "ord",
    "os", "ot", "other", "others", "otherwise", "ou", "ought", "our", "ours", "ourselves", "out", "outside", "over", "overall",
    "ow", "owing", "own", "ox", "oz", "p", "p1", "p2", "p3", "page", "pagecount", "pages", "par", "part", "particular",
    "particularly", "pas", "past", "pc", "pd", "pe", "per", "perhaps", "pf", "ph", "pi", "pj", "pk", "pl", "placed", "please",
    "plus", "pm", "pn", "po", "poorly", "possible", "possibly", "potentially", "pp", "pq", "pr", "predominantly", "present",
    "presumably", "previously", "primarily", "probably", "promptly", "proud", "provides", "ps", "pt", "pu", "put", "py", "q",
    "qj", "qu", "que", "quickly", "quite", "qv", "r", "r2", "ra", "ran", "rather", "rc", "rd", "re", "readily", "really",
    "reasonably", "recent", "recently", "ref", "refs", "regarding", "regardless", "regards", "related", "relatively", "research",
    "research-articl", "respectively", "resulted", "resulting", "results", "rf", "rh", "ri", "right", "rj", "rl", "rm", "rn", "ro",
    "rq", "rr", "rs", "rt", "ru", "run", "rv", "ry", "s", "s2", "sa", "said", "same", "saw", "say", "saying", "says", "sc", "sd",
    "se", "sec", "second", "secondly", "section", "see", "seeing", "seem", "seemed", "seeming", "seems", "seen", "self",
    "selves", "sensible", "sent", "serious", "seriously", "seven", "several", "sf", "shall", "shan", "shan't", "she",
    "shed", "she'd", "she'll", "shes", "she's", "should", "shouldn", "shouldn't", "should've", "show", "showed", "shown",
    "showns", "shows", "si", "side", "significant", "significantly", "similar", "similarly", "since", "sincere", "six",
    "sixty", "sj", "sl", "slightly", "sm", "sn", "so", "some", "somebody", "somehow", "someone", "somethan", "something",
    "sometime", "sometimes", "somewhat", "somewhere", "soon", "sorry", "sp", "specifically", "specified", "specify",
    "specifying", "sq", "sr", "ss", "st", "still", "stop", "strongly", "sub", "substantially", "successfully", "such",
    "sufficiently", "suggest", "sup", "sure", "sy", "system", "sz", "t", "t1", "t2", "t3", "take", "taken", "taking", "tb",
    "tc", "td", "te", "tell", "ten", "tends", "tf", "th", "than", "thank", "thanks", "thanx", "that", "that'll", "thats",
    "that's", "that've", "the", "their", "theirs", "them", "themselves", "then", "thence", "there", "thereafter", "thereby",
    "thered", "therefore", "therein", "there'll", "thereof", "therere", "theres", "there's", "thereto", "thereupon",
    "there've", "these", "they", "theyd", "they'd", "they'll", "theyre", "they're", "they've", "thickv", "thin", "think",
    "third", "this", "thorough", "thoroughly", "those", "thou", "though", "thoughh", "thousand", "three", "throug", "through",
    "throughout", "thru", "thus", "ti", "til", "tip", "tj", "tl", "tm", "tn", "to", "together", "too", "took", "top",
    "toward", "towards", "tp", "tq", "tr", "tried", "tries", "truly", "try", "trying", "ts", "t's", "tt", "tv", "twelve",
    "twenty", "twice", "two", "tx", "u", "u201d", "ue", "ui", "uj", "uk", "um", "un", "under", "unfortunately", "unless",
    "unlike", "unlikely", "until", "unto", "uo", "up", "upon", "ups", "ur", "us", "use", "used", "useful", "usefully",
    "usefulness", "uses", "using", "usually", "ut", "v", "va", "value", "various", "vd", "ve", "ve", "very", "via", "viz", 
    "vj", "vo", "vol", "vols", "volumtype", "vq", "vs", "vt", "vu", "w", "wa", "want", "wants", "was", "wasn", "wasnt", "wasn't",
    "way", "we", "wed", "we'd", "welcome", "well", "we'll", "well-b", "went", "were", "we're", "weren", "werent", "weren't",
    "we've", "what", "whatever", "what'll", "whats", "what's", "when", "whence", "whenever", "when's", "where", "whereafter",
    "whereas", "whereby", "wherein", "wheres", "where's", "whereupon", "wherever", "whether", "which", "while", "whim", "whither",
    "who", "whod", "whoever", "whole", "who'll", "whom", "whomever", "whos", "who's", "whose", "why", "why's", "wi", "widely",
    "will", "willing", "wish", "with", "within", "without", "wo", "won", "wonder", "wont", "won't", "words", "world", "would",
    "wouldn", "wouldnt", "wouldn't", "www", "x", "x1", "x2", "x3", "xf", "xi", "xj", "xk", "xl", "xn", "xo", "xs", "xt", "xv",
    "xx", "y", "y2", "yes", "yet", "yj", "yl", "you", "youd", "you'd", "you'll", "your", "youre", "you're", "yours", "yourself",
    "yourselves", "you've", "yr", "ys", "yt", "z", "zero", "zi", "zz", "a", "acerca", "adeus", "agora", "ainda", "alem", "algmas", "algo", "algumas", "alguns", "ali", "além", "ambas", "ambos", "ano", "anos", "antes", "ao", "aonde", "aos", "apenas", "apoio", "apontar", "apos", "após", "aquela", "aquelas", "aquele", "aqueles", "aqui", "aquilo", "as", "assim", "através", "atrás", "até", "aí", "baixo", "bastante", "bem", "boa", "boas", "bom", "bons", "breve", "cada", "caminho", "catorze", "cedo", "cento", "certamente", "certeza", "cima", "cinco", "coisa", "com", "como", "comprido", "conhecido", "conselho", "contra", "contudo", "corrente", "cuja", "cujas", "cujo", "cujos", "custa", "cá", "da", "daquela", "daquelas", "daquele", "daqueles", "dar", "das", "de", "debaixo", "dela", "delas", "dele", "deles", "demais", "dentro", "depois", "desde", "desligado", "dessa", "dessas", "desse", "desses", "desta", "destas", "deste", "destes", "deve", "devem", "deverá", "dez", "dezanove", "dezasseis", "dezassete", "dezoito", "dia", "diante", "direita", "dispoe", "dispoem", "diversa", "diversas", "diversos", "diz", "dizem", "dizer", "do", "dois", "dos", "doze", "duas", "durante", "dá", "dão", "dúvida", "e", "ela", "elas", "ele", "eles", "em", "embora", "enquanto", "entao", "entre", "então", "era", "eram", "essa", "essas", "esse", "esses", "esta", "estado", "estamos", "estar", "estará", "estas", "estava", "estavam", "este", "esteja", "estejam", "estejamos", "estes", "esteve", "estive", "estivemos", "estiver", "estivera", "estiveram", "estiverem", "estivermos", "estivesse", "estivessem", "estiveste", "estivestes", "estivéramos", "estivéssemos", "estou", "está", "estás", "estávamos", "estão", "eu", "exemplo", "falta", "fará", "favor", "faz", "fazeis", "fazem", "fazemos", "fazer", "fazes", "fazia", "faço", "fez", "fim", "final", "foi", "fomos", "for", "fora", "foram", "forem", "forma", "formos", "fosse", "fossem", "foste", "fostes", "fui", "fôramos", "fôssemos", "geral", "grande", "grandes", "grupo", "ha", "haja", "hajam", "hajamos", "havemos", "havia", "hei", "hoje", "hora", "horas", "houve", "houvemos", "houver", "houvera", "houveram", "houverei", "houverem", "houveremos", "houveria", "houveriam", "houvermos", "houverá", "houverão", "houveríamos", "houvesse", "houvessem", "houvéramos", "houvéssemos", "há", "hão", "iniciar", "inicio", "ir", "irá", "isso", "ista", "iste", "isto", "já", "lado", "lhe", "lhes", "ligado", "local", "logo", "longe", "lugar", "lá", "maior", "maioria", "maiorias", "mais", "mal", "mas", "me", "mediante", "meio", "menor", "menos", "meses", "mesma", "mesmas", "mesmo", "mesmos", "meu", "meus", "mil", "minha", "minhas", "momento", "muito", "muitos", "máximo", "mês", "na", "nada", "nao", "naquela", "naquelas", "naquele", "naqueles", "nas", "nem", "nenhuma", "nessa", "nessas", "nesse", "nesses", "nesta", "nestas", "neste", "nestes", "no", "noite", "nome", "nos", "nossa", "nossas", "nosso", "nossos", "nova", "novas", "nove", "novo", "novos", "num", "numa", "numas", "nunca", "nuns", "não", "nível", "nós", "número", "o", "obra", "obrigada", "obrigado", "oitava", "oitavo", "oito", "onde", "ontem", "onze", "os", "ou", "outra", "outras", "outro", "outros", "para", "parece", "parte", "partir", "paucas", "pegar", "pela", "pelas", "pelo", "pelos", "perante", "perto", "pessoas", "pode", "podem", "poder", "poderá", "podia", "pois", "ponto", "pontos", "por", "porque", "porquê", "portanto", "posição", "possivelmente", "posso", "possível", "pouca", "pouco", "poucos", "povo", "primeira", "primeiras", "primeiro", "primeiros", "promeiro", "propios", "proprio", "própria", "próprias", "próprio", "próprios", "próxima", "próximas", "próximo", "próximos", "puderam", "pôde", "põe", "põem", "quais", "qual", "qualquer", "quando", "quanto", "quarta", "quarto", "quatro", "que", "quem", "quer", "quereis", "querem", "queremas", "queres", "quero", "questão", "quieto", "quinta", "quinto", "quinze", "quáis", "quê", "relação", "sabe", "sabem", "saber", "se", "segunda", "segundo", "sei", "seis", "seja", "sejam", "sejamos", "sem", "sempre", "sendo", "ser", "serei", "seremos", "seria", "seriam", "será", "serão", "seríamos", "sete", "seu", "seus", "sexta", "sexto", "sim", "sistema", "sob", "sobre", "sois", "somente", "somos", "sou", "sua", "suas", "são", "sétima", "sétimo", "só", "tal", "talvez", "tambem", "também", "tanta", "tantas", "tanto", "tarde", "te", "tem", "temos", "tempo", "tendes", "tenha", "tenham", "tenhamos", "tenho", "tens", "tentar", "tentaram", "tente", "tentei", "ter", "terceira", "terceiro", "terei", "teremos", "teria", "teriam", "terá", "terão", "teríamos", "teu", "teus", "teve", "tinha", "tinham", "tipo", "tive", "tivemos", "tiver", "tivera", "tiveram", "tiverem", "tivermos", "tivesse", "tivessem", "tiveste", "tivestes", "tivéramos", "tivéssemos", "toda", "todas", "todo", "todos", "trabalhar", "trabalho", "treze", "três", "tu", "tua", "tuas", "tudo", "tão", "tém", "têm", "tínhamos", "um", "uma", "umas", "uns", "usa", "usar", "vai", "vais", "valor", "veja", "vem", "vens", "ver", "verdade", "verdadeiro", "vez", "vezes", "viagem", "vindo", "vinte", "você", "vocês", "vos", "vossa", "vossas", "vosso", "vossos", "vários", "vão", "vêm", "vós", "zero", "à", "às", "área", "é", "éramos", "és", "último", "a", "abord", "absolument", "afin", "ah", "ai", "aie", "aient", "aies", "ailleurs", "ainsi", "ait", "allaient", "allo", "allons", "allô", "alors", "anterieur", "anterieure", "anterieures", "apres", "après", "as", "assez", "attendu", "au", "aucun", "aucune", "aucuns", "aujourd", "aujourd'hui", "aupres", "auquel", "aura", "aurai", "auraient", "aurais", "aurait", "auras", "aurez", "auriez", "aurions", "aurons", "auront", "aussi", "autant", "autre", "autrefois", "autrement", "autres", "autrui", "aux", "auxquelles", "auxquels", "avaient", "avais", "avait", "avant", "avec", "avez", "aviez", "avions", "avoir", "avons", "ayant", "ayez", "ayons", "b", "bah", "bas", "basee", "bat", "beau", "beaucoup", "bien", "bigre", "bon", "boum", "bravo", "brrr", "c", "car", "ce", "ceci", "cela", "celle", "celle-ci", "celle-là", "celles", "celles-ci", "celles-là", "celui", "celui-ci", "celui-là", "celà", "cent", "cependant", "certain", "certaine", "certaines", "certains", "certes", "ces", "cet", "cette", "ceux", "ceux-ci", "ceux-là", "chacun", "chacune", "chaque", "cher", "chers", "chez", "chiche", "chut", "chère", "chères", "ci", "cinq", "cinquantaine", "cinquante", "cinquantième", "cinquième", "clac", "clic", "combien", "comme", "comment", "comparable", "comparables", "compris", "concernant", "contre", "couic", "crac", "d", "da", "dans", "de", "debout", "dedans", "dehors", "deja", "delà", "depuis", "dernier", "derniere", "derriere", "derrière", "des", "desormais", "desquelles", "desquels", "dessous", "dessus", "deux", "deuxième", "deuxièmement", "devant", "devers", "devra", "devrait", "different", "differentes", "differents", "différent", "différente", "différentes", "différents", "dire", "directe", "directement", "dit", "dite", "dits", "divers", "diverse", "diverses", "dix", "dix-huit", "dix-neuf", "dix-sept", "dixième", "doit", "doivent", "donc", "dont", "dos", "douze", "douzième", "dring", "droite", "du", "duquel", "durant", "dès", "début", "désormais", "e", "effet", "egale", "egalement", "egales", "eh", "elle", "elle-même", "elles", "elles-mêmes", "en", "encore", "enfin", "entre", "envers", "environ", "es", "essai", "est", "et", "etant", "etc", "etre", "eu", "eue", "eues", "euh", "eurent", "eus", "eusse", "eussent", "eusses", "eussiez", "eussions", "eut", "eux", "eux-mêmes", "exactement", "excepté", "extenso", "exterieur", "eûmes", "eût", "eûtes", "f", "fais", "faisaient", "faisant", "fait", "faites", "façon", "feront", "fi", "flac", "floc", "fois", "font", "force", "furent", "fus", "fusse", "fussent", "fusses", "fussiez", "fussions", "fut", "fûmes", "fût", "fûtes", "g", "gens", "h", "ha", "haut", "hein", "hem", "hep", "hi", "ho", "holà", "hop", "hormis", "hors", "hou", "houp", "hue", "hui", "huit", "huitième", "hum", "hurrah", "hé", "hélas", "i", "ici", "il", "ils", "importe", "j", "je", "jusqu", "jusque", "juste", "k", "l", "la", "laisser", "laquelle", "las", "le", "lequel", "les", "lesquelles", "lesquels", "leur", "leurs", "longtemps", "lors", "lorsque", "lui", "lui-meme", "lui-même", "là", "lès", "m", "ma", "maint", "maintenant", "mais", "malgre", "malgré", "maximale", "me", "meme", "memes", "merci", "mes", "mien", "mienne", "miennes", "miens", "mille", "mince", "mine", "minimale", "moi", "moi-meme", "moi-même", "moindres", "moins", "mon", "mot", "moyennant", "multiple", "multiples", "même", "mêmes", "n", "na", "naturel", "naturelle", "naturelles", "ne", "neanmoins", "necessaire", "necessairement", "neuf", "neuvième", "ni", "nombreuses", "nombreux", "nommés", "non", "nos", "notamment", "notre", "nous", "nous-mêmes", "nouveau", "nouveaux", "nul", "néanmoins", "nôtre", "nôtres", "o", "oh", "ohé", "ollé", "olé", "on", "ont", "onze", "onzième", "ore", "ou", "ouf", "ouias", "oust", "ouste", "outre", "ouvert", "ouverte", "ouverts", "o|", "où", "p", "paf", "pan", "par", "parce", "parfois", "parle", "parlent", "parler", "parmi", "parole", "parseme", "partant", "particulier", "particulière", "particulièrement", "pas", "passé", "pendant", "pense", "permet", "personne", "personnes", "peu", "peut", "peuvent", "peux", "pff", "pfft", "pfut", "pif", "pire", "pièce", "plein", "plouf", "plupart", "plus", "plusieurs", "plutôt", "possessif", "possessifs", "possible", "possibles", "pouah", "pour", "pourquoi", "pourrais", "pourrait", "pouvait", "prealable", "precisement", "premier", "première", "premièrement", "pres", "probable", "probante", "procedant", "proche", "près", "psitt", "pu", "puis", "puisque", "pur", "pure", "q", "qu", "quand", "quant", "quant-à-soi", "quanta", "quarante", "quatorze", "quatre", "quatre-vingt", "quatrième", "quatrièmement", "que", "quel", "quelconque", "quelle", "quelles", "quelqu'un", "quelque", "quelques", "quels", "qui", "quiconque", "quinze", "quoi", "quoique", "r", "rare", "rarement", "rares", "relative", "relativement", "remarquable", "rend", "rendre", "restant", "reste", "restent", "restrictif", "retour", "revoici", "revoilà", "rien", "s", "sa", "sacrebleu", "sait", "sans", "sapristi", "sauf", "se", "sein", "seize", "selon", "semblable", "semblaient", "semble", "semblent", "sent", "sept", "septième", "sera", "serai", "seraient", "serais", "serait", "seras", "serez", "seriez", "serions", "serons", "seront", "ses", "seul", "seule", "seulement", "si", "sien", "sienne", "siennes", "siens", "sinon", "six", "sixième", "soi", "soi-même", "soient", "sois", "soit", "soixante", "sommes", "son", "sont", "sous", "souvent", "soyez", "soyons", "specifique", "specifiques", "speculatif", "stop", "strictement", "subtiles", "suffisant", "suffisante", "suffit", "suis", "suit", "suivant", "suivante", "suivantes", "suivants", "suivre", "sujet", "superpose", "sur", "surtout", "t", "ta", "tac", "tandis", "tant", "tardive", "te", "tel", "telle", "tellement", "telles", "tels", "tenant", "tend", "tenir", "tente", "tes", "tic", "tien", "tienne", "tiennes", "tiens", "toc", "toi", "toi-même", "ton", "touchant", "toujours", "tous", "tout", "toute", "toutefois", "toutes", "treize", "trente", "tres", "trois", "troisième", "troisièmement", "trop", "très", "tsoin", "tsouin", "tu", "té", "u", "un", "une", "unes", "uniformement", "unique", "uniques", "uns", "v", "va", "vais", "valeur", "vas", "vers", "via", "vif", "vifs", "vingt", "vivat", "vive", "vives", "vlan", "voici", "voie", "voient", "voilà", "voire", "vont", "vos", "votre", "vous", "vous-mêmes", "vu", "vé", "vôtre", "vôtres", "w", "x", "y", "z", "zut", "à", "â", "ça", "ès", "étaient", "étais", "était", "étant", "état", "étiez", "étions", "été", "étée", "étées", "étés", "êtes", "être", "ô"
]


    if st.button("Analyze"):
        if url:
            # ses = requests_html.HTMLSession()
            # headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            #            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            #            'Accept-Encoding':'gzip',
            #            'Cache-Control':'no-cache',
            #            'Pragma':'no-cache',
            #            'x-seo-crawler':st.secrets["CUSTOM_HEADER"]}
            # # sync
            # get_url = ses.get(url, headers=headers)
            # # get_url.html.render()
            # # st.info(f"prueba{get_url}")
            # soup = BeautifulSoup(get_url.text, "html.parser") 

            get_url = requests.get(url)
            soup = BeautifulSoup(get_url.text, "html.parser")

            st.subheader("URL friendliness")
            try:
                hyphen_count = url.count("-")
                has_digit = any(char.isdigit() for char in url)
                st.info(f"This is the URL:\n{url}", icon="👀")
                if hyphen_count > 6:
                    st.warning(f"The URL seems to be too long. Consider shortening it.", icon="⚠️")
                else:
                    st.success(f"The URL looks fine in terms of length.", icon="✅")

                if has_digit:
                    st.warning("The URL doesn't seem very SEO friendly. Consider removing any numbers if they are not necessary.", icon="⚠️")
                else:
                    st.success(f"The URL is fine in terms of SEO friendliness.", icon="✅")
                
                #keyword check in URL
                if kw:
                    kw_cln = ' '.join(word for word in kw.split() if word.lower() not in stopwords)

                    if len(kw_cln) == 0:
                        st.warning("The keyword cannot be empty after removing stopwords. Please try again.")
                    else:
                        url_cleaned = url.split("/")[-2]
                        url_cleaned = url_cleaned.replace("-", " ")
                        url_cleaned = ' '.join(word for word in url_cleaned.split() if word.lower() not in stopwords)
                        kw_cln_url = kw_cln.replace('ñ', 'n')

                        if kw_cln_url.lower() in url_cleaned:
                            st.success(f"The keyword '{kw}' is in the URL.", icon="✅")
                        else:
                            st.error(f"The keyword '{kw}' is not in the URL.", icon="🚨")

            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please check that it's valid.")
            
            st.subheader("SEO Title Length:")
            try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser")                                
                
                seot, lenseot = get_seo_title_length(soup)
                if lenseot < 50:
                    st.error(f"SEO title is BELOW 50 characters. It is {lenseot} characters long.\n\nCurrent SEO Title: '{seot}'", icon="🚨" )
                elif lenseot > 65:
                    st.error(f"SEO title is a bit too long. Please shorten it.\n\nCurrent SEO Title: '{seot}'", icon="🚨")
                    st.warning(f"If this is a 'News' kind of article and not an Evergreen/Roundup, the SEO Title can be longer for editorial purposes", icon="⚠️")
                else:
                    st.success(f"SEO title is OPTIMIZED in terms of length. Well done!\n\nSEO Title: '{seot}'", icon="✅")

            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please check that it's valid.")

            # Check KW in SEO Title
            if kw:
                seot_cln = ' '.join(word for word in seot.split() if word.lower() not in stopwords)
                # kw_cln = kw.lower()
                if len(seot_cln) > 0:
                    if kw_cln.lower() in seot_cln.lower():
                        st.success(f"The keyword'{kw}' is in the SEO Title", icon="✅")
                    else:
                        st.error(f"La kewyword '{kw}' NO está en el SEO Title", icon="🚨")

            
            st.subheader("Meta Description Length:")
            try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser")                   
    
                metad, len_metad = get_meta_description_length(soup)
                if len_metad < 120:
                    st.error(f"Meta Description is BELOW 120 characters. It is {len_metad} characters long.\n\nMeta Description: '{metad}'", icon="🚨" )
                elif len_metad > 150:
                    st.error(f"Meta Description is OVER 150 characters. It is {len_metad} characters long.\n\nMeta Description: '{metad}'", icon="🚨" )
                else:
                    st.success(f"Meta Description is OPTIMIZED in terms of length. It is {len_metad} characters long. Well done!\n\n Meta Description: '{metad}'", icon="✅")
            
            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please check that it's valid.")                

            # Check KW Meta-Description
            if kw:
                kw_metad  = ' '.join(word for word in metad.split() if word.lower() not in stopwords)
                if kw_cln.lower() in kw_metad.lower():
                    st.success(f"The keyword '{kw}' is in the MetaDescription", icon="✅")
                else:
                    st.error(f"The keyword '{kw}' IS NOT in the MetaDescription", icon="🚨")


            st.subheader("Secondary Title Length:")
            try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser")                    
    
                secondary, len_secondary = get_secondary_title_length(soup)
                if len_secondary < 110:
                    st.warning(f"Secondary title seems to be too short. Please ensure its length is between one and a half lines to two lines and is at least longer than 110 characters long.\n\nCurrent Secondary Title:'{secondary}'", icon="⚠️")
                elif len_secondary > 210:
                    st.warning(f"Secondary title seems to be too long. Please ensure its length is between one and a half lines to two lines.\n\Current Secondary Title:'{secondary}'", icon="⚠️")
                else:
                    if len_secondary > 109 and len_secondary < 211:
                        st.success(f"Looks like Secondary Title is OPTIMIZED in terms of length. Well done!\n\nSecondary Title: '{secondary}'", icon="✅")
            
            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please, check that it's valid.")

            # Check kw secondary title
            if kw:
                kw_secon  = ' '.join(word for word in secondary.split() if word.lower() not in stopwords)
                if kw_cln.lower() in kw_secon.lower():
                    st.warning(f"The keyword '{kw}' it's in the secondary title, although it's fine, try to use a secondary keyword instead", icon="⚠️")
                else:
                    st.warning(f"The keyword '{kw}' is not in the secondary title, which is okay, as long as we are using a secondary keyword instead, please make sure of it.", icon="⚠️")
            
            # Check kw in 1st paragraph
            try:
                if kw:
                    st.subheader("Is the keyword in the first paragraph?")    
                    par_full = kw_in_first_par(soup)

                    kw_par  = ' '.join(word for word in par_full.split() if word.lower() not in stopwords)

                    if kw_cln.lower() in kw_par.lower():
                        st.success(f"The keyword '{kw}' appears in the first paragraph of the article", icon="✅")
                    else:
                        st.warning(f"The keyword '{kw}' does not appear in the first paragraph of the article, please try to add it in the first paragraph", icon="⚠️")
            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please, check that it's valid.")

                # # kw_cln = kw.lower()
                # if len(par_cln) > 0:
                #     if kw_cln.lower() in par_cln.lower():
                #         st.success(f"La keyword '{kw}' está en el primer párrafo:\n\n{par_full}", icon="✅")
                #     else:
                #         st.error(f"La keyword '{kw}' NO está en el primer párrafo. Please, add it.", icon="🚨")
            # else:
            #     st.info(f"This is the 1st paragraph, please make sure the main keyword is in it:\n{par_full}")

            # Check kw density
            # st.subheader("Keyword density (how many times the focus keyword appears in the content in relation to total words")
            # if kw:
            #     word_list, word_count = kw_density(soup, stopwords)
            #     # st.info(f"Word list: {word_list}")
            #     # st.info(f"word count{word_count}")

            #     find = kw_cln.lower()
            #     words_in_keyword = kw_cln.split()
            #     if find in word_list:
            #         kw_count = word_list.count(find)
            #         words_in_keyword = kw_cln.split()
            #         a = word_count
            #         kw_len = len(words_in_keyword)
            #         b = kw_len
            #         while True:
            #             try:
            #                 c = round(a//b,4)
            #                 d = round(kw_count / c,4)
            #                 e = round(d,4)
            #                 f = e * 100
            #                 kw_den = str(round(f,3))
            #                 st.info(f"the keyword '{kw}' appears {kw_count} times in the content, hence the keyword density is {kw_den}%")
            #                 break
            #             except ZeroDivisionError:
            #                 print('\nDivision by Zero Error, Please input a valid keyword')
            #                 break
            #     # return kw_count, word_count, kw_len            

            # Internal Links            
            st.subheader("Internal Links:")
        # try:
            # get_url = requests.get(url)
            # soup = BeautifulSoup(get_url.text, "html.parser")
            art_ucount, art_count, art_list= get_internal_links_count(soup, url)
            feverup_count, feverup_percentage, exp_plans = feverup_plans_check(soup, art_count)
            
            cta_count,cta_list = check_cta(soup)
            
            if feverup_count > 0:
                # st.info(f"Number of items: {h2_count}")
                # st.error(f"feverup count {feverup_count}")
                # st.error(f"feverup percentage {feverup_percentage}")
                if feverup_percentage > 30:
                    st.error(f"The percentage of Fever plans in this article exceeds the allowed 30%. There are a total of {feverup_count} plans, making a {feverup_percentage}% of the total.", icon="🚨")
                else:
                    st.info(f"The percentage of Fever plans in this article is {feverup_percentage}, with a total of {feverup_count} plans in it. You can add more as long as the total percentage does not exceed the 30% mark.", icon="👀")
                if len(exp_plans) > 0:
                    st.warning(f"There are some expired Fever plans linked in the article, please remove or substitute them. Here the expired plans:\n Here are the links: {exp_plans}.", icon="⚠️")
            else:
                    st.info(f"There are no Fever plans linked in the article.", icon="👀")
            if cta_count > 0:
                total = art_ucount - cta_count
                if total == 0:
                    if art_list[0]==cta_list[0]:
                        st.error(f"There is only one internal link in the article and it is the same as the CTA.\n\nPlease make sure that it is different to the CTA and add more relevant key content articles as internal links.", icon="🚨")
                        st.warning(f"If this is a Fever branded article, please disregard this alert, as internal linking is not applied.", icon="⚠️")
                    else:
                        st.error(f"There is only one internal link in the article.\n\nPlease add more relevant key content articles as internal links.", icon="🚨")
                        st.warning(f"If this is a Fever branded article, please disregard this alert, as internal linking is not applied.", icon="⚠️")
                elif total < 0:
                    st.error(f"There's no internal linking in the article. Please, add relevant key content articles as internal links.", icon="🚨")
                    st.warning(f"If this is a Fever branded article, please disregard this alert, as internal linking is not applied.", icon="⚠️")
                elif total > 0 and total <= 3:
                    st.warning(f"Please consider adding more unique articles as internal links.\n\n There are a total of {total} unique articles and a total of {art_count} URLs (one being the CTA) linked within this article.\n\n Here are the links: {art_list}.", icon="⚠️")
                    st.warning(f"If this is a Fever branded article, please disregard this alert, as internal linking is not applied.", icon="⚠️")
                else:
                    if total > 3:
                        st.success(f"Nicely done!\nThere are a total of {total} no CTA unique articles in the content and a total of {art_count} URLs linked within this article.\n\nHere the links: {art_list}.", icon="✅")
            else:
                if art_ucount < 1:
                    st.error(f"There is no internal linking in the article. Please add relevant key content articles as internal links.", icon="🚨")
                    st.warning(f"If this is a Fever branded article, please disregard this alert, as internal linking is not applied.", icon="⚠️")
                elif art_ucount > 0 and art_ucount <= 3:
                    st.warning(f"Please consider adding more unique articles as internal links.\n\n There are a total of {art_ucount} unique articles and a total of {art_count} URLs linked within this article.\n\n Here are the links: {art_list}.", icon="⚠️")
                    st.warning(f"If this is a Fever branded article, please disregard this alert, as internal linking is not applied.", icon="⚠️")
                else:
                    st.success(f"Nicely done!.\nThere are a total of {total} unique articles and a total of {art_count} URLs linked within this article.\n Here are the links: {art_list}.", icon="✅")
        # except Exception as e:
        #     st.error("Error: Unable to analyze the URL. Please, check that it's valid.")

            st.subheader("CTA Checker:")
            try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser")                       
    
                cta_count,cta_list = check_cta(soup)
                if cta_count > 0:
                    st.success(f"There is a CTA: {cta_list}", icon="✅")
                    # st.info(f"That means that from the {art_ucount} links, one is the CTA.", icon="👀")
                #     total=art_ucount-1
                #     if total>1:
                #         st.info(f"\nTotal amount of unique articles is {total}.", icon="👀")
                #     elif total == 0:
                #         st.error(f"There is no internal linking done in this article. Please, add internal linking throughout the content, linking to key content.", icon="🚨")
                #     else:
                #         st.warning(f"Total amount of unique articles is just {total}. Please, add more internal linking throughout the content", icon="⚠️")
                else:
                    st.error("There is no CTA. Please add one evergreen key organic content link as a CTA.", icon="🚨")
            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please check that it's valid.")                

            st.subheader("Categories Count:")
            try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser") 
    
                cat_ucount, cat_count = get_categories_count(soup)
                if cat_count < 1:
                    st.error("There are no categories. Please, add a max of two categories.", icon="🚨")
                elif cat_count > 2:
                    st.error("There are more than 2 categories. Please, limit it to one or two.", icon="🚨")
                else:
                    st.success(f"There is a total of {cat_ucount} categories in this article. Perfect!", icon="✅")
            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please check that it's valid.") 

            st.subheader("Featured Image Size and Alt:") 
            try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser")                                 
                   
                width = get_featured_image_width(soup)
                alt = get_featured_image_alt(soup)
                if width != None:
                    if width >= 1200:
                        st.success(f"The featured image meets width requirements of at least 1200px wide: it is {width}px.\n\nThe Alt is: '{alt}'", icon="✅")
                    else:
                        st.warning(f"Remember: feature image must be at least 1200px wide.\n\nThe current featured image is {width}px wide.\n\nThe Alt is: '{alt}'", icon="⚠️")            
                else:
                    st.error("The article has no featured image. Please add one of a minimum of 1200px wide.", icon="🚨")              
            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please, check if it's valid.")   
            
            st.subheader("Images in content:")
            
            get_url = requests.get(url)
            soup = BeautifulSoup(get_url.text, "html.parser") 

            img_count, alt_count, alt_list, ig_count, total = get_total_image_count(soup)
                
            if img_count <=1 and ig_count != 0:
                st.error(f"All images (except for the featured one) are Instagram embed ({ig_count}). Please add uploaded images instead, where possible.", icon="🚨")
            elif img_count > 1 and ig_count < 1:    
                if alt_count == img_count:
                    st.success(f"There are a total of {img_count} uploaded images, all with alt text.\n\nHere are the alt texts:{alt_list}", icon="✅")
                else:
                    st.warning(f"There are a total of {img_count} images, out of these, {img_count-alt_count} have no alt text.\n\nPlease add alt text to these images.", icon="⚠️")
            elif img_count > 1 and ig_count > 0:
                if alt_count == img_count:
                    st.success(f"There are a total of {total} images, including {ig_count} embeds from Instagram.\n\nAll of the uploaded images have alt text.\n\nHere are the alt texts:{alt_list}", icon="✅")
                    st.warning(f"Please try to limit the use of Instagram embeds as much as possible.", icon="⚠️")
                else:
                    st.warning(f"There are a total of {total} images, including {ig_count} embeds from Instagram.\n\nFrom those {img_count} uploaded images, {img_count-alt_count} have no alt. Please add alt text to the images.", icon="⚠️")
            else:
                st.error(f"There are no images included in the content. Please, add images.", icon="🚨")
        else:
            st.warning("Please enter a valid URL.")
    st.divider()
    st.caption("If you happen to find any bug or something to be fixed, please contact [Aitor Alonso](https://fever.slack.com/team/U04CDG1B5CZ)\nfrom the SEO team on Slack")
if __name__ == "__main__":
    main()
