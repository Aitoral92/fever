import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import Counter
from urllib.parse import urlparse

def count_hyphens_and_digits_in_url(url):
    hyphen_count = url.count("-")
    has_digit = any(char.isdigit() for char in url)
    url_len = len(url)
    return hyphen_count, has_digit, url_len

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
            art_count += 1
            art_list.append(link)

    art_ucount = len(set(art_list))
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

# def check_featured_image(soup):
#     ft_img = soup.find("meta", property="og:image")
#     if ft_img and 'content' in ft_img.attrs:
#         st.subheader("Featured Image Check:")
#         st.write("El artículo tiene una imagen destacada.")
        
#         ft_img_width = soup.find("meta", property="og:image:width")
#         if ft_img_width and 'content' in ft_img_width.attrs:
#             image_width = int(ft_img_width['content'])
#             if image_width >= 1200:
#                 st.success("La imagen es del tamaño adecuado: {}px".format(image_width))
#             else:
#                 st.error("La imagen destacada es de {}px de ancho y debe tener un mínimo de 1200px.".format(image_width))
#         else:
#             st.warning("No se encontró el ancho de la imagen en la etiqueta og:image:width.")
#     else:
#         st.subheader("Featured Image Check:")
#         st.warning("No hay ninguna imagen destacada. Por favor, añade una.")

# def check_alt_attribute(soup):
#     all_content = soup.find("section", class_="article__body col-md-8")
#     alt_text = all_content.find("img", alt=True)
#     if alt_text:
#         st.subheader("Alt Attribute Check:")
#         st.write("El atributo alt de la imagen es: {}".format(alt_text["alt"]))
#     else:
#         st.subheader("Alt Attribute Check:")
#         st.error("La imagen no tiene atributo Alt. Añádele un alt.")

# def count_normal_images(soup):
#     all_content = soup.find("section", class_="article__body col-md-8")
#     img_count = 0
#     alt_count = 0
#     alt_list = []
#     for img in all_content.find_all('img', alt=True):
#         # Verificar si la etiqueta 'img' tiene la clase "emoji" o está dentro de <noscript></noscript>
#         if "emoji" in img.get("class", []) or img.find_parent("noscript"):
#             continue  # Ignorar esta etiqueta 'img' y pasar a la siguiente

#         img_count += 1
#         if len(img["alt"]) > 0:
#             alt_count += 1
#             alt_list.append(img["alt"])
#     st.subheader("Normal Images Check:")
#     st.write("Hay un total de {} imágenes normales, de las cuales {} tienen atributo alt.".format(img_count, alt_count))
#     st.write("Estos son los alts:")
#     for alt in alt_list:
#         st.write("- " + alt)

# def count_embedded_images(soup):
#     all_content = soup.find("section", class_="article__body col-md-8")
#     ig_count = 0
#     for img in all_content.find_all('blockquote', class_=True):
#         ig_count += 1
#     st.subheader("Embedded Instagram Images Check:")
#     st.write("Hay un total de {} imágenes embedadas de IG".format(ig_count))

