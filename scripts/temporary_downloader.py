import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from urllib.parse import urljoin
import os
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

async def download_images():

    # Setup WebDriver, options taken from recommended FAQ
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")  # May help on some systems
    options.add_argument("--disable-software-rasterizer")  # Prevents software fallback for WebGL
    options.add_argument("--window-size=1920,1080")  # Set a standard window size
    options.add_argument("--no-sandbox")  # Useful for running in some environments
    options.add_argument("--disable-dev-shm-usage")  # Helps prevent crashes
    options.add_argument("--use-gl=swiftshader") # Addresses "fallback to swftware WebGL depricated" errors
    options.add_argument("--ignore-certificate-errors") # Addresses "handshake failed" errors
    options.add_argument("--disable-features=SSLVersionMin") # Addresses "handshake failed" errors
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) "
                     "Chrome/120.0.0.0 Safari/537.36")

    # Create the Driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Target URL (where the images are hosted)
    url = "https://tiermaker.com/create/yu-gi-oh-master-duel-secret-pack-list-1564997"  # Change this to the URL you're working with
    driver.get(url)

    # Wait for the page to load completely (you can adjust the sleep time or use WebDriverWait)
    time.sleep(3)

    # Get all image elements
    img_elements = driver.find_elements(By.TAG_NAME, "img")

    # Create a directory to save the images
    os.makedirs("global/images/secret_pack_images", exist_ok=True)

    # Download all images
    for img in img_elements:
        img_url = img.get_attribute("src")  # This gets the URL of the image
        
        if img_url:  # Skip if no image URL
            img_url = urljoin(url, img_url)  # Resolve relative URLs

            # Extract the image filename
            img_name = os.path.basename(img_url)
            
            # Download the image
            try:
                img_data = requests.get(img_url).content
                with open(f"global/images/secret_pack_images/{img_name}", "wb") as f:
                    f.write(img_data)
                print(f"Downloaded: {img_name}")
            except Exception as e:
                print(f"Failed to download {img_url}: {e}")

    # Close the browser once done
    driver.quit()
