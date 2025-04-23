import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from scripts import card_price_pagination, formatter
from collections import defaultdict

# Scrolls the webpage to the element we want to click on
def scroll_to_element(driver, element):
    driver.execute_script("arguments[0].scrollIntoView(true);", element)

    # Go 100 units further up to account for latency or sizing issues
    driver.execute_script("window.scrollBy(0, -100);") 

# Called whenever something needs to be interacted with
def click_element(driver, wait, element, scroll_y_n: bool):
    try:
        if scroll_y_n:
            # Scroll to the element to make sure it's in view
            scroll_to_element(driver, element)

        # Wait until the element is clickable
        wait.until(EC.element_to_be_clickable(element))

        # Perform the click
        element.click()
    except Exception as e:
        print(f"Error clicking element: {element}")

# Creates a progress bar as a string to append to messages
def progress_bar(iteration, total):
    total_squares = 20

    # A number from 0 to total_squares, for how many should be green
    progress = int((iteration / total) * total_squares)

    #These will always add up to 20 when combined
    green_squares = '🟩' * progress
    red_squares = '🟥' * (total_squares - progress)

    # Creates a string of green/red squares depending on how far through the iteration we are on
    progress_bar = f"Total Progress: **{(iteration / total) * 100:.2f}%**\n{green_squares}{red_squares}"
    return progress_bar

# Gets the data from TCG Player
async def pull_data_from_tcg_player(guild_id_as_int: int, message, card_name: str):
    # Check if input is correct
    if not formatter.check_valid_card_name(card_name):
        await message.edit(content=f"{card_name} is not a valid card name")
        return

    # Setup WebDriver, options taken from recommended FAQ
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
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

    # Inform the user that the driver has started
    await message.edit(content="Launching Selenium Web Driver For TCG Player")

    # Create the Driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Wait for initial load
    wait = WebDriverWait(driver, 5)  # Increase wait time

    # Go to the home page
    tcg_player_url = "https://www.tcgplayer.com/"
    driver.get(tcg_player_url)

    # Iterator for Progress Bar function
    num_printings = 0

    try:
        # Inform the user that we are now searching for the card
        await message.edit(content=f"Driver Launched, searching for **{formatter.smart_capitalize(card_name)}**")

        # Searches for the card
        await search_for_card(driver, wait, card_name, message)

        # Gets all the links for each individual printing of the card
        printings_links = []
        printings_links = await get_all_printings(driver, wait, card_name, message)

        # Used for the total value of the progress bar
        num_printings = len(printings_links)

        # Visit all the urls and get the listing information
        all_listings = []
        listing_number = 0
        for printing_url in printings_links:
            # Update the progress bar and Inform the user which archetype we are looking at
            progress_bar_message = progress_bar(listing_number, num_printings)

            # Retreive listings
            listing_data = await get_printing_information(driver, wait, printing_url, card_name, message)
            all_listings.append(listing_data)

            # Increment the iterator for the Progress Bar function
            listing_number += 1

            # Extract the printing name from the result
            printing_name = next(iter(listing_data))

            # Update the message with the progress bar and current printing
            await message.edit(content=f"Visiting listings for: \n\n\t**{formatter.smart_capitalize(printing_name)}**\n\n{progress_bar_message}")

        # Exit the Web Driver
        driver.quit()

        # Save the data to a JSON file
        with open(f"guilds/{guild_id_as_int}/json/card_price.json", "w", encoding="utf-8") as f:
            json.dump(all_listings, f, indent=2)
        
        await message.edit(content=f"Done collecting data")

        await card_price_pagination.show_card_listings(message, guild_id_as_int)

    # If the home page fails to load
    except Exception as e:
        await message.edit(content=f"Error with TCG Player")

# Inputs the card name and searches for the card
async def search_for_card(driver, wait, card_name, message):
    # Filters the search to yugioh cards
    await filter_By_YuGiOh(driver, wait, message)

    # click the input box
    input_box = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "input")))
    if input_box:
        click_element(driver, wait, input_box, True)
    else:
        await message.edit(content="Failed to find the input box for card search")

    # Type the card name
    input_box.clear()
    input_box.send_keys(card_name)
    input_box.send_keys(Keys.ENTER)