def get_featured_image_width(soup):
    ft_img_width = soup.find("meta", property="og:image:width")
    if ft_img_width and 'content' in ft_img_width.attrs:
        return int(ft_img_width['content'])
    else:
        return None

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
    st.title("Web Page SEO Analyzer")
    url = st.text_input("Paste the URL:")

    if st.button("Analyze"):
        if url:
            try:
                get_url = requests.get(url)
                soup = BeautifulSoup(get_url.text, "html.parser")

                st.subheader("URL friendliness")
                hyphen_count, has_digit, url_len = count_hyphens_and_digits_in_url(url)
                st.info(f"This is de URL:\n{url}", icon="👀")
                if hyphen_count > 3:
                    st.warning(f"The URL seems to be too long (it is {url_len} characters long), consider shorten it.", icon="⚠️")
                else:
                    st.success(f"The URL looks fine in terms of length.", icon="✅")

                if has_digit:
                    st.warning("The URL doesn't seem very SEO friendly. Consider removing the number if it is not needed.", icon="⚠️")
                else:
                    st.success(f"The URL is fine in terms of SEO friendliness.", icon="✅")
                
                st.subheader("SEO Title Length:")
                seot, lenseot = get_seo_title_length(soup)
                if lenseot < 50:
                    st.error(f"SEO title is BELOW 50 characters. It is {lenseot} characters long.\n\nSEO Title: '{seot}'", icon="🚨" )
                elif lenseot > 60:
                    st.error(f"SEO title is OVER 60 characters. It is {lenseot} characters long.\n\nSEO Title: '{seot}'", icon="🚨")
                    st.warning(f"If this is a 'News' kind of article and not an Evergreen/Roundup, the SEO Title can be longer for editorial purposes", icon="⚠️")
                else:
                    st.success(f"SEO title is OPTIMIZED in length. It is {lenseot} characters long. Well done!\n\nSEO Title: '{seot}'", icon="✅")

                st.subheader("Meta Description Length:")
                metad, len_metad = get_meta_description_length(soup)
                if len_metad < 120:
                    st.error(f"Meta Description is BELOW 120 characters. It is {len_metad} characters long.\n\nMeta Description: '{metad}'", icon="🚨" )
                elif len_metad > 150:
                    st.error(f"Meta Description is OVER 150 characters. It is {len_metad} characters long.\n\nMeta Description: '{metad}'", icon="🚨" )
                else:
                    st.success(f"Meta Description is OPTIMIZED in length. It is {len_metad} characters long. Well done!\n\n Meta Description: '{metad}'", icon="✅")

                st.subheader("Secondary Title Length:")
                secondary, len_secondary = get_secondary_title_length(soup)
                if len_secondary < 120:
                    st.error(f"Secondary title is BELOW 120 characters. It is {len_secondary} characters long.\n\nSecondary Title:'{secondary}'", icon="🚨")
                elif len_secondary > 180:
                    st.error(f"Secondary title is OVER 180 characters. It is {len_secondary} characters long.\n\nSecondary Title:'{secondary}'", icon="🚨")
                else:
                    st.success(f"Secondary title is OPTIMIZED in length. It is {len_secondary} characters long. Well done!\n\nSecondary Title:'{secondary}'", icon="✅")

                st.subheader("Internal Links:")
                art_ucount, art_count, art_list = get_internal_links_count(soup, url)
                cta_count,cta_list = check_cta(soup)
                if cta_count is not 0:
                    total = art_ucount - cta_count
                    if total <= 0:
                        st.error(f"There's no internal linking in the article. Please, add relevant key content articles as internal links.", icon="🚨")
                    elif total >0 and total < 3:
                        st.warning(f"Please, consider adding more unique articles as internal links.\n\n There is a total of {total} unique articles and a total of {art_count} URLs (one being the CTA) linked into this article.\n\n Here are the links: {art_list}.", icon="⚠️")
                    else:
                        st.success(f"Internal linking nicely done!.\nThere is a total of {total} no CTA unique articles in the content and a total of {art_count} URLs linked into this article.\n Here the links: {art_list}.", icon="✅")                
                else:
                    if art_ucount < 1:
                        st.error(f"There's no internal linking in the article. Please, add relevant key content articles as internal links.", icon="🚨")
                    elif art_ucount > 0 and art_ucount < 3:
                        st.warning(f"Please, consider adding more unique articles as internal links.\n\n There is a total of {art_ucount} unique articles and a total of {art_count} URLs linked into this article.\n\n Here the links: {art_list}.", icon="⚠️")
                    else:
                        st.success(f"Internal linking nicely done!.\nThere is a total of {total} unique articles and a total of {art_count} URLs linked into this article.\n Here the links: {art_list}.", icon="✅")
      
                st.subheader("CTA Checker:")
                cta_count,cta_list = check_cta(soup)
                if cta_count > 0:
                    st.success(f"There is a CTA: {cta_list}", icon="✅")
                    st.info(f"That means that from the {art_ucount} links, one is the CTA.", icon="👀")
                    total=art_ucount-1
                    if total>1:
                        st.info(f"\nTotal amount of unique articles is {total}.", icon="👀")
                    elif total == 0:
                        st.error(f"There is no internal linking done in this article. Please, add internal linking throughout the content, linking to key content.", icon="🚨")
                    else:
                        st.warning(f"Total amount of unique articles is just {total}. Please, add more internal linking throughout the content", icon="⚠️")
                else:
                    st.error("There is no CTA. Please add one evergreen key organic content as CTA.", icon="🚨")
                
                st.subheader("Categories Count:")
                cat_ucount, cat_count = get_categories_count(soup)
                if cat_count < 1:
                    st.error("There are no categories. Please, add a max of two categories.", icon="🚨")
                elif cat_count > 2:
                    st.error("There are more than 2 categories. Please, limit it to one or two.", icon="🚨")
                else:
                    st.success(f"There is a total of {cat_ucount} categories in this article. Perfect!", icon="✅")
                
                st.subheader("Featured Image Size and Alt:")                
                width = get_featured_image_width(soup)
                alt = get_featured_image_alt(soup)
                if width is not None:
                    if width >= 1200:
                        st.success(f"The featured image meets width requirements: {width}px.\n\nThe Alt is: '{alt}'", icon="✅")
                    else:
                        st.warning(f"Remember: feature image must be at least 1200px wide.\n\nThe current featured image is {width}px wide.\n\nThe Alt is: '{alt}'", icon="⚠️")            
                else:
                    st.error("The article has no featured image. Please add one of a minimum of 1200px wide.", icon="🚨")              

                st.subheader("Images in content:")
                img_count, alt_count, alt_list, ig_count, total = get_total_image_count(soup)
                
                if ig_count is not 0 and img_count <=1:
                    st.error(f"All the images (except for the featured one) are Instagram embededs. Please, add real images instead.", icon="🚨")

                    
                if img_count <= 1:
                    st.error(f"There is no images thoughout the article besides the featured one. Please, add images.", icon="🚨")
                elif ig_count is 0:
                    if alt_count == img_count:
                        st.success(f"There is a total of {img_count} images, from which all of them have an alt.\n\nThis are the alts:{alt_list}", icon="✅")
                    else:
                        st.warning(f"There is a total of {img_count} images, from which {img_count-alt_count} have no alt.\n\nPlease, add an Alt to the images.", icon="⚠️")
                else:
                    st.warning(f"There is a total of {total} images, from which {ig_count} are embeded from Instagram. Please, try not to use embeded images.", icon="⚠️")
                    st.warning(f"From those {total} images, {img_count-alt_count} have no alt. Please, add an alt to the images.", icon="⚠️")


            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please, check if it's valid.")
        else:
            st.warning("Please enter a valid URL.")

if __name__ == "__main__":
    main()
