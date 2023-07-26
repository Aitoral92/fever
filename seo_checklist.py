# %%
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from collections import Counter

# %% [markdown]
# ### URL to Check

# %%
url = input("Paste the URL: ")

# %% [markdown]
# ### H1 length

# %%
get_url = requests.get(url)
get_text = get_url.text
soup = BeautifulSoup(get_text, "html.parser")

h1 = soup.find_all('h1')[0].text.strip()
lenh1 = len(h1)
if lenh1< 50:
    print("Length of SEO title '{}'\nis BELOW 50 characters. Is {} long.".format(h1, lenh1))
elif lenh1 > 60:
    print("Length of SEO title '{}'\nis OVER 60 characters. Is {} long.".format(h1, lenh1))
else:
    print("Length of SEO title '{}'\nis OPTIMIZED in length. Is {} long. Well done!".format(h1, lenh1))

# %% [markdown]
# ### Meta Description

# %%
get_url = requests.get(url)
get_text = get_url.text
soup = BeautifulSoup(get_text, "html.parser")

metad = soup.find("meta", property="og:description")
len_metad = len(metad["content"] if metad else "No meta title given")

if len_metad < 120:
    print("Length of Meta Description '{}'\nis BELOW 120 characters. Is {} long.".format(metad["content"], len_metad))
elif len_metad > 150:
    print("Length of Meta Description '{}'\nis OVER 150 characters. Is {} long.".format(metad["content"], len_metad))
else:
    print("Length of Meta Description '{}'\nis OPTIMIZED in length. Is {} long. Well done!".format(metad["content"], len_metad))

# print(metad)
# print(len_metad)

# %% [markdown]
# ### Secondary Length

# %%
get_url = requests.get(url)
get_text = get_url.text
soup = BeautifulSoup(get_text, "html.parser")

secondary = soup.find("p", class_="single__subtitle")
lensecon = len(secondary.text)

if lensecon< 120:
    print("Length of Secondary title '{}'\nis BELOW 120 characters. Is {} long.".format(secondary.text, lensecon))
elif lensecon > 180:
    print("Length of Secondary title '{}'\nis OVER 180 characters. Is {} long.".format(secondary.text, lensecon))
else:
    print("Length of Secondary title '{}'\nis OPTIMIZED in length. Is {} long. Well done!".format(secondary.text, lensecon))


# %% [markdown]
# ### Finding and counting all internal links

# %%
get_url = requests.get(url)
get_text = get_url.text
soup = BeautifulSoup(get_text, "html.parser")

all_content = soup.find("section", class_="article__body col-md-8")

art_count = 0
art_list = []
for a in all_content.find_all('a', href=True):
    art_count +=1
    art_list.append(a['href'])
    # print ("Found a URL:", a['href'])

art_ucount = Counter(art_list).keys()

print("\nThere is a total of {} unique articles and a total of {} linked into this article".format(len(art_ucount),art_count))


# %% [markdown]
# ### Counting categories

# %%
get_url = requests.get(url)
get_text = get_url.text
soup = BeautifulSoup(get_text, "html.parser")

all_content = soup.find("div", class_="post-list-view-home__category-wrapper")

cat_count = 0
cat_list = []
for a in all_content.find_all('a', href=True):
    cat_count +=1
    cat_list.append(a['href'])
    # print ("Found a URL:", a['href'])

cat_ucount = Counter(cat_list).keys()

if cat_count< 1:
    print("There is no categories. Please, add a max of two categories.")
elif cat_count > 2:
    print("There are more than 2 categories. Please, limit it to two.")
else:
    print("\nThere is a total of {} categories this article. Perfect!".format(len(cat_ucount)))




