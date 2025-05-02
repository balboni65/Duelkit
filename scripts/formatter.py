import json
import re
import discord
import aiohttp
import os
from scripts import decklist_scraper
from datetime import datetime

# Calls all functions in the file to update all json files
async def update(interaction: discord.Interaction):
    # Creates the file path if it doesn't exist
    os.makedirs("global/json", exist_ok=True)
    
    # Defer the response so multiple processes can use its webhook
    await interaction.response.defer(thinking=True)

    message = await interaction.followup.send("Updating full card database...")
    await retrieve_full_database(message)

    await message.edit(content="Creating Monster databases...")
    format_monsters()

    await message.edit(content="Creating Names database for autocompletion...")
    format_names()

    await message.edit(content="Creating Names and Set Codes database for autocompletion...")
    format_names_and_set_codes()

    await message.edit(content="Beginning to update all topping decklists...")
    await decklist_scraper.pull_data_from_ygo_pro(message)

# retrieves the full card database from Konami's API
async def retrieve_full_database(message):
    # Konami card database API URL
    url = "https://db.ygoprodeck.com/api/v7/cardinfo.php"

    # Try to access Konami's card database API
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                # Check if the response was successful
                if response.status != 200:
                    await message.edit(content=f"Failed to fetch data. Status code: {response.status}")
                    return
                data = await response.json()

        # Save the data to a JSON file
        with open("global/json/full_database.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        await message.edit(content="Card database successfully saved.")

    # Error Handling
    except aiohttp.ClientError as e:
        await message.edit(content=f"Network error while fetching cards: {e}")
    except json.JSONDecodeError as e:
        await message.edit(content=f"Error decoding JSON: {e}")
    except Exception as e:
        await message.edit(content=f"An unexpected error occurred: {e}")

# Formats the monster_database.json file
def format_monsters():
    # Get the latest database of cards
    with open('global/json/full_database.json', 'r', encoding="utf-8") as file:
        full_database = json.load(file)

    all_monsters = []
    main_monsters = []
    
    # Seventh Tachyon numbers
    xyz_numbers = ['101', '102', '103', '104', '105', '106', '107']
    seventh_tachyon_targets = []

    # Filter to just monsters and specific fields
    for card in full_database["data"]:
        # If its a monster, store its data
        if "Monster" in card["type"]:
            monster_data = {
                "id": card["id"],
                "name": card["name"],
                "type": card["type"],
                "race": card["race"],
                "level": card["level"],
                "atk": card.get("atk"),
                "def": card.get("def"),
                "attribute": card.get("attribute")
            }
            # Add it to the list of all monsters
            all_monsters.append(monster_data)

            # If its not an extra deck monster, add it to the list of main deck monsters
            if all(x not in card["type"] for x in ["Fusion", "XYZ", "Link", "Synchro"]):
                main_monsters.append(monster_data)
            
            for number in xyz_numbers:
                if number in card["name"] and "XYZ" in card["type"]:
                    seventh_tachyon_targets.append(monster_data)
    
    # Get it back into json format
    all_monsters = {"data": all_monsters}
    main_monsters = {"data": main_monsters}
    seventh_tachyon_targets = {"data": seventh_tachyon_targets}

    # Store all monster data
    with open('global/json/all_monster_database.json', 'w', encoding="utf-8") as file:
        json.dump(all_monsters, file, indent=4, ensure_ascii=False)

    # Store main deck monster data
    with open('global/json/main_monster_database.json', 'w', encoding="utf-8") as file:
        json.dump(main_monsters, file, indent=4, ensure_ascii=False)

    # Store Seventh Tachyon data
    with open('global/json/seventh_tachyon_targets.json', 'w', encoding="utf-8") as file:
        json.dump(seventh_tachyon_targets, file, indent=4, ensure_ascii=False)

# Converts a ydk clipboard deck to an array of ids
def convert_ydk_clipboard_to_id(decklist, array_of_ids):
    filter = decklist.strip().split()
    for line in filter:
        if line and line[0].isdigit() and int(line) not in array_of_ids:
            array_of_ids.append(int(line))
    return

# Converts a ygopro clipboard deck to an array of ids
def convert_ygo_pro_clipboard_to_id(decklist, array_of_ids):
    filter = decklist.strip().split()
    for line in filter:
        if line and line[0].isdigit() and int(line) not in array_of_ids:
            array_of_ids.append(int(line))
    return

# Converts an array of card ids to an array of correlated card json objects that are only monsters
def assign_monster_card_by_id(array_of_ids, array_of_cards, database):
    # For every id in the array
    for id in array_of_ids:
        # Iterate through the database
        for card in database["data"]:
            # If there is a match
            if card["id"] == id:
                # Check if it's a monster, otherwise break from the loop
                if "Monster" in card["type"]:
                    array_of_cards.append(
                        {
                            "id": card["id"],
                            "name": card["name"],
                            "type": card["type"],
                            "race": card["race"],
                            "level": card.get("level"),
                            "atk": card.get("atk"),
                            "def": card.get("def"),
                            "attribute": card.get("attribute")
                        }
                    )
                break
    return

# Converts an array of card ids to an array of correlated card json objects that are only main deck monsters
def assign_main_deck_monsters_by_id(array_of_ids, array_of_cards, database):
    # For every id in the array
    for id in array_of_ids:
        # Iterate through the database
        for card in database["data"]:
            # If there is a match
            if card["id"] == id:
                # Check if it's a monster, otherwise break from the loop
                if all(x not in card["type"] for x in ["Fusion", "XYZ", "Link", "Synchro"]) and "Monster" in card["type"]:
                    array_of_cards.append(
                        {
                            "id": card["id"],
                            "name": card["name"],
                            "type": card["type"],
                            "race": card["race"],
                            "level": card.get("level"),
                            "atk": card.get("atk"),
                            "def": card.get("def"),
                            "attribute": card.get("attribute")
                        }
                    )
                break
    return

# Converts an array of card ids to an array of correlated card json objects
def assign_cards_by_id(array_of_ids, array_of_cards, database):
    # For every id in the array
    for id in array_of_ids:
        # Iterate through the database
        for card in database["data"]:
            # If there is a match
            if card["id"] == id:
                array_of_cards.append(
                    {
                        "id": card["id"],
                        "name": card["name"],
                    }
                )
                break
    return

# Converts an array of card ids to an array of correlated card json objects
def assign_single_card_by_id(card_id, database):
    # Iterate through the database
    for card in database["data"]:
        for card_image in card["card_images"]:
            # If there is a match
            if card_image["id"] == card_id:
                return card["name"]
    return

# Converts an array of card names to an array of correlated card json objects
def assign_cards_by_name(array_of_names, array_of_cards, database):
    # For every id in the array
    for name in array_of_names:
        # Iterate through the database
        for card in database["data"]:
            # If there is a match
            if name.lower().strip() in card["name"].lower().strip():
                array_of_cards.append(
                    {
                        "id": card["id"],
                        "name": card["name"],
                        "type": card["type"],
                        "race": card["race"],
                        "level": card.get("level"),
                        "atk": card.get("atk"),
                        "attribute": card.get("attribute")
                    }
                )
                break
    return

def smart_capitalize(s):
    def cap_special(word):
        # Handle hyphenated and slash-separated segments
        for sep in ['-', '/']:
            if sep in word:
                return sep.join(cap_special(w) for w in word.split(sep))
        return word.capitalize()

    # Use regex to split while preserving punctuation as separate tokens
    tokens = re.findall(r"[\w'-]+|[^\w\s]", s)
    return ''.join(
        (cap_special(token) if re.match(r"[\w'-]+", token) else token)
        + (' ' if i < len(tokens) - 1 and tokens[i+1] not in [',', '.', ':', ';', ')', ']', '}'] else '')
        for i, token in enumerate(tokens)
    ).strip()


# Formats the monster_database.json file
def format_names():
    # Get the latest database of cards
    with open('global/json/full_database.json', 'r', encoding="utf-8") as file:
        full_database = json.load(file)

    all_names = []

    # Filter to just monsters and specific fields
    for card in full_database["data"]:
        all_names.append(card["name"])

    # Store all monster data
    with open('global/json/card_names_database.json', 'w', encoding="utf-8") as file:
        json.dump(all_names, file, indent=4, ensure_ascii=False)

# Formats the monster_database.json file
def format_names_and_set_codes():
    # Get the latest database of cards
    with open('global/json/full_database.json', 'r', encoding="utf-8") as file:
        full_database = json.load(file)

    card_data = []

    # Filter to just monsters and specific fields
    for card in full_database["data"]:
        # Get the set codes
        set_codes = []
        if "card_sets" in card:
            set_codes = [set_info["set_code"] for set_info in card["card_sets"]]

        # Remove duplicates by converting the list to a set and back to a list
        set_codes = list(set(set_codes))

        card_data.append({
            "name": card["name"],
            "set_code": set_codes
        })

    # Store all monster data
    with open('global/json/card_names_and_set_codes_database.json', 'w', encoding="utf-8") as file:
        json.dump(card_data, file, indent=4, ensure_ascii=False)

def card_name_autocomplete(current_input: str):
    with open('global/json/card_names_database.json', 'r', encoding="utf-8") as file:
        card_names_database = json.load(file)
    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in card_names_database
        if current_input.lower() in name.lower()
    ][:25]

