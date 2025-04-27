import discord
import random
from scripts import formatter

async def setup_tournament(interaction: discord.Interaction, players: str):
    # Store a string of players as individuals in an array
    player_list = players.split()

    player_list = [formatter.smart_capitalize(player) for player in player_list]


    if interaction.channel.category == None:
        await interaction.followup.send("Please create a **category** for this channel before creating a tournament, so they can be grouped by seasons.", ephemeral=True)
        return

    # Get the tournament name from the category name + channel name
    tournament_name = (f"{interaction.channel.category.name}_{interaction.channel.name}").replace(" ", "_")

    # Randomize the order of players
    random.shuffle(player_list)

    return tournament_name, player_list