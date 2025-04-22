import json
import scripts.formatter as formatter
import os
import discord

# Creates a list of all the current Metaltronus targets
def metaltronus_single(guild_id_as_int, input: str):    
    # Get the latest database of cards
    with open('global/json/all_monster_database.json', 'r', encoding="utf-8") as file:
        metaltronus_database = json.load(file)

    chosen_card = {}
    matching_characteristics = 0
    metaltronus_targets = []

    # Filter to just monsters and specific fields
    for card in metaltronus_database["data"]:
        if input.lower().strip() in card.get("name", "").lower().strip():
            chosen_card = {
                "name": card["name"],
                "race": card["race"],
                "attribute": card.get("attribute"),
                "atk": card.get("atk"),
            }
            break  # Exit the loop after the first match

    # Exits if it couldn't validate the search
    if chosen_card == {}:
        return "I could not validate the card you're searching for"

    # Find any matching cards
    for card in metaltronus_database["data"]:
        if chosen_card["race"].lower().strip() in card.get("race", "").lower().strip():
            matching_characteristics += 1
        if chosen_card["attribute"].lower().strip() in card.get("attribute", "").lower().strip():
            matching_characteristics += 1
        if chosen_card["atk"] == card.get("atk"):
            matching_characteristics += 1
        if matching_characteristics >= 2:
            if chosen_card["name"].lower().strip() != card.get("name", "").lower().strip():
                metaltronus_targets.append(card["name"])
        matching_characteristics = 0

    # Creates the file path if it doesn't exist
    os.makedirs(f"guilds/{guild_id_as_int}/docs", exist_ok=True)

    # Create the file with the results
    with open(f"guilds/{guild_id_as_int}/docs/metaltronus_single.txt", "w", encoding="utf-8") as file:
        for card in metaltronus_targets:
            file.write(f"{card}\n")
    
    return f"Here are all your matches for: \n```{chosen_card['name']}```"

# Creates a list of all the Metaltronus targets between 2 given decklists
def metaltronus_decklist(guild_id_as_int, decklist_to_search: str, decklist_as_targets: str):    
    # Get the latest database of cards
    with open('global/json/all_monster_database.json', 'r', encoding="utf-8") as file:
        metaltronus_database = json.load(file)
        
    array_of_ids_to_search = []
    array_of_ids_as_targets = []
    cards_to_search = []
    cards_as_targets = []
    metaltronus_final_results = []

    # Convert ydk clipboard deck to array of ids
    formatter.convert_ydk_clipboard_to_id(decklist_to_search, array_of_ids_to_search)
    formatter.convert_ydk_clipboard_to_id(decklist_as_targets, array_of_ids_as_targets)

    # Convert arrays of IDs to array of JSON card details
    formatter.assign_monster_card_by_id(array_of_ids_to_search, cards_to_search, metaltronus_database)
    formatter.assign_monster_card_by_id(array_of_ids_as_targets, cards_as_targets, metaltronus_database)
    # Computes all targets into metaltronus_final_results
    metaltronus_list_from_two_decklists(cards_to_search, cards_as_targets, metaltronus_final_results)
    
    # Creates the file path if it doesn't exist
    os.makedirs(f"guilds/{guild_id_as_int}/docs", exist_ok=True)

    # Write the findings to a file
    with open(f"guilds/{guild_id_as_int}/docs/metaltronus_deck_compare.txt", "w", encoding="utf-8") as file:
        for card in metaltronus_final_results:
            file.write(f"{card}")
    return "Here's all the valid targets I was able to find for those 2 decklists"

# Creates a list of all the valid Metaltronus targets for two given arrays of cards
def metaltronus_list_from_two_decklists(cards_to_search, cards_as_targets, metaltronus_final_results):
    matching_characteristics = 0
    current_card_results = "Targets for: "
    no_card_results = "There are no unfortunately no targets for:\n"

    # For every card in the first decklist
    for searched_card in cards_to_search:
        # Add the card name to results
        current_card_results += f"{searched_card['name']}\n"
        # Compare to every monster in the second decklist
        for target_card in cards_as_targets:
            # Compare properties
            if target_card["race"].lower().strip() in searched_card.get("race", "").lower().strip():
                matching_characteristics += 1
            if target_card["attribute"].lower().strip() in searched_card.get("attribute", "").lower().strip():
                matching_characteristics += 1
            if target_card["atk"] == searched_card.get("atk"):
                matching_characteristics += 1
            # If a valid Metaltronus target
            if matching_characteristics >= 2:
                # If they aren't the same name
                if target_card["name"].lower().strip() != searched_card.get("name", "").lower().strip():
                    # Add the card to the list of valid targets for the target card
                    current_card_results += f"\t-{target_card['name']}\n"
            # Reset the matching characteristics
            matching_characteristics = 0

        # After searching through every card in the second decklist, check if you did not find any targets
        if current_card_results == f"Targets for: {searched_card['name']}\n":
            # Add to no results found section
            no_card_results += f"\t{searched_card['name']}\n"
        else:
            # Add to valid targets list
            current_card_results += "\n"
            metaltronus_final_results.append(current_card_results)
        # Reset current card text
        current_card_results = "Targets for: "
    
    # After we've finished searching for every card in the first decklist, append the cards we didn't find
    metaltronus_final_results.append(no_card_results)
    return

def metaltronus_autocomplete(current_input: str):
    with open('global/json/all_monster_database.json', 'r', encoding="utf-8") as file:
        metaltronus_database = json.load(file)
    monster_names = [card['name'] for card in metaltronus_database['data']]
    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in monster_names
        if current_input.lower() in name.lower()
    ][:25]