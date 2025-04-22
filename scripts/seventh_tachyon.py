import json
import os
import scripts.formatter as formatter

# Creates a list of all the current Seventh Tachyon targets
def seventh_tachyon_list(guild_id_as_int):
    # Load the full database of cards
    with open('global/json/full_database.json', 'r', encoding="utf-8") as file:
        full_database = json.load(file)

    # Retrieve all the valid targets
    valid_targets = search_for_tachyon_targets(full_database["data"])

    # Creates the file path if it doesn't exist
    os.makedirs(f"guilds/{guild_id_as_int}/docs", exist_ok=True)

    # Save the results to a file
    with open(f"guilds/{guild_id_as_int}/docs/seventh_tachyon_targets.txt", "w", encoding="utf-8") as file:
        for card in valid_targets:
            file.write(f"{card}")
    return "List of all current Seventh Tachyon targets:"

# Creates a list of all the Seventh Tachyon targets in a given decklist
def seventh_tachyon_decklist(guild_id_as_int, decklist: str):
    # Load the full database of cards
    with open('global/json/full_database.json', 'r', encoding="utf-8") as file:
        full_database = json.load(file)

    array_of_ids_to_search = []
    cards_to_search = []

    # Convert ydk clipboard deck to array of IDs
    formatter.convert_ydk_clipboard_to_id(decklist, array_of_ids_to_search)

    # Convert arrays of IDs to array of JSON card details
    formatter.assign_monster_card_by_id(array_of_ids_to_search, cards_to_search, full_database)
    
    # Retrieve all the valid targets
    valid_targets = search_for_tachyon_targets(cards_to_search)

    # Creates the file path if it doesn't exist
    os.makedirs(f"guilds/{guild_id_as_int}/docs", exist_ok=True)
    
    # Save the results to a file
    with open(f"guilds/{guild_id_as_int}/docs/seventh_tachyon_deck_targets.txt", "w", encoding="utf-8") as file:
        for card in valid_targets:
            file.write(f"{card}")

    return "Here is the list of your deck's Seventh Tachyon targets:"

# Creates a list of all the valid Seventh Tachyon targets for a given array of cards
def search_for_tachyon_targets(cards_json):
    # Load the Seventh Tachyon database
    with open('global/json/seventh_tachyon_targets.json', 'r', encoding="utf-8") as file:
        seventh_tachyon_database = json.load(file)

    current_card_results = "Targets for "
    valid_targets = []

    # For every XYZ monster listed in the Seventh Tachyon database
    for card in seventh_tachyon_database["data"]:
        # List the name of the card in the output
        current_card_results += f"{card['name']}\n"
        # For every card in the list
        for data in cards_json:
            # If it is a monster and not an extra deck monster
            if all(x not in data["type"] for x in ["Fusion", "XYZ", "Link", "Synchro"]) and "Monster" in data["type"]:
                # If the level of the monster equals the rank of the XYZ monster
                if data["level"] == card["level"]:
                    # If the type or attribute is also the same
                    if data["race"] == card["race"] or data["attribute"] == card["attribute"]:
                        # Add the card to the list
                        current_card_results += f"\t-{data['name']}\n"

        # If there are any valid targets for the card, add it to the list
        if current_card_results != f"Targets for {card['name']}\n":
            current_card_results += "\n"
            valid_targets.append(current_card_results)

        # Reset the base text
        current_card_results = "Targets for "
    return valid_targets