# Selects the Yugioh Filter from TCG Player search
async def filter_By_YuGiOh(driver, wait, message):
    # Find and click the dropdown
    dropdown = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "dropdown-container")))
    if dropdown:
        click_element(driver, wait, dropdown, True)
    else:
        await message.edit(content="Failed to find the dropdown box for filtering by franchise")

    # Find and save the container for list elements, then get the individual elements
    options_container = wait.until(EC.presence_of_element_located((By.ID, "drop-down-menu")))
    options = options_container.find_elements(By.TAG_NAME, "li")

    # Find the YuGiOh filter option
    target_option = None
    for option in options:
        # If its the yugioh filter, save the element and exit
        if "YuGiOh" in option.text:
            target_option = option
            break
        # If its not the yugioh filter, scroll down and keep going
        else:
            driver.execute_script("arguments[0].scrollIntoView(true);", option)

    # Click the option if found, click it
    if target_option:
        click_element(driver, wait, target_option, True)
    else:
        await message.edit(content="Failed to find the filter for YuGiOh")

# Gets all the valid urls for each printings of the card
async def get_all_printings(driver, wait, card_name, message):
    all_links = []
    card_name_lower = card_name.lower()

    # For every page,
    while True:
        # Try and read the page
        try:
            # Wait for results to load and save the result elements
            results_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-results")))
            result_elements = results_container.find_elements(By.CLASS_NAME, "search-result")
            
            # Filter the elements
            for result in result_elements:
                try:
                    # Get the name of the printing
                    title_element = result.find_element(By.CLASS_NAME, "product-card__title")
                    card_name_text = title_element.text.strip().lower()
                    if card_name_text == "":
                        card_name_text = formatter.smart_capitalize(card_name)

                    # Add to the list if the name is exactly the same or starts with exact name + " ("
                    if card_name_text == card_name_lower or card_name_text.startswith(card_name_lower + " ("):
                        link_element = result.find_element(By.TAG_NAME, "a")
                        href = link_element.get_attribute("href")
                        if href and href not in all_links:
                            all_links.append(href)
                
                except Exception as e:
                    print(f"Skipping one result due to error:")
            
            # Check if there are more pages
            try:
                # Find the next page icon within the button
                next_button = driver.find_element(By.CLASS_NAME, "fa-chevron-right")

                if next_button:
                    # Get the button element containing the icon
                    next_button_parent = next_button.find_element(By.XPATH, "./ancestor::a")
                else:
                    await message.edit(content="Failed to find the next button chevron for the results page")


                # Check if the button is disabled (on last page)
                if "disabled" in next_button_parent.get_attribute("class"):
                    # Stop looking for pages
                    break 

                if next_button_parent:
                    # If it's not disabled, move to the next page
                    click_element(driver, wait, next_button_parent, True)
                else:
                    await message.edit(content="Failed to find the next button for the results page")

                # Wait for the page to reload and the results to update
                wait.until(EC.staleness_of(result_elements[0]))

            except Exception as e:
                # Stop looking for pages if there is an error
                print(f"Error occurred detecting pages: {e}")
                break

        except Exception as e:
            # Stop if an error occurs in processing the page
            print(f"Error occurred while reading the page: {e}")
            break  

    # Return the urls of all relevant printings
    return all_links

