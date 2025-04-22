import json
import os
import scripts.formatter as formatter
import discord

# Creates a list of all the Small World bridges between 2 cards
def small_world_pair(guild_id_as_int, first_card: str, second_card: str):
    # Get the latest database of cards
    with open('global/json/main_monster_database.json', 'r', encoding="utf-8") as file:
        main_monster_database = json.load(file)

    # Small World is exactly 1 of the same: Type, Attribute, Level, ATK or DEF
    cards_as_names = [first_card, second_card]
    cards_as_json = []
    valid_bridges_matrix = []
    list_of_matches = []

    # Change list of card names to a list of card objects with populated information
    formatter.assign_cards_by_name(cards_as_names, cards_as_json, main_monster_database)

    # Change a list of card objects to a matrix of valid Small World targets
    share_one_feature(cards_as_json, valid_bridges_matrix, main_monster_database["data"])

    # Change 2 or more lists of valid Small World targets to a single list of valid bridges
    same_name(valid_bridges_matrix, list_of_matches)

    # Creates the file path if it doesn't exist
    os.makedirs(f"guilds/{guild_id_as_int}/docs", exist_ok=True)

    # Write results to a file
    with open(f"guilds/{guild_id_as_int}/docs/small_world.txt", "w", encoding="utf-8") as file:
        # Write the bridge we're trying to solve
        file.write(f"{cards_as_json[0]['name']} -> {cards_as_json[1]['name']}:\n")
        
        # Write the valid targets
        for card in list_of_matches:
            file.write(f"{card}")

    return "These are all the Small World bridges for:"

# Creates a list of all the Small World bridges in a decklist
def small_world_decklist(guild_id_as_int, decklist: str):
    with open('global/json/full_database.json', 'r', encoding="utf-8") as file:
        full_database = json.load(file)
        
    # Variable declarations
    array_of_ids_to_search = []
    cards_to_search = []
    valid_bridges_matrix = []

    # Convert ydk clipboard deck to array of IDs
    formatter.convert_ydk_clipboard_to_id(decklist, array_of_ids_to_search)

    # Convert arrays of IDs to array of JSON card details
    formatter.assign_main_deck_monsters_by_id(array_of_ids_to_search, cards_to_search, full_database)

    # Create a matrix that holds all cards that share 1 feature with every card in the array 
    share_one_feature(cards_to_search, valid_bridges_matrix, cards_to_search)
    
    # Creates the file path if it doesn't exist
    os.makedirs(f"guilds/{guild_id_as_int}/docs", exist_ok=True)

    # Write the results to a file
    with open(f"guilds/{guild_id_as_int}/docs/small_world_decklist.txt", "w", encoding="utf-8") as file:
        # For every card in every list
        for starting_card in range(len(valid_bridges_matrix)):
            # For every card in every other list
            for ending_card in range(starting_card + 1, len(valid_bridges_matrix)):
                # Set the lists to variables
                starting_card_list = valid_bridges_matrix[starting_card]
                ending_card_list = valid_bridges_matrix[ending_card]
                
                # Use matrix "set" to intersect the lists (only keep duplicates)
                valid_bridges_list = set(starting_card_list) & set(ending_card_list)
                
                # If it finds any matches to begin with
                if valid_bridges_list:
                    # Write the card names and all valid bridges
                    file.write(f"{starting_card_list[0]} --> {ending_card_list[0]}:\n")
                    for card in valid_bridges_list:
                        file.write(f"{card}")
                    file.write("\n")

    return "Here are all the Small World bridges for your decklist"

# Converts a list of card objects to a matrix of valid Small World targets
def share_one_feature(cards_as_json, valid_bridges_matrix, database):
    matching_features = 0
    current_matches = []
    # For every card passed in the array (for every card in the decklist)
    for card in cards_as_json:
        current_matches = [card["name"]]
        # For every card in the game OR 
        for data in database:
            if card["name"] != data["name"]:
                # Reset the number of matching features
                matching_features = 0

                # Check for only 1 matching feature
                if card["race"] == data["race"]:
                    matching_features += 1
                if card["attribute"] == data["attribute"]:
                    matching_features += 1
                if card["level"] == data["level"]:
                    matching_features += 1
                if card.get("atk") == data.get("atk"):
                    matching_features += 1
                if card.get("def") == data.get("def"):
                    matching_features += 1
                if matching_features == 1:
                    current_matches.append(f"\t-{data['name']}\n")
            
        valid_bridges_matrix.append(current_matches)
        current_matches = []
    return

# Compares two different lists of targets, returns a result if there is a match between them (They both have the same target)
def same_name(valid_bridges_matrix, list_of_matches):
    for first_card in valid_bridges_matrix[0]:
        for second_card in valid_bridges_matrix[1]:
            if first_card == second_card:
                list_of_matches.append(first_card)
    return

def small_world_autocomplete(current_input: str):
    with open('global/json/main_monster_database.json', 'r', encoding="utf-8") as file:
        small_world_database = json.load(file)
    monster_names = [card['name'] for card in small_world_database['data']]
    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in monster_names
        if current_input.lower() in name.lower()
    ][:25]