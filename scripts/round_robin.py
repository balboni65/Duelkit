import discord
import random
import json
import scripts.bracket_builder as bracket_builder
import pandas
import asyncio
import os

# In Discord, putting ```_``` around a string allows you to copy the text, creating a keyword for it here
copy = "```"

# Creates a round robin tournament
async def round_robin_bracket(interaction: discord.Interaction, players: str, guild_id: int):
    # Store a string of players as individuals in an array
    player_list = players.split()

    if interaction.channel.category == None:
        await interaction.followup.send("Please create a **category** for this channel before creating a tournament, so they can be grouped by seasons.", ephemeral=True)
        return

    # Get the tournament name from the category name + channel name
    tournament_name = (f"{interaction.channel.category.name}_{interaction.channel.name}").replace(" ", "_")

    # Randomize the order of players
    random.shuffle(player_list)

    # Build the bracket for our competitors
    bracket_builder.bracket_builder(tournament_name, player_list, guild_id)

    # Read the bracket results
    with open(f'guilds/{guild_id}/json/tournaments/{tournament_name}.json', 'r', encoding="utf-8") as file:
        bracket = json.load(file)

    # Define the Discord embed to notify players
    response_embed = discord.Embed(title=f"Tournament Bracket For {str(len(player_list))} Players:", color=0xbbaa5e)

    # Populate the Discord embed with tournament information
    response_embed = create_tournament_embed(bracket, response_embed)

    # Send the message with the bracket
    bracket_message = await interaction.followup.send(embed=response_embed)
    
    # Take the sent message and update the bracket file with the message ID to edit later
    bracket_builder.attach_message_to_bracket(bracket_message, interaction, tournament_name)

# Creates the embed message displaying the pairings
def create_tournament_embed(bracket, embed):
    # For every index of the pairings array, get the JSON object
    for round in bracket["pairings"]:
        # Get the key-value pair of the round JSON object, e.g., the key (round1) and the value (JSON object of match/results info)
        for round_name, round_info in round.items():
            # Format the round name for later
            round_text = f"**{round_name.replace('round', 'Round ')}:**"
            # Create the match text that will appear in the embed
            match_text = ""
            # For every index of the round array, get the JSON object
            for match in round_info:
                # Get the key-value pair of the match/results JSON string, e.g., the key (match1/result) and the value (p v p/"")
                for match_name, match_value in match.items():
                    # We want to filter to just the match values
                    if "match" in match_name:
                        match_text += f"{copy}{match_value}{copy}\n"
            # Populate the embed with round info            
            embed.add_field(name=round_text, value=match_text, inline=True)

    return embed

# Creates the embed message asking who won the match
async def report(interaction: discord.Interaction, result: str):
    # Get the tournament name from the category name + channel name
    tournament_name = (f"{interaction.channel.category.name}_{interaction.channel.name}").replace(" ", "_")

    # Get the listed match name from the tournament file and result string
    match_name = check_result(tournament_name, result, interaction)

    # If the match is found
    if match_name:
        embed = discord.Embed(title=f"Please select who has won the following match:\n\n**{match_name}**", color=0xbbaa5e)

        # Generate the buttons to enter a match result
        await interaction.response.send_message(embed=embed, view=generate_view(interaction, match_name), ephemeral=True)
    else:   
        embed = discord.Embed(title="Match not Found.\n\nPlease press the copy button on the match,\nthen paste it into the /report field.", color=0xbbaa5e)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    return embed

# Checks if all matches in the tournament have a result
def check_result(tournament_name, result, interaction: discord.Interaction):
    guild_id = interaction.guild.id

    # Read the current bracket standings
    with open(f'guilds/{guild_id}/json/tournaments/{tournament_name}.json', 'r', encoding="utf-8") as file:
        bracket = json.load(file)

    # For every index of the pairings array, get the JSON object
    for round in bracket["pairings"]:
        # Get the key-value pair of the round JSON object, e.g., the key (round1) and the value (JSON object of match/results info)
        for round_name, round_info in round.items():
            # For every index of the round array, get the JSON object
            for match in round_info:
                # Get the key-value pair of the match/results JSON string, e.g., the key (match1/result) and the value (p v p/"")
                for match_name, match_value in match.items():
                    # We want to filter to just the match values
                    if result.lower().strip() in match_value.lower().strip():
                        return match_value
                    
    return ""

