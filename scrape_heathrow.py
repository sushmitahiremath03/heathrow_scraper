import requests
from bs4 import BeautifulSoup
import time
import pandas as pd

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

# Define limits and pagination settings
MAX_PRODUCTS = 200  # Limit products to avoid excessive scraping(if needed)
PAGE_SIZE = 18  # Number of products per request

def scrape_category(category_name, category_info):
    """
    Scrapes product details for a given category from Heathrow's website.

    Parameters:
        category_name (str): Name of the category
        category_info (dict): Contains category URL and CGID value

    Returns:
        list: A list of dictionaries containing product details
    """
    print(f"Scraping category: {category_name} (CGID: {category_info['cgid']})")

    all_products = []
    start = 0  # Track pagination index

    while len(all_products) < MAX_PRODUCTS:
        # Construct paginated URL to fetch product listings dynamically
        paginated_url = f"{BASE_URL}/en/update-search?cgid={category_info['cgid']}&start={start}&sz={PAGE_SIZE}"
        print(f"Fetching page: {paginated_url}")

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(paginated_url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to fetch data for {category_name}. HTTP Status Code: {response.status_code}")
            break  # Stop scraping this category if request fails

        soup = BeautifulSoup(response.text, "html.parser")
        products = soup.find_all("div", class_="product-tile")

        if not products:
            print("No more products found. Stopping pagination.")
            break  # Stop if no products are available

        # Extract product details from each product tile
        for product in products:
            name_tag = product.find("div", class_="pdp-link")
            product_name = name_tag.text.strip() if name_tag else "N/A"

            link_tag = product.find("a", href=True)
            product_url = BASE_URL + link_tag["href"] if link_tag else "N/A"

            img_tag = product.select_one(".image-container img.tile-image")
            product_image = img_tag["src"] if img_tag else "N/A"

            price_container = product.find("div", class_="price")
            original_price_tag = price_container.find("span", class_="value-price") if price_container else None
            original_price = original_price_tag["content"] if original_price_tag else "N/A"

            discounted_price_tag = price_container.find("span", class_="sales value mr-1") if price_container else None
            discounted_price = discounted_price_tag.text.strip() if discounted_price_tag else "N/A"


            discount_tag = price_container.find("span", class_="you-save") if price_container else None
            discount_text = discount_tag.text.strip() if discount_tag else "N/A"

            brand_tag = product.select_one("p.product-tile-brand")
            brand_name = brand_tag.text.strip() if brand_tag else "N/A"

            product_data = {
                "Product Name": product_name,
                "Product URL": product_url,
                "Product Image": product_image,
                "Original Price": original_price,
                "Discounted Price": discounted_price,
                "Discount Info": discount_text,
                "Brand Name": brand_name,
            }

            all_products.append(product_data)

            # Stop if the max limit is reached
            if len(all_products) >= MAX_PRODUCTS:
                break

        # Move to the next set of products
        start += PAGE_SIZE
        time.sleep(1)  # Add delay to prevent overwhelming the server

    return all_products

print("Starting the scraping process...")

all_data = {}

# Scrape each category and store data in a dictionary
for category_name, category_info in CATEGORIES.items():
    products = scrape_category(category_name, category_info)
    if products:
        all_data[category_name] = pd.DataFrame(products)  # Convert to DataFrame

# Save the data in an Excel file with separate sheets for each category
excel_filename = "scraped_products.xlsx"

try:
    # Append data to an existing Excel file if it exists
    with pd.ExcelWriter(excel_filename, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
        for category, df in all_data.items():
            sheet_name = category.capitalize()[:31]  # Sheet names have a max length of 31 characters
            existing_sheet = writer.sheets.get(sheet_name)  # Check if sheet exists

            # Append data below existing rows
            startrow = existing_sheet.max_row if existing_sheet else 0
            df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=startrow)
except FileNotFoundError:
    # Create a new file if it does not exist
    with pd.ExcelWriter(excel_filename, engine="openpyxl") as writer:
        for category, df in all_data.items():
            sheet_name = category.capitalize()[:31]
            df.to_excel(writer, sheet_name=sheet_name, index=False)

print(f"Scraped data saved to {excel_filename}")
print(f"Total categories scraped: {len(all_data)}")