def card_set_code_autocomplete(card_name: str, current_input: str):
    with open('global/json/card_names_and_set_codes_database.json', 'r', encoding="utf-8") as file:
        card_data_list = json.load(file)

    set_codes = []
    for card in card_data_list:
        if card["name"].lower() == card_name.lower():
            if "set_code" in card:
                set_codes = card["set_code"]
            break

    return [
        discord.app_commands.Choice(name=code, value=code)
        for code in set_codes
        if current_input.lower() in code.lower()
    ][:25]


def check_valid_card_name(card_name):
    # Open the list of card names
    with open('global/json/card_names_database.json', 'r', encoding="utf-8") as file:
        card_names_database = json.load(file)

    # Check if the name is correct before proceeding
    for name in card_names_database:
        if card_name.lower() in name.lower():
            return True
    return False

async def format_two_decklist_inputs(interaction: discord.Interaction,
                                opponents_clipboard_ydk: str = None,
                                your_clipboard_ydk: str = None,
                                opponents_ydk_file: discord.Attachment = None,
                                your_ydk_file: discord.Attachment = None):

    # Validation: Make sure there is input, then at least one source is provided for each
    if not (opponents_clipboard_ydk or your_clipboard_ydk or opponents_ydk_file or your_ydk_file):
        await interaction.followup.send("❌ You must provide either a `copied ydk` or a `.ydk file` for both the `opponent's decklist` and `your decklist`.")
        return None, None
    if not opponents_clipboard_ydk and not opponents_ydk_file:
        await interaction.followup.send("❌ You must provide either a `copied ydk` or a `.ydk file` for the `opponent's decklist`.")
        return None, None
    if not your_clipboard_ydk and not your_ydk_file:
        await interaction.followup.send("❌ You must provide either a `copied ydk` or a `.ydk file` for `your decklist`.")
        return None, None
    
    # Default to copied input
    opponents_decklist = opponents_clipboard_ydk
    your_decklist = your_clipboard_ydk

    # Read uploaded files (if any)
    if opponents_ydk_file is not None:
        opponents_decklist = (await opponents_ydk_file.read()).decode("utf-8")
    if your_ydk_file is not None:
        your_decklist = (await your_ydk_file.read()).decode("utf-8")
    
    return opponents_decklist, your_decklist

async def format_one_decklist_input(interaction: discord.Interaction,
                                decklist_clipboard_ydk: str = None,
                                decklist_ydk_file: discord.Attachment = None):
    # Validation: Make sure at least one source is provided for each
    if not decklist_clipboard_ydk and not decklist_ydk_file:
        await interaction.followup.send("❌ You must provide either a `copied ydk` or a `.ydk file`.")
        return None
    
    # Default to copied input
    decklist = decklist_clipboard_ydk

    # Read uploaded files (if any)
    if decklist_ydk_file is not None:
        decklist = (await decklist_ydk_file.read()).decode("utf-8")

    return decklist

# Replace non-alphanumeric characters (except spaces) with a space
def sanitize_card_name(card_name: str):
    sanitized_name = re.sub(r'[^a-zA-Z0-9\s-]', ' ', card_name)
    return sanitized_name.lower()

def get_current_date():
    current_date_str = datetime.now().strftime("%B %d, %Y")
    return current_date_str