# Writes the result of a match to the tournament file
def write_result(tournament_name, pairing, result, interaction: discord.Interaction):
    guild_id = interaction.guild.id
    # Read the current bracket standings
    with open(f'guilds/{guild_id}/json/tournaments/{tournament_name}.json', 'r', encoding="utf-8") as file:
        bracket = json.load(file)

    # For every index of the pairings array, get the JSON object
    for round in bracket["pairings"]:
        # Get the key-value pair of the round JSON object, e.g., the key (round1) and the value (JSON object of match/results info)
        for round_name, round_info in round.items():
            # For every index of the round array, get the JSON object
            for match in round_info:
                # Get the key-value pair of the match/results JSON string, e.g., the key (match1/result) and the value (p v p/"")
                for match_name, match_value in match.items():
                    # We want to filter to just the match values
                    if pairing in match_value:
                        match["result"] = result
    
    # Creates the file path if it doesn't exist
    os.makedirs(f"guilds/{guild_id}/json/tournaments", exist_ok=True)   

    # If the bracket has been updated, it writes the changes into the file
    with open(f'guilds/{guild_id}/json/tournaments/{tournament_name}.json', 'w', encoding="utf-8") as file:
        json.dump(bracket, file, ensure_ascii=False, indent=4)

# Checks if the tournament has resolved all matches
async def check_tournament(tournament_name, interaction: discord.Interaction):    
    guild_id = interaction.guild.id
    # Set to true immediately, will change to false if it finds any unresolved matches
    is_tournament_finished = True

    # Read the current bracket standings
    with open(f'guilds/{guild_id}/json/tournaments/{tournament_name}.json', 'r', encoding="utf-8") as file:
        bracket = json.load(file)

    # For every index of the pairings array, get the JSON object
    for round in bracket["pairings"]:
        # Get the key-value pair of the round JSON object, e.g., the key (round1) and the value (JSON object of match/results info)
        for round_name, round_info in round.items():
            # For every index of the round array, get the JSON object
            for match in round_info:
                # Get the key-value pair of the match/results JSON string, e.g., the key (match1/result) and the value (p v p/"")
                for match_name, match_value in match.items():
                    # Check if there is a result
                    if match["result"] == "":
                        # Set the tournament to unfinished if there isn't a result
                        is_tournament_finished = False

    # If all matches have a result, save it to an xlsx file                    
    if is_tournament_finished:
        await save_tournament(tournament_name, interaction)

# Saves the tournament to an Excel file
async def save_tournament(tournament_name, interaction: discord.Interaction):
    guild_id = interaction.guild.id
    # Open the tournament
    with open(f'guilds/{guild_id}/json/tournaments/{tournament_name}.json', 'r', encoding="utf-8") as file:
        bracket = json.load(file)

    matches = []
    # For every match in the tournament, save the pairing and result into the matches array
    for round_data in bracket["pairings"]:
        for round_name, matches_list in round_data.items():
            for match in matches_list:
                for key, value in match.items():
                    if "match" in key:
                        match_name = value
                    elif "result" in key:
                        match_result = value
                matches.append([match_name, match_result])
    
    # Create a dataframe which can be converted to an xlsx file and saved
    dataframe = pandas.DataFrame(matches, columns=["Match", "Result"])

    # Creates the file path if it doesn't exist
    os.makedirs(f"guilds/{guild_id}/xlsx/tournaments", exist_ok=True)   

    # Create the xlsx file
    dataframe.to_excel(f"guilds/{guild_id}/xlsx/tournaments/{tournament_name}.xlsx", index=False)

    # attach the xlsx file to the message
    file_path = f"guilds/{guild_id}/xlsx/tournaments/{tournament_name}.xlsx"
    xlsx_file = discord.File(file_path, filename=f"{tournament_name}.xlsx")

    message = "Tournament Finished! Use **/standings** to see the season scores!\n\nAlso, here is an excel file of this weeks results for your own record keeping."

    await interaction.followup.send(content=message, file=xlsx_file)

# Populates the player names into the buttons
def generate_view(interaction: discord.Interaction, result):
    # Separates player1 vs player2 into 3 variables (" vs " is ignored via "_")
    name_1, _, name_2 = result.partition(" vs ")
    
    return View(name_1, name_2, interaction)

