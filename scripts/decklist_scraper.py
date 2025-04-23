import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from scripts import formatter

# Writes data to a file
def save_progress(archetype_data):
    with open("global/json/topping_decklists.json", "w") as f:
        json.dump(archetype_data, f, indent=4)

# Scrolls the webpage to the element we want to click on
def scroll_to_element(driver, element):
    driver.execute_script("arguments[0].scrollIntoView(true);", element)

    # Go 100 units further up to account for latency or sizing issues
    driver.execute_script("window.scrollBy(0, -100);") 

# Called whenever something needs to be interacted with
def click_element(driver, wait, element):
    try:
        # Scroll to the element to make sure it's in view
        scroll_to_element(driver, element)

        # Wait until the element is clickable
        wait.until(EC.element_to_be_clickable(element))

        # Perform the click
        element.click()

    except Exception as e:
        print(f"Error clicking element: {e}")
        return False
    return True

# Gets the data from YGOPro.com
async def pull_data_from_ygo_pro(message):
    # Get the latest database of cards
    with open('global/json/full_database.json', 'r', encoding="utf-8") as file:
        full_database = json.load(file)

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


    
    # Inform the user that the driver has started
    await message.edit(content="Launching Selenium Web Driver For YGO Pro...")  # Edit the message sent earlier

    # Create the Driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    # Wait for initial load
    wait = WebDriverWait(driver, 10)  # Increase wait time

    # Go to the Top Archetypes page
    url = "https://ygoprodeck.com/tournaments/top-archetypes/"
    driver.get(url)

    # Setup archetype JSON
    archetype_data = {}
    all_deck_links = []

    # Iterator for Progress Bar function
    archetype_number = 0

    try:
        # Inform the user that we are now searching for all archetypes
        await message.edit(content="Driver Launched, Obtaining list of Topping Archetypes...")

        # Get all the archetypes on the page
        archetype_html_elements = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "arch-item")))

        # Get the total amount of archetypes to use in the progress bar later
        total_archetypes = len(archetype_html_elements)
        total_archetypes_message = f"Total Archetypes: **{total_archetypes}**"

        # For every archetype on the page
        for archetype in archetype_html_elements:
            try:
                # Counter for progress through the array, to be sent to the progress bar function
                archetype_number +=1

                # Get the archetype name and percentage
                archetype_name = (archetype.find_element(By.CLASS_NAME, "arch-name")).text.strip()
                archetype_percentage = (archetype.find_element(By.CLASS_NAME, "arch-sub")).text.strip()

                # Define archetype structure in the JSON
                archetype_data[archetype_name] = {
                    "percentage": archetype_percentage,
                    "decks": {}
                }

                # Build initial sentence structure for informing the user on current progress
                archetype_message = "Finding all decklists for:"
                archetype_message += f" **{archetype_name}**"

                # Update the progress bar and add it to the message
                progress_bar_message = progress_bar(archetype_number, total_archetypes)

                # Inform the user which archetype we are currently looking at, and how many archetypes have been completed
                await message.edit(content=f"{total_archetypes_message}\n\n{archetype_message}\n\n{progress_bar_message}")

                # Scroll to the archetype and click it
                if not click_element(driver, wait, archetype):
                    # Skip to the next archetype if this one couldn't be clicked
                    continue  

                # Wait for the page to load
                wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a.deck_article-card-title")))

                # Extract all the decklist URLs into a set to prevent duplicates
                deck_links = set()
                deck_elements = driver.find_elements(By.CSS_SELECTOR, "a.deck_article-card-title")

                # For every decklist, if the url exists, add it to the set
                for deck_list in deck_elements:
                    deck_url = deck_list.get_attribute("href")
                    if deck_url:
                        deck_links.add(deck_url)
                    else:
                        print(f"Skipping deck without URL in {archetype_name}.")

                # If there are any deck links for this archetype, add it to the json
                if deck_links:
                    all_deck_links.append((archetype_name, deck_links))
                else:
                    print(f"No deck URLs found for {archetype_name}, skipping this archetype.")

            except Exception as e:
                await message.edit(content=f"Error processing: **{archetype}**: {e}")
                print(f"Error processing archetype {archetype}: {e}")
                # Skip this archetype and move on to the next
                continue  
    except Exception as e:
        await message.edit(content=f"Error loading archetype page: {e}")
        print(f"Error loading archetype page: {e}")

    # Calculate the total number of decks by iterating through the Tuple, and create the initial message
    total_decks = sum(len(deck_links) for _, deck_links in all_deck_links)
    total_decks_message = f"Found **{total_decks}** unique deck lists"
    await message.edit(content=total_decks_message)

    # Iterator for Progress Bar function
    deck_number = 0

    # For every archetype, look at the deck url
    for archetype_name, deck_links in all_deck_links:
        # For every deck url, visit all the deck links and extract data
        for deck_url in deck_links:
            # Increment the iterator for the Progress Bar function
            deck_number += 1

            # Update the progress bar and Inform the user which archetype we are looking at
            progress_bar_message = progress_bar(deck_number, total_decks)
            await message.edit(content=f"{total_decks_message}\n\n Visiting deck lists for: **{archetype_name}**\n\n{progress_bar_message}")

            try:
                # Visit the deck URL and wait for the page to load
                driver.get(deck_url)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))  

                # Extract data from public variables, and html values
                main_deck = driver.execute_script("return maindeckjs;")
                extra_deck = driver.execute_script("return extradeckjs;")
                side_deck = driver.execute_script("return sidedeckjs;")
                deck_name = driver.execute_script("return deckname;")
                deck_id = driver.execute_script("return deckid;")
                archetypes = driver.execute_script("return chart1;")
                main_deck_count = driver.execute_script("return maindeckcount;")
                total_price = driver.execute_script("return jQuery('a[title=\"Deck Price (TCGplayer)\"]').text();")
                placement = driver.execute_script("return jQuery('.deck-metadata-child:first-of-type b:first-of-type').text();")

                #Convert deck string of ids, into an array of names
                main_deck_ids = json.loads(main_deck)
                main_deck_names = [formatter.assign_single_card_by_id(int(card_id), full_database) for card_id in main_deck_ids]
                extra_deck_ids = json.loads(extra_deck)
                extra_deck_names = [formatter.assign_single_card_by_id(int(card_id), full_database) for card_id in extra_deck_ids]
                side_deck_ids = json.loads(side_deck)
                side_deck_names = [formatter.assign_single_card_by_id(int(card_id), full_database) for card_id in side_deck_ids]

                # Store deck data, using name and ID to make a unique key
                archetype_data[archetype_name]["decks"][f"{deck_name}-{deck_id}"] = {
                    "deck_url": deck_url,
                    "deck_name": deck_name,
                    "deck_id": deck_id,
                    "total_price": total_price,
                    "placement": placement,
                    "main_deck_count": main_deck_count,
                    "deck_list": {
                        "main_deck": main_deck_names,
                        "extra_deck": extra_deck_names,
                        "side_deck": side_deck_names,
                    },
                    "archetypes": archetypes,
                }

                # Write the results to a file after processing each deck
                save_progress(archetype_data)

            except Exception as e:
                await message.edit(content=f"Error extracting data for {deck_url}: {e}")
                print(f"Error extracting data for {deck_url}: {e}")
                # Skip this deck and move on to the next
                continue  

    # Final save when done
    save_progress(archetype_data)

    # Inform the user the process is done
    await message.edit(content="Complete! All data has been updated")

    # Close WebDriver
    driver.quit()

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