import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
from openpyxl import load_workbook

# Base URL for Heathrow Boutique
BASE_URL = "https://boutique.heathrow.com"

# Define category names, URLs, and correct CGID values
CATEGORIES = {
    "fragrance": {
        "url": f"{BASE_URL}/en/shop/beauty/fragrance",
        "cgid": "beauty_fragrance",
    },
    "technology": {
        "url": f"{BASE_URL}/en/shop/technology",
        "cgid": "technology",
    },
    "spirits": {
        "url": f"{BASE_URL}/en/shop/food-and-drink/spirits",
        "cgid": "food_drink_wine_spirits",
    },
    "sunglasses": {
        "url": f"{BASE_URL}/en/shop/women/accessories/sunglasses",
        "cgid": "sunglasses_women",
    },
    "fashion-watches": {
        "url": f"{BASE_URL}/en/shop/jewellery-and-watches/fashion-watches",
        "cgid": "jewellery_fashion_watches",
    },
    "jewellery-and-watches": {
        "url": f"{BASE_URL}/en/shop/jewellery-and-watches",
        "cgid": "jewellery",
    },
    "make-up": {
        "url": f"{BASE_URL}/en/shop/beauty/make-up",
        "cgid": "beauty_make_up",
    },
    "confectionery": {
        "url": f"{BASE_URL}/en/shop/food-and-drink/food/confectionery",
        "cgid": "food_drink_confectionery",
    },
}

# Define pagination settings
PAGE_SIZE = 18  # Number of products per request
MAX_RETRIES = 5  # Number of times to retry failed requests
RETRY_DELAY = 2  # Initial delay in seconds (doubles each retry)

#-----------------------------Optional------------------------------------
# MAX_PRODUCTS = 200  Limit products to avoid excessive scraping(if needed)


def fetch_with_retries(url, headers):
    """Fetch a URL with retry logic."""
    attempt = 0
    while attempt < MAX_RETRIES:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response
        else:
            attempt += 1
            wait_time = RETRY_DELAY * (2 ** attempt)  # Exponential backoff
            print(f"Request failed (Attempt {attempt}/{MAX_RETRIES}). Retrying in {wait_time}s...")
            time.sleep(wait_time)
    print(f"Failed to fetch data after {MAX_RETRIES} retries. Skipping URL: {url}")
    return None


def scrape_category(category_name, category_info):
    """
    Scrapes product details for a given category from Heathrow's website.

    Parameters:
        category_name (str): Name of the category
        category_info (dict): Contains category URL and CGID value

    Returns:
        list: A list of dictionaries containing product details
    """
    print(f"----------------------------------------------------------------------------------------")
    print(f"Scraping category: {category_name} (CGID: {category_info['cgid']})")
    
    all_products = []
    start = 0  # Track pagination index

    while True:
        paginated_url = f"{BASE_URL}/en/update-search?cgid={category_info['cgid']}&start={start}&sz={PAGE_SIZE}"
        print(f"Fetching page: {paginated_url}")

        headers = {"User-Agent": "Mozilla/5.0"}
        response = fetch_with_retries(paginated_url, headers)

        if response is None:  
            break  # Stop scraping this category if request fails after retries

        soup = BeautifulSoup(response.text, "html.parser")
        products = soup.find_all("div", class_="product-tile")

        if not products:
            print("No more products found. Stopping pagination.")
            break  

        for product in products:
            name_tag = product.find("div", class_="pdp-link")
            product_name = name_tag.text.strip() if name_tag else "N/A"

            link_tag = product.find("a", href=True)
            product_url = BASE_URL + link_tag["href"] if link_tag else "N/A"

            img_tag = product.select_one(".image-container img.tile-image")
            product_image = img_tag["src"] if img_tag else "N/A"

            price_container = product.find("div", class_="price")
            discounted_price_tag = price_container.find("span", class_="sales value mr-1") if price_container else None
            discounted_price = discounted_price_tag.text.strip() if discounted_price_tag else "N/A"

            discount_tag = price_container.find("span", class_="you-save") if price_container else None
            discount_text = discount_tag.text.strip() if discount_tag else "N/A"

            you_save = 0.0
            if discount_text != "N/A":
                match = re.search(r"You save £([0-9,\.]+)", discount_text)
                if match:
                    you_save = float(match.group(1).replace(",", ""))

            try:
                if discounted_price != "N/A":
                    discounted_price_float = float(discounted_price.replace("£", "").replace(",", ""))
                    original_price = discounted_price_float + you_save
                else:
                    original_price_tag = price_container.find("span", class_="value-price") if price_container else None
                    original_price = float(original_price_tag["content"]) if original_price_tag else "N/A"
            except ValueError:
                original_price = "N/A"

            brand_tag = product.select_one("p.product-tile-brand")
            brand_name = brand_tag.text.strip() if brand_tag else "N/A"

            product_data = {
                "Product Name": product_name,
                "Product URL": product_url,
                "Product Image": product_image,
                "Original Price": f"£{original_price:.2f}" if isinstance(original_price, float) else "N/A",
                "Discounted Price": discounted_price,
                "Discount Info": discount_text,
                "You Save Amount": f"£{you_save:.2f}" if you_save > 0 else "N/A",
                "Brand Name": brand_name,
            }

            all_products.append(product_data)

        start += PAGE_SIZE
        time.sleep(1)

    return all_products


print("Starting the scraping process...")

all_data = {}

for category_name, category_info in CATEGORIES.items():
    products = scrape_category(category_name, category_info)
    if products:
        all_data[category_name] = pd.DataFrame(products)  

# Save the data in an Excel file
excel_filename = "scraped_products.xlsx"

try:
    book = load_workbook(excel_filename)
    with pd.ExcelWriter(excel_filename, engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
        for category, df in all_data.items():
            sheet_name = category.capitalize()[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)
except FileNotFoundError:
    with pd.ExcelWriter(excel_filename, engine="openpyxl") as writer:
        for category, df in all_data.items():
            sheet_name = category.capitalize()[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"Scraped data saved to {excel_filename}")
print(f"Total categories scraped: {len(all_data)}")
