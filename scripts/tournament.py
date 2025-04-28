import discord
import math

async def tournament_info(interaction: discord.Interaction, players: int):
    rounds_of_swiss = 0
    top_cut_breakpoint = 0
    invites = 0
    
    # Set the values for rounds of swiss and top cut based on the number of players
    # These are fixed values from Konami
    match players:
        case _ if 0 <= players <= 3:
            rounds_of_swiss = 2
            top_cut_breakpoint = 0
        case _ if 4 <= players <= 8:
            rounds_of_swiss = 3
            top_cut_breakpoint = 0
        case _ if 9 <= players <= 16:
            rounds_of_swiss = 4
            top_cut_breakpoint = 4
        case _ if 17 <= players <= 32:
            rounds_of_swiss = 5
            top_cut_breakpoint = 4
        case _ if 33 <= players <= 64:
            rounds_of_swiss = 6
            top_cut_breakpoint = 8
        case _ if 65 <= players <= 128:
            rounds_of_swiss = 7
            top_cut_breakpoint = 8
        case _ if 129 <= players <= 256:
            rounds_of_swiss = 8
            top_cut_breakpoint = 16
        case _ if 257 <= players <= 512:
            rounds_of_swiss = 9
            top_cut_breakpoint = 16
        case _ if 513 <= players <= 1024:
            rounds_of_swiss = 10
            top_cut_breakpoint = 32
        case _ if 1025 <= players <= 2048:
            rounds_of_swiss = 11
            top_cut_breakpoint = 32
        case _ if 2049 <= players:
            rounds_of_swiss = 12
            top_cut_breakpoint = 64
        
    # Set the number of invites based on the number of players
    # These are fixed values provided by TheSideDeck
    match players:
        case _ if 4 <= players <= 49:
            invites = 4
        case _ if 50 <= players <= 99:
            invites = 8
        case _ if 100 <= players <= 149:
            invites = 16
        case _ if 150 <= players <= 199:
            invites = 24
        case _ if 200 <= players <= 299:
            invites = 32
        case _ if 300 <= players <= 499:
            invites = 48
        case _ if 500 <= players:
            invites = 64

    # Build the initial text response
    message_response = f"In a Konami sanctioned tournament with **{str(players)} players**, \nThere will be **{str(rounds_of_swiss)} rounds of swiss** and"

    # Check if there is top cut
    if (top_cut_breakpoint > 0):
        message_response += f" a cut to **Top {str(top_cut_breakpoint)}** with the following results:"
        message_response = top_cut(players, rounds_of_swiss, top_cut_breakpoint, message_response)
    else:
        message_response = f"With a tournament of **{str(players)} players**, \nThere will be **{str(rounds_of_swiss)} rounds of swiss** and **No Top Cut**."

    # Add invite information if applicable
    if (players >= 4):
        message_response += f"\n\nAdditionally, if this is a **Regional Qualifier**, there will be **{str(invites)} invites**"
        message_response = f"{invite_breakpoints(players, rounds_of_swiss, invites, message_response)}\n"
        message_response = f"{regional_prizing(players, rounds_of_swiss, 4, message_response)}\n"
        message_response = regional_prizing(players, rounds_of_swiss, 8, message_response)

    await interaction.response.send_message(message_response)

def top_cut(players: int, rounds: int, top_cut_breakpoint: int, message_response: str):
    # Define the number of players finishing at each record, better than x-1,x-2,x-3,x-4
    player_counts = get_player_counts(players, rounds)

    # Define the text for how many points a player would have to be above a given record (10-12 points for above x-1 etc.)
    point_ranges = get_point_ranges(rounds)

    # For every record,
    for iterator, players_above_current_record in enumerate(player_counts):
        # If the number of players above this record exceeds the number of invites
        breakpoint_text = format_breakpoints(top_cut_breakpoint, players_above_current_record)
        players_text = format_players(top_cut_breakpoint, players_above_current_record)

        if players_above_current_record >= top_cut_breakpoint:
            # Add the text to the message response
            message_response += f"\n\t\tFinally, {breakpoint_text} {players_text} with a record better than **{rounds - iterator - 1}-{iterator+1}** (*{point_ranges[iterator]}* points) will make top cut"
            return message_response
        # If there are more invites than the number of players above this record
        else:
            message_response += f"\n\t\t{players_text}with a record better than **{rounds - iterator - 1}-{iterator+1}** (*{point_ranges[iterator]}* points)"
            # Subtract the player count
            top_cut_breakpoint -= players_above_current_record

    return message_response


def invite_breakpoints(players: int, rounds: int, invites: int, message_response: str):
    # Define the number of players finishing at each record, better than x-1,x-2,x-3,x-4
    player_counts = get_player_counts(players, rounds)

    # Define the text for how many points a player would have to be above a given record (10-12 points for above x-1 etc.)
    point_ranges = get_point_ranges(rounds)

    # For every record,
    for iterator, players_above_current_record in enumerate(player_counts):
        # If the number of players above this record exceeds the number of invites

        if players == invites:
            message_response += f"\n\t\t**Invites** will be given to **All** players in the tournament"
            return message_response
        elif players_above_current_record >= invites:
            # Format the text
            invite_text = format_breakpoints(invites, players_above_current_record)
            players_text = format_players(invites, players_above_current_record)

            if (invite_text == "**All** players"):
                message_response += f"\n\t\t**Invites** will be given to **All** players with a record better than **{rounds - iterator - 1}-{iterator+1}** (*{point_ranges[iterator]}* points)"
            else:
                message_response += f"\n\t\t**Invites** will be given to **All** players with a record better than **{rounds - iterator}-{iterator}** (*{point_ranges[iterator - 1]}* points)\n\t\t\tand to {invite_text} {players_text}with a record better than **{rounds - iterator - 1}-{iterator+1}** (*{point_ranges[iterator]}* points)"
            return message_response
        # If there are more invites than the number of players above this record
        else:
            # Subtract the player count
            invites -= players_above_current_record

    return message_response

