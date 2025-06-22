from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Συνάρτηση που κάνει scraping από συγκεκριμένο URL του Market IN
def scrape_marketin(url):

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
        soup = BeautifulSoup(driver.page_source, "html.parser")

        # τιμή 
        try:
            price_tag = soup.find("span", id="finalPrice", class_="p-price")
            price_str = price_tag.text.strip() if price_tag else None
            price = float(price_str.replace("€", "").replace(",", ".")) if price_str else None
        except:
            price = None

        # τιμή ανά μονάδα 
        try:
            price_per_unit_tag = soup.find("div", id="ssfield4", class_="p-weight-price")
            price_per_unit = price_per_unit_tag.get_text(separator=" ", strip=True) if price_per_unit_tag else ""
        except:
            price_per_unit = ""

        # διατροφικά Στοιχεία
        try:
            nutr_div = soup.find("div", class_="nutritional-details")
            if nutr_div:
                # Παίρνω όλο το κείμενο (χωρίς τα <br> ως ξεχωριστά tags)
                nutritional_text = nutr_div.get_text(separator="\n", strip=True)
            else:
                nutritional_text = ""
        except:
            nutritional_text = ""

        # όλα τα στοιχεία
        return {
            "price_marketin": price,
            "price_per_unit_marketin": price_per_unit,
            "nutritional_info": nutritional_text,
            "scraped_from": ["marketin"] if price else []
        }

    except Exception as e:
        print("Σφάλμα κατά το scraping από το Market IN:", e)
        return None

    finally:
        driver.quit()
