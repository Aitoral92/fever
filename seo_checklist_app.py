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
                st.info(f"This is de URL:\n{url}")
                if hyphen_count > 3:
                    st.warning(f"The URL seems to be too long (it is {url_len} characters long), consider shorten it.", icon="⚠")
                else:
                    st.success(f"The URL looks fine in terms of length.", icon="✅")

                if has_digit:
                    st.warning("The URL doesn't seem very SEO friendly. Consider removing the number if it is not needed.", icon="⚠")
                else:
                    st.success(f"The URL is fine in terms of SEO friendliness.", icon="✅")
                
                st.subheader("SEO Title Length:")
                seot, lenseot = get_seo_title_length(soup)
                if lenseot < 50:
                    st.error(f"SEO title is BELOW 50 characters. It is {lenseot} characters long.\n\nSEO Title: '{seot}'", icon="🚨" )
                elif lenseot > 60:
                    st.error(f"SEO title is OVER 60 characters. It is {lenseot} characters long.\n\nSEO Title: '{seot}'", icon="🚨")
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
                total = art_ucount - cta_count
                if total <= 0:
                    st.error(f"There's no internal linking in the article. Please, add relevant key content articles as internal links.", icon="🚨")
                elif total >0 and art_count < 3:
                    st.warning(f"Please, consider adding more unique articles as internal links.\nThere is a total of {art_ucount} unique articles and a total of {art_count} URLs linked into this article.\n Here the links: {art_list}.", icon="⚠")
                else:
                    st.success(f"Internal linking nicely done!.\nThere is a total of {total} unique articles and a total of {art_count} URLs linked into this article.\n Here the links: {art_list}.", icon="✅")
      
                st.subheader("CTA Checker:")
                cta_count,cta_list = check_cta(soup)
                if cta_count > 0:
                    st.success(f"There is a CTA: {cta_list}", icon="✅")
                    st.info(f"That means that from the {art_ucount} links, one is the CTA.")
                    total=art_ucount-1
                    if total>1:
                        st.info(f"\nTotal amount of unique articles is {total}.")
                    elif total == 0:
                        st.error(f"There is no internal linking done in this article. Please, add internal linking throughout the content, linking to key content.", icon="🚨")
                    else:
                        st.warning(f"Total amount of unique articles is just {total}. Please, add more internal linking throughout the content", icon="⚠")
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
            except Exception as e:
                st.error("Error: Unable to analyze the URL. Please, check if it's valid.")
        else:
            st.warning("Please enter a valid URL.")

if __name__ == "__main__":
    main()
