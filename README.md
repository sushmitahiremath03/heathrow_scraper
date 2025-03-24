# Duty-Free Scraper

This project is a web scraper for extracting product details from an online duty-free shopping website.

## Features
- Scrapes product names, prices, discounts, and images.
- Handles pagination dynamically.
- Saves data in a structured format.

## Requirements
- Python 3.x
- BeautifulSoup
- Requests
- Pandas (if saving data to CSV)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sushmitahiremath03/heathrow_scraper.git
   ```
2. Navigate to the project directory:
   ```bash
   cd heathrow_scraper
   ```
3. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   ```
4. Activate the virtual environment:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
5. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
6. Run the scraper:
   ```bash
   python scrape.py
   