def regional_prizing(players: int, rounds: int, top_cut_breakpoint: int, message_response: str):
    # Define the number of players finishing at each record, better than x-1,x-2,x-3,x-4
    player_counts = get_player_counts(players, rounds)

    # Define the text for how many points a player would have to be above a given record (10-12 points for above x-1 etc.)
    point_ranges = get_point_ranges(rounds)

    # This function uses the total top cut, rather than a variable number
    initial_top_cut = top_cut_breakpoint

    # For every record,
    for iterator, players_above_current_record in enumerate(player_counts):
        # If the number of players above this record exceeds the number of invites
        breakpoint_text = format_breakpoints(top_cut_breakpoint, players_above_current_record)
        players_text = format_players(top_cut_breakpoint, players_above_current_record)

        if players == initial_top_cut:
            message_response += f"\n\t\t**Top {initial_top_cut}** prizing will be given to **All** players in the tournament"
            return message_response
        elif players_above_current_record >= top_cut_breakpoint:
            if (breakpoint_text == "**All** players"):
                message_response += f"\n\t\t**Top {initial_top_cut}** prizing will be given to **All** players with a record better than **{rounds - iterator - 1}-{iterator+1}** (*{point_ranges[iterator]}* points)"
                return message_response
            else:
                # Add the text to the message response
                message_response += f"\n\t\t**Top {initial_top_cut}** prizing will be given to **All** players with a record better than **{rounds - iterator}-{iterator}** (*{point_ranges[iterator - 1]}* points)\n\t\t\tand to {breakpoint_text} {players_text}with a record better than **{rounds - iterator - 1}-{iterator+1}** (*{point_ranges[iterator]}* points)"
                return message_response
        # If there are more invites than the number of players above this record
        else:
            # Subtract the player count
            top_cut_breakpoint -= players_above_current_record

    return message_response

# Checks if a float is a whole number, or has a decimal value. Used for punctuation and pluralization purposes
def is_whole_number(value):
    return math.floor(value) == math.ceil(value)

# Set the text for the current breakpoint
def format_breakpoints(remaining_spots, current_players):
    # Check if the number of remaining spots is a whole number or a float
    if is_whole_number(remaining_spots):
        # Set the value to an int to avoid floating point errors
        remaining_spots = int(remaining_spots)

        if remaining_spots == 1:
            return "**1** player"
        elif abs(remaining_spots - current_players) < 0.01:
            return f"**All** players"
        else:
            return f"**{int(remaining_spots)}** players"
    else:
        if (math.floor(remaining_spots) == math.floor(current_players)) and (math.ceil(remaining_spots) == math.ceil(current_players)):
            return f"**All** players"
        else:
            return f"**{math.floor(remaining_spots)}-{math.ceil(remaining_spots)}** players"

# Set the text for the current player count
def format_players(remaining_spots, players):
    # Check if the number of players is a whole number or a float
    if is_whole_number(players):
        # Set the value to an int to avoid floating point errors
        players = int(players)

        if players == 1:
            return "**1** player "
        elif remaining_spots >= players:
            # This text would appear at the start of a setence as listing the number of remaining spots is not needed
            return f"**{int(players)}** players "
        else:
            # This text would appear in the middle of a sentence as listing the number of remaining spots is required
            return f"out of the **{int(players)}** "
    # If its a float, its interpreted as a range of numbers
    else:
        if (math.floor(remaining_spots) == math.floor(players)) and (math.ceil(remaining_spots) == math.ceil(players)):
            return ""
        # If there are more spots remaining than players
        elif remaining_spots >= players:
            # This text would appear at the start of a setence as listing the number of remaining spots is not needed
            return f"**{math.floor(players)}-{math.ceil(players)}** players "
        else:
            # This text would appear in the middle of a sentence as listing the number of remaining spots is required
            return f"out of the **{math.floor(players)}-{math.ceil(players)}** "

# Retrieves the number of players above each record
def get_player_counts(players: int, rounds: int):
    player_counts = [
        players / (2 ** rounds),
        players / (2 ** rounds) * rounds,
        players / (2 ** rounds) * rounds * ((rounds - 1) / 2),
        players / (2 ** rounds) * rounds * ((rounds - 1) / 2) * ((rounds - 2) / 3),
    ]
    return player_counts

# Retrieves the point ranges for each record
def get_point_ranges(rounds: int):
    point_ranges = [
        f"{rounds * 3 - 2}-{rounds * 3}",     
        f"{rounds * 3 - 5}-{rounds * 3 - 3}",
        f"{rounds * 3 - 8}-{rounds * 3 - 6}",
        f"{rounds * 3 - 11}-{rounds * 3 - 9}"
    ]
    return point_ranges