# Gets the addtional information for that printing, as well as listing information
async def get_printing_information(driver, wait, printing_url, card_name, message):
    # Go to the printing url and wait for the page to load
    driver.get(printing_url)
    time.sleep(1)

    # Define the json object that will be returned
    results = defaultdict(list)

    # Define the array of listings
    all_listings = []

    # Get the printing name, and set a default if not found
    printing_name = card_name
    printing_name = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-details__name"))).text
    
    # Get the printing code and rarity elements
    printing_info_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product__item-details__attributes")))
    printing_info_elements = printing_info_container.find_elements(By.TAG_NAME, "li")
    
    printing_code = ""
    printing_rarity = ""

    # For every printing info element
    for element in printing_info_elements:
        try:
            # Check the field and set the appropriate text
            strong_text = element.find_element(By.TAG_NAME, "strong").text
            span_text = element.find_element(By.TAG_NAME, "span").text
            if (strong_text == "Number:"):
                printing_code = span_text
            elif (strong_text == "Rarity:"):
                printing_rarity = span_text
        except Exception as e:
            print(f"Skipping due to missing printing information")

    # Define the base json structure for this printing
    results[printing_name] = {
        "printing_url": printing_url,
        "printing_code": printing_code,
        "printing_rarity": printing_rarity
    }

    # Get 2 html elements, 1 for each edition of printing
    edition_filters = await initial_listing_filter(driver, wait, message)
    unlimited = edition_filters.get("unlimited")
    first_edition = edition_filters.get("first_edition")
    limited = edition_filters.get("limited")

    # Used for edition text within the results
    current_edition = ""

    # Check which options exist
    # if no options exist, then there are no current listings
    if not unlimited and not first_edition and not limited:
        return results
    # if both options exist, figure it out later
    elif unlimited and first_edition:
        # Run through unlimited printings first
        current_edition = "unlimited"

        # Make sure "First Edition" is unselected, and "Unlimited" is
        if "is-checked" in first_edition.get_attribute("class"):
            click_element(driver, wait, first_edition, False)
        if "is-checked" not in unlimited.get_attribute("class"):
            click_element(driver, wait, unlimited, False)

        # Save and exit the filter
        await save_filter(driver, wait, message)

        # Set the listings for unlimited printings
        results[printing_name][current_edition] = await get_listing_information(driver, wait, all_listings, message)
        all_listings = []

        # Reset the filter again to first edition
        filter_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "horizontal-filters-bar__filters__filters-button")))
        if filter_button:
            click_element(driver, wait, filter_button, False)
        else:
            await message.edit(content="Failed to find the filter button after finding the first 5 unlimited listings")


        # Make sure "Unlimited" is unselected, and "First Edition" is
        click_element(driver, wait, unlimited, False)
        time.sleep(0.5)
        if "is-checked" not in first_edition.get_attribute("class"):
            click_element(driver, wait, first_edition, False)

        current_edition = "first_edition"

        # Save and exit the filter
        await save_filter(driver, wait, message)
        driver.execute_script("window.scrollTo(0, 0);")

        # Set the listings for first edition printings
        results[printing_name][current_edition] = await get_listing_information(driver, wait, all_listings, message)
        
        # Return the complete printing information and listings
        return results
    
    # if 1 option exists, click it
    else:
        # Click unlimited
        if unlimited:
            current_edition = "unlimited"
            click_element(driver, wait, unlimited, False)
        # Or click first edition
        else:
            current_edition = "first_edition"
            click_element(driver, wait, first_edition, False)

        if limited:
            current_edition = "limited"
            click_element(driver, wait, limited, False)

        # Save and exit the filter
        await save_filter(driver, wait, message)

        # Set the listings for the current edition printing
        results[printing_name][current_edition] = await get_listing_information(driver, wait, all_listings, message)

        # Return the complete printing information and listings
        return results

# Set the initial filter, and return the printing edition elements
async def initial_listing_filter(driver, wait, message):
    # Find and click the "All filters" button
    filter_button = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "horizontal-filters-bar__filters__filters-button")))
    if filter_button:
        click_element(driver, wait, filter_button, False)
    else:
        await message.edit(content="Failed to find the dropdown box for filtering by franchise")
    
    # Find and click the "verified sellers" check box
    verified_sellers_check_box = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="verified-seller-filter"]')))

    if verified_sellers_check_box:
        verified_sellers_check_box_classes = verified_sellers_check_box.get_attribute("class")
    else:
        await message.edit(content="Failed to find the verified sellers check box container")

    if verified_sellers_check_box_classes:
        if "is-checked" not in verified_sellers_check_box_classes:
            click_element(driver, wait, verified_sellers_check_box, True)
    else:
        await message.edit(content="Failed to find the verified sellers check box")

    # Find the printing edition elements
    printing_edition_container = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "search-filter__facets__container")))

    # Gets the parent of the element that contains the following css
    try:
        printing_edition_element_unlimited = printing_edition_container.find_element(
            By.XPATH, ".//label[@for='Printing-Unlimited-filter']/.."
        )
    except NoSuchElementException:
        printing_edition_element_unlimited = None

    try:
        printing_edition_element_first_edition = printing_edition_container.find_element(
            By.XPATH, ".//label[@for='Printing-1stEdition-filter']/.."
        )
    except NoSuchElementException:
        printing_edition_element_first_edition = None

    try:
        printing_edition_element_limited = printing_edition_container.find_element(
            By.XPATH, ".//label[@for='Printing-Limited-filter']/.."
        )
    except NoSuchElementException:
        printing_edition_element_limited = None

    # Sets the printing edition elements
    edition_filters = {
        "unlimited": printing_edition_element_unlimited,
        "first_edition": printing_edition_element_first_edition,
        "limited": printing_edition_element_limited
    }

    # Returns the printing edition elements
    return edition_filters

