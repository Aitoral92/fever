import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import Counter
from urllib.parse import urlparse

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
    all_content = soup.find("section", class_="article__body col-md-8")
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
    for a in all_content.find_all('a', href=True):
        cta_count += 1
        cta_list.append(a['href'])
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

def main():
    st.title("Web Page SEO Analyzer")
    url = st.text_input("Paste the URL:")

    if st.button("Analyze"):
        if url:
            try:
                get_url = requests.get(url)
                soup = BeautifulSoup(get_url.text, "html.parser")

                st.subheader("SEO Title Length:")
                seot, lenseot = get_seo_title_length(soup)
                if lenseot < 50:
                    st.error(f"SEO title '{seot}' is BELOW 50 characters. It is {lenseot} characters long.", icon="🚨" )
                elif lenseot > 60:
                    st.error(f"SEO title '{seot}' is OVER 60 characters. It is {lenseot} characters long.", icon="🚨")
                else:
                    st.success(f"SEO title '{seot}' is OPTIMIZED in length. It is {lenseot} characters long. Well done!", icon="✅")

                st.subheader("Meta Description Length:")
                metad, len_metad = get_meta_description_length(soup)
                if len_metad < 120:
                    st.error(f"Meta Description '{metad}' is BELOW 120 characters. It is {len_metad} characters long.", icon="🚨" )
                elif len_metad > 150:
                    st.error(f"Meta Description '{metad}' is OVER 150 characters. It is {len_metad} characters long.", icon="🚨" )
                else:
                    st.success(f"Meta Description '{metad}' is OPTIMIZED in length. It is {len_metad} characters long. Well done!", icon="✅")

                st.subheader("Secondary Title Length:")
                secondary, len_secondary = get_secondary_title_length(soup)
                if len_secondary < 120:
                    st.error(f"Secondary title '{secondary}' is BELOW 120 characters. It is {len_secondary} characters long.", icon="🚨")
                elif len_secondary > 180:
                    st.error(f"Secondary title '{secondary}' is OVER 180 characters. It is {len_secondary} characters long.", icon="🚨")
                else:
                    st.success(f"Secondary title '{secondary}' is OPTIMIZED in length. It is {len_secondary} characters long. Well done!", icon="✅")

                st.subheader("Internal Links:")
                art_ucount, art_count, art_list = get_internal_links_count(soup, url)
                cta_count,cta_list = check_cta(soup)
                if art_list[-1] == cta_list:
                    total=art_ucount-1
                    st.info(f"There is a total of {art_ucount} unique articles and a total of {art_count} URLs linked into this article.\nOne of those links is the CTA, so total amount of unique articles is {total}.")
                else:
                    st.error(f"There is no internal linking done in this article. Please, add nternal linking throughout the content, linking to key content).", icon="🚨")

                st.subheader("CTA Checker:")
                cta_count,cta_list = check_cta(soup)
                if cta_count > 0:
                    st.success(f"There is a CTA: {cta_list}", icon="✅")
                else:
                    st.error("There is not a CTA. Please add one evergreen key organic content as CTA.", icon="🚨")

                st.subheader("Categories Count:")
                cat_ucount, cat_count = get_categories_count(soup)
                if cat_count < 1:
                    st.error("There are no categories. Please, add a max of two categories.", icon="🚨")
                elif cat_count > 2:
                    st.error("There are more than 2 categories. Please, limit it to two.", icon="🚨")
                else:
                    st.success(f"There is a total of {cat_ucount} categories in this article. Perfect!", icon="✅")
            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please, check if it's valid.")
        else:
            st.warning("Please enter a valid URL.")

if __name__ == "__main__":
    main()
