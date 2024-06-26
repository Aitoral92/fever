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

def check_cta(soup):
    # # Create a copy of soup so it does not interfare with internal links count
    # soup_copy = BeautifulSoup(str(soup), "html.parser")
    
    all_content = soup.find("div", class_="smn-tracklink-cta")

    cta_count = 0
    cta_list = []
    try:
        for a in all_content.find_all('a', href=True):
            cta_count += 1
            cta_list.append(a['href'])
    except AttributeError:
        cta_count = 0
        cta_list = []
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

    if st.button("Analyze"):
        if url:
            # headers = {
            #     'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            #     'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            #     'Accept-Encoding':'gzip',
            #     'Cache-Control':'no-cache',
            #     'Pragma':'no-cache',
            #     'x-seo-crawler':'*****'}
            # get_url = requests.get(url,headers=headers)
            # # get_url = requests.get(url_head)
            # st.info(f"prueba{get_url}")
            # soup = BeautifulSoup(get_url.content, "html.parser")
            # st.info(f"prueba{soup}")
            
            ses = requests_html.HTMLSession()
            headers = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                       'Accept-Encoding':'gzip',
                       'Cache-Control':'no-cache',
                       'Pragma':'no-cache',
                       'x-seo-crawler':st.secrets["CUSTOM_HEADER"]}
            # sync
            get_url = ses.get(url, headers=headers)
            # get_url.html.render()
            # st.info(f"prueba{get_url}")
            soup = BeautifulSoup(get_url.text, "html.parser") 
            # st.info(f"prueba{soup}")
            # 
            # Async
            # get_url = await asession.get(url, headers=headers)
            # st.info(f"prueba{get_url}")
            # await get_url.html.arender()
            # soup = BeautifulSoup(get_url.text, "html.parser") 
            # st.info(f"prueba{soup}")

            st.subheader("URL friendliness")
            # try:
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

                # hyphen_count, has_digit = count_hyphens_and_digits_in_url(url)
                # st.info(f"This is the URL:\n{url}", icon="👀")
                # if hyphen_count > 6:
                #     st.warning(f"The URL seems to be too long. Consider shortening it.", icon="⚠️")
                # else:
                #     st.success(f"The URL looks fine in terms of length.", icon="✅")

                # if has_digit:
                #     st.warning("The URL doesn't seem very SEO friendly. Consider removing any numbers if they are not necessary.", icon="⚠️")
                # else:
                #     st.success(f"The URL is fine in terms of SEO friendliness.", icon="✅")
            # except Exception as e:
            #     st.error("Error: Unable to analyze the URL. Please check that it's valid.")
            
            st.subheader("SEO Title Length:")
            # try:
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
            # except Exception as e:
            #     st.error("Error: Unable to analyze the URL. Please check that it's valid.")
            
            st.subheader("Meta Description Length:")
            # try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser")                   
    
            metad, len_metad = get_meta_description_length(soup)
            if len_metad < 120:
                st.error(f"Meta Description is BELOW 120 characters. It is {len_metad} characters long.\n\nMeta Description: '{metad}'", icon="🚨" )
            elif len_metad > 150:
                st.error(f"Meta Description is OVER 150 characters. It is {len_metad} characters long.\n\nMeta Description: '{metad}'", icon="🚨" )
            else:
                st.success(f"Meta Description is OPTIMIZED in terms of length. It is {len_metad} characters long. Well done!\n\n Meta Description: '{metad}'", icon="✅")
            # except Exception as e:
            #     st.error("Error: Unable to analyze the URL. Please check that it's valid.")

            st.subheader("Secondary Title Length:")
            # try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser")                    
    
            secondary, len_secondary = get_secondary_title_length(soup)
            if len_secondary < 120:
                st.warning(f"Secondary title seems to be too short. Please ensure its length is between one and a half lines to two lines.\n\nCurrent Secondary Title:'{secondary}'", icon="⚠️")
            elif len_secondary > 210:
                st.warning(f"Secondary title seems to be too long. Please ensure its length is between one and a half lines to two lines.\n\Current Secondary Title:'{secondary}'", icon="⚠️")
            else:
                if len_secondary > 120 and len_secondary < 210:
                    st.success(f"Looks like Secondary Title is OPTIMIZED in terms of length. Well done!\n\nSecondary Title: '{secondary}'", icon="✅")
            # except Exception as e:
            #     st.error("Error: Unable to analyze the URL. Please, check that it's valid.")
            
            st.subheader("Internal Links:")
            # try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser")                       
    
            art_ucount, art_count, art_list = get_internal_links_count(soup, url)
            cta_count,cta_list = check_cta(soup)
            
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
            # try:
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
            # except Exception as e:
            #     st.error("Error: Unable to analyze the URL. Please check that it's valid.")                

            st.subheader("Categories Count:")
            # try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser") 
    
            cat_ucount, cat_count = get_categories_count(soup)
            if cat_count < 1:
                st.error("There are no categories. Please, add a max of two categories.", icon="🚨")
            elif cat_count > 2:
                st.error("There are more than 2 categories. Please, limit it to one or two.", icon="🚨")
            else:
                st.success(f"There is a total of {cat_ucount} categories in this article. Perfect!", icon="✅")
            # except Exception as e:
            #     st.error("Error: Unable to analyze the URL. Please check that it's valid.") 

            st.subheader("Featured Image Size and Alt:") 
            # try:
                # get_url = requests.get(url)
                # soup = BeautifulSoup(get_url.text, "html.parser")                                 
                   
            width = get_featured_image_width(soup)
            alt = get_featured_image_alt(soup)
            if width is not None:
                if width >= 1200:
                    st.success(f"The featured image meets width requirements of at least 1200px wide: it is {width}px.\n\nThe Alt is: '{alt}'", icon="✅")
                else:
                    st.warning(f"Remember: feature image must be at least 1200px wide.\n\nThe current featured image is {width}px wide.\n\nThe Alt is: '{alt}'", icon="⚠️")            
            else:
                st.error("The article has no featured image. Please add one of a minimum of 1200px wide.", icon="🚨")              
            # except Exception as e:
            #     st.error("Error: Unable to analyze the URL. Please, check if it's valid.")   
            
            st.subheader("Images in content:")
            
            # sync
            get_url = ses.get(url, headers=headers)
            # get_url.html.render()
            # st.info(f"prueba{get_url}")
            soup = BeautifulSoup(get_url.text, "html.parser") 
            # st.info(f"prueba{soup}")

            img_count, alt_count, alt_list, ig_count, total = get_total_image_count(soup)
            
            if img_count <=1 and ig_count is not 0:
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