# Save and exit the filter
async def save_filter(driver, wait, message):
    save_button = wait.until(EC.presence_of_element_located((
        By.CSS_SELECTOR, 
        ".tcg-button.tcg-button--md.tcg-standard-button.tcg-standard-button--priority.filter-drawer-footer__button-save"
    )))
    if save_button:
        click_element(driver, wait, save_button, False)
    else:
        await message.edit(content="Failed to find the save button for the filters")


# Gets the individual listing information for the edition
async def get_listing_information(driver, wait, all_listings, message):
    # For the listings
    while True:
        try:
            # Wait until at least one listing loads or timeout
            wait.until(lambda d: len(d.find_elements(By.CLASS_NAME, "listing-item")) > 0)
        except TimeoutException:
            return all_listings
        
        # Set the listings
        listing_elements = driver.find_elements(By.CLASS_NAME, "listing-item")

        # For every listing
        for listing in listing_elements:
            # Scroll to the element and save the information
            try:
                # If we already have 5 saved results, exit
                if len(all_listings) >= 5:
                    break

                # Scroll to the listing
                scroll_to_element(driver, listing)

                # Save the card condition
                condition = listing.find_element(By.CLASS_NAME, "listing-item__listing-data__info__condition").text

                # See if there is subtext, used to check if ocg
                try:
                    subtext_parent = listing.find_element(By.CLASS_NAME, "listing-item__listing-data__listo__title")
                    subtext = subtext_parent.find_element(By.XPATH, "./div").text
                except:
                    subtext = ""

                # If its in good enough condition, and not ocg, save it
                if "Lightly Played"in condition or "Near Mint"in condition and check_subtext(subtext):
                    vendor = listing.find_element(By.CLASS_NAME, "seller-info__name").text
                    rating_raw = listing.find_element(By.CLASS_NAME, "seller-info__rating").text.strip("%")
                    rating = float(rating_raw) if rating_raw else None
                    condition = listing.find_element(By.CLASS_NAME, "listing-item__listing-data__info__condition").text
                    card_price = listing.find_element(By.CLASS_NAME, "listing-item__listing-data__info__price").text

                    # Save the listing info
                    all_listings.append({
                        "vendor": vendor,
                        "rating": rating,
                        "condition": condition,
                        "card_price": card_price,
                    })

            except Exception as e:
                print(f"Error extracting listing")

        # If there aren't enough listings, look to go to the next page
        if len(all_listings) < 5:
            # Try to find the next page button
            next_button = driver.find_element(By.CLASS_NAME, "fa-chevron-right")
            if next_button:
                next_button_parent = next_button.find_element(By.XPATH, "./ancestor::a")  # Get the <a> ancestor
            else:
                await message.edit(content="Failed to find the next button chevron for listings")

            if next_button_parent:
                # Check if the button is disabled
                if "disabled" in next_button_parent.get_attribute("class"):
                    return all_listings

                # If it's not disabled, scroll and click to go to the next page
                click_element(driver, wait, next_button_parent, True)
            else:
                await message.edit(content="Failed to find the next button for listings")


            # Wait for the page to reload and continue on the next page
            wait.until(EC.staleness_of(listing_elements[0]))
        else:
            return all_listings
        
# Check if the printing is OCG, return false if found
def check_subtext(subtext: str):
    ocg_keywords = ["ocg", "asia", "asian", "korea", "korean", "japan", "japanese", "china", "chinese"]
    if any (word.lower() in subtext.lower() for word in ocg_keywords):
        return False
    return True
