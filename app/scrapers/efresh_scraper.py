from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Συνάρτηση που κάνει scraping από συγκεκριμένο URL του e-Fresh
def scrape_efresh(url):
    
    # Ορίζω τις επιλογές για τον Chrome browser χωρίς παράθυρο
    options = Options()
    options.add_argument("--headless")  
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument("--allow-running-insecure-content")

    # Εκκίνηση του Selenium Chrome driver
    driver = webdriver.Chrome(options=options)

    try:
        # Ανοίγω τη σελίδα του προϊόντος
        driver.get(url)
        time.sleep(2) 

        # Παίρνω όλο τον HTML κώδικα της σελίδας
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # τιμή
        try:
            price_tag = soup.find("span", class_="price")
            price_str = price_tag.text.strip() if price_tag else None
            price = float(price_str.replace("€", "").replace(",", ".")) if price_str else None
        except:
            price = None

        # τιμή ανά μονάδα
        price_per_unit_element = soup.select_one('span.price-per-unit')
        if price_per_unit_element:
            price_per_unit = price_per_unit_element.get_text(strip=True)
        else:
            price_per_unit = ""

        # περιγραφή
        try:
            # Προσπαθώ πρώτα να βρω τη βασική περιγραφή
            desc_div = soup.find("div", class_="description")

            if desc_div:
                # Παίρνω όλο το κείμενο ακόμα και αν έχει nested tags
                description = desc_div.get_text(separator=" ", strip=True)
            else:
                # Αν δεν βρω, προσπαθώ σε εναλλακτική θέση
                desc_alt = soup.find("div", class_="description-full")
                if desc_alt:
                    description = desc_alt.get_text(separator=" ", strip=True)
                else:
                    description = ""
        except:
            description = ""

        # URL της εικόνας
        try:
            image_div = soup.find("div", class_="img normal")
            style_attr = image_div["style"]
            image_url = style_attr.split('url("')[1].split('")')[0]
        except:
            image_url = None

        # όλα τα στοιχεία
        return {
            "price_efresh": price,
            "price_per_unit": price_per_unit,
            "description": description,
            "image_url": image_url,
            "scraped_from": ["efresh"] if price else []
        }

    except Exception as e:
        print("Σφάλμα κατά το scraping:", e)
        return None

    finally:
        driver.quit()  # Κλείνω το πρόγραμμα του browser