# View for the report buttons
class View(discord.ui.View):
    def __init__(self, player_1, player_2, interaction: discord.Interaction):
        super().__init__()
        # Variables
        self.player_1 = player_1
        self.player_2 = player_2
        self.interaction = interaction
        self.pairing = f"{player_1} vs {player_2}"
        self.tournament_name = (f"{interaction.channel.category.name}_{interaction.channel.name}").replace(" ", "_")

        # Because Discord needs a base value for buttons, we have to create the buttons after we have the variable names
        button_1 = discord.ui.Button(label=self.player_1, style=discord.ButtonStyle.blurple, custom_id="player_1")
        button_2 = discord.ui.Button(label=self.player_2, style=discord.ButtonStyle.green, custom_id="player_2")
        button_3 = discord.ui.Button(label="Cancel", style=discord.ButtonStyle.red, custom_id="cancel")
        
        # Set callback methods for buttons
        button_1.callback = self.player_1_button
        button_2.callback = self.player_2_button
        button_3.callback = self.cancel_button

        # Add buttons to the view
        self.add_item(button_1)
        self.add_item(button_2)
        self.add_item(button_3)

    # Callback methods for the buttons
    async def player_1_button(self, interaction: discord.Interaction):
        await self.button_report(interaction, self.player_1, self.player_2, self.tournament_name)

    async def player_2_button(self, interaction: discord.Interaction):
        await self.button_report(interaction, self.player_2, self.player_1, self.tournament_name)

    async def cancel_button(self, interaction: discord.Interaction):
        await self.button_report(interaction, "", "", self.tournament_name)

    # Action taken after choosing a button
    async def button_report(self, interaction: discord.Interaction, winner, loser, tournament_name):
        # Delete the original message asking for who won
        await self.interaction.delete_original_response()

        # Check if player data was passed, if not, it was the cancel button
        if winner and loser:
            await interaction.response.send_message(f"**{winner}** has defeated {loser}!")

            # Save the results to the tournament file
            write_result(self.tournament_name, self.pairing, winner, interaction)
        else:
            await interaction.response.send_message("👍")

        guild_id = interaction.guild.id
        # Read the current bracket standings
        with open(f'guilds/{guild_id}/json/tournaments/{tournament_name}.json', 'r', encoding="utf-8") as file:
            bracket = json.load(file)

        # Retrieve the message for the tournament
        channel_id = bracket["message_info"]["channel_id"]
        channel = interaction.client.get_channel(channel_id)
        message_id = bracket["message_info"]["message_id"]
        bracket_message = await channel.fetch_message(message_id)
        embed_title = bracket_message.embeds[0].title

        # Define the Discord embed to notify players
        response_embed = discord.Embed(title=embed_title, color=0xbbaa5e)

        # Create an embed with updated tournament results
        response_embed = update_tournament(bracket, response_embed)

        # Edit the message with the updated results
        await bracket_message.edit(embed=response_embed)

        await check_tournament(tournament_name, interaction)

        # Wait 5 seconds before deleting the report response message
        await asyncio.sleep(5)
        await interaction.delete_original_response()

# Creates the embed message displaying the pairings
def update_tournament(bracket, embed):
    # For every index of the pairings array, get the JSON object
    for round in bracket["pairings"]:
        # Get the key-value pair of the round JSON object, e.g., the key (round1) and the value (JSON object of match/results info)
        for round_name, round_info in round.items():
            # Format the round name for later
            round_text = f"**{round_name.replace('round', 'Round ')}:**"
            # Create the match text that will appear in the embed
            match_text = ""
            # For every index of the round array, get the JSON object
            for match in round_info:
                # Get the key-value pair of the match/results JSON string, e.g., the key (match1/result) and the value (p v p/"")
                for match_name, match_value in match.items():
                    # We want to filter to just the match values
                    if "match" in match_name:
                        initial_text = f"{copy}{match_value}{copy}\n"
                        if match["result"] != "":
                            match_text += f":white_check_mark: {match['result']} Wins!"
                            # match_text += initial_text.replace(match["result"], f"{match['result']} (WIN)")
                        else:
                            match_text += f":zzz: waiting for results..."

                        
                        match_text += initial_text

                        
            # Populate the embed with round info            
            embed.add_field(name=round_text, value=match_text, inline=True)

    return embed


def get_all_matches(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    tournament_name = ""
    if (interaction.channel and interaction.channel.name and interaction.channel.category):
        tournament_name = (f"{interaction.channel.category.name}_{interaction.channel.name}").replace(" ", "_")
    else:
        return
    
    # Read the current bracket standings
    with open(f'guilds/{guild_id}/json/tournaments/{tournament_name}.json', 'r', encoding="utf-8") as file:
        bracket = json.load(file)
    all_matches = []

    for round_data in bracket["pairings"]:
        for round_name, matches in round_data.items():  # round_name is "round1", etc.
            for match in matches:
                all_matches.append(match)
    return list(all_matches)


async def report_autocomplete(interaction: discord.Interaction, current_input: str):
    match_dicts = get_all_matches(interaction)

    match_names = []
    for match in match_dicts:
        for key, value in match.items():
            if "match" in key.lower():
                match_names.append(value)

    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in match_names
        if current_input.lower() in name.lower()
    ][:25]