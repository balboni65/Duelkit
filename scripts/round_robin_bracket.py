import json
import os
import discord
from scripts import formatter

# Creates a tournament bracket for a given list of players
def round_robin_bracket_builder(tournamentName, player_list, guild_id):
    # Define the base of the bracket json object
    bracket = {
        "title": "Round Robin Bracket:",
        "pairings": []
        }
    
    # Number of rounds per tournament
    rounds_per_bracket = roundsPerBracket(player_list)
    # Number of matches per round
    matches_per_round = matchesPerRound(player_list)
    # Which preset of pairings to use stored as a matrix see pairingsMatrix()
    pairings_matrix = pairingsMatrix(player_list)
   
    # For every round in the tournament
    for round_number in range(1, rounds_per_bracket + 1):

        # Set current round text
        round_name = f"round{str(round_number)}"
        round_pairings = []

        # For every match in the round
        for match_number in range(1, matches_per_round + 1):
            
            # Sets the match name: "match1", "match2", etc.
            match_name = f"match{str(match_number)}"
            player_1 = ""
            player_2 = ""

            if matches_per_round == 1:
                # First gets an index number from the pairing matrix based on the current round # and match #: "0", "1", etc; Then gets the player for that index: "mike", etc.
                player_1 = player_list[pairings_matrix[round_number-1][0]]
                player_2 = player_list[pairings_matrix[round_number-1][1]]

            elif matches_per_round > 1:
                # First gets an index number from the pairing matrix based on the current round # and match #: "0", "1", etc; Then gets the player for that index: "mike", etc.
                player_1 = player_list[pairings_matrix[round_number-1][match_number-1][0]]
                player_2 = player_list[pairings_matrix[round_number-1][match_number-1][1]]

            # Sets the text for which players are in that match
            match_pairing = f"{formatter.smart_capitalize(player_1)} vs {formatter.smart_capitalize(player_2)}"

            # Creates the match object, and adds a result variable for later
            match = {
                match_name: match_pairing,
                "result": ""
            }

            # Adds the match to the specific round
            round_pairings.append(match)

        # Adds the round object to the pairings array
        bracket["pairings"].append({round_name: round_pairings})

    # Creates the file path if it doesn't exist
    os.makedirs(f"guilds/{guild_id}/json/tournaments", exist_ok=True)   

    # Save the bracket for results later
    with open(f'guilds/{guild_id}/json/tournaments/{tournamentName}.json', 'w', encoding="utf-8") as file:
        json.dump(bracket, file, indent=4, ensure_ascii=False)


def attach_message_to_bracket(bracket_message: discord.Message, interaction: discord.Interaction, tournament_name: str):
    guild_id = interaction.guild.id
    category_id = interaction.channel.category.id
    channel_id = interaction.channel.id
    message_id = bracket_message.id


    # Read the bracket results
    with open(f'guilds/{guild_id}/json/tournaments/{tournament_name}.json', 'r', encoding="utf-8") as file:
        bracket = json.load(file)

    message_info = {
        "guild_id": guild_id,
        "category_id": category_id,
        "channel_id": channel_id,
        "message_id": message_id,
    }

    bracket["message_info"] = message_info

    # Save the bracket for results later
    with open(f'guilds/{guild_id}/json/tournaments/{tournament_name}.json', 'w', encoding="utf-8") as file:
        json.dump(bracket, file, indent=4, ensure_ascii=False)

# Determines the number of rounds based on player count
def roundsPerBracket(player_list):
    if len(player_list) == 3:
        rounds_per_bracket = 3
    if len(player_list) == 4:
        rounds_per_bracket = 6
    if len(player_list) == 5 or len(player_list) == 6:
        rounds_per_bracket = 5
    if len(player_list) == 7 or len(player_list) == 8:
        rounds_per_bracket = 7
    return rounds_per_bracket

# Determines the number of matches per round based on player count
def matchesPerRound(player_list):
    if len(player_list) == 3 or len(player_list) == 4:
        matches_per_round = 1
    if len(player_list) == 5:
        matches_per_round = 2
    if len(player_list) == 6 or len(player_list) == 7:
        matches_per_round = 3
    if len(player_list) == 8:
        matches_per_round = 4
    return matches_per_round

# Creates a matrix of pairings based on player count
def pairingsMatrix(player_list):
    # The pairing matrix exists to avoid someone sitting out for multiple rounds in a row, or missing match-ups
    # By defining pairing patterns, it avoids errors and minimizes player downtime between matches
    pairings_matrix = []
    # Format:
    # Each line is a round #, a round may have multiple pairings inside
    match len(player_list):
        case 3:
            pairings_matrix =  [[0,1],
                                [1,2],
                                [2,0]]
        case 4:
            pairings_matrix =  [[2,3],
                                [0,1],
                                [1,2],
                                [3,0],
                                [1,3],
                                [2,0]]
        case 5:
            pairings_matrix =  [[[0,3],[1,2]],
                                [[2,0],[3,4]],
                                [[4,2],[0,1]],
                                [[1,4],[2,3]],
                                [[3,1],[4,0]]]
        case 6:
            pairings_matrix = [[[1,0],[2,5],[3,4]],
                               [[2,3],[5,0],[1,4]],
                               [[5,3],[1,2],[0,4]],
                               [[3,0],[4,2],[5,1]],
                               [[4,5],[0,2],[3,1]]]
        case 7:
            pairings_matrix = [[[0,5],[1,4],[2,3]],
                               [[3,1],[4,0],[5,6]],
                               [[1,6],[2,5],[3,4]],
                               [[4,2],[5,1],[6,0]],
                               [[2,0],[3,6],[4,5]],
                               [[5,3],[6,2],[0,1]],
                               [[0,3],[1,2],[4,6]]]
        case 8:
            pairings_matrix = [[[1,0],[2,7],[3,6],[4,5]],
                               [[2,3],[0,6],[7,5],[1,4]],
                               [[5,1],[6,7],[3,0],[4,2]],
                               [[6,4],[7,3],[1,2],[5,0]],
                               [[0,2],[3,1],[4,7],[5,6]],
                               [[3,4],[7,0],[1,6],[2,5]],
                               [[6,2],[7,1],[0,4],[5,3]]]
    return pairings_matrix