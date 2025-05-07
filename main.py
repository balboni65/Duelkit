# MARK: IMPORTS
import discord
from discord import app_commands
from discord.ext import commands
from scripts import (help_pagination, round_robin, formatter, metaltronus, saga, seventh_tachyon, small_world, standings, tiebreakers, top_archetype_breakdown, tournament, top_archetypes, top_cards, card_price_scraper, feedback)
from dotenv import load_dotenv
import os
import asyncio

# Load the environment variables
load_dotenv()

# MARK: VARIABLES
intents = discord.Intents.default()
intents.guilds = True
intents.message_content = True
update_lock = asyncio.Lock() # Lock to prevent multiple instances of the /update command from running at the same time

# MARK: BOT CREATION
class Client(commands.Bot):
    async def on_ready(self):
        # Print bot name and ID
        print(f'Logged on as {self.user} (ID: {self.user.id})')

        # Print connected guild names and IDs
        if not self.guilds:
            print("Bot is not in any guilds.")
            return
        else:
            for guild in self.guilds:
                print(f"Connected to guild: {guild.name} (ID: {guild.id})")

        # Try to sync commands
        try:
            synced = await self.tree.sync()
            print(f'Globally synced {len(synced)} commands')
        except Exception as e:
            print(f'Error syncing commands: {e}')

# Create the client
client = Client(command_prefix="!", intents=intents)



# MARK: CARD PRICE 
@client.tree.command(name="card_price", description="View a card's pricing from TCG Player")
@app_commands.describe(
    card_name="(Required): Any Yu-Gi-Oh! card name (Partial names work as well)", 
    set_code="(Optional): The set code of the card's printing")
async def card_price_helper(interaction: discord.Interaction, card_name: str, set_code: str = None):
    if update_lock.locked():
        await interaction.response.send_message("The bot is already in the process of retreiving another card's information.\nThis may have been triggered in another channel.\nPlease wait a short while until it finishes and try again", ephemeral=True)
    async with update_lock:
        try:
            await interaction.response.defer(thinking=True)

            message = await interaction.followup.send("Starting script...")
            await card_price_scraper.pull_data_from_tcg_player(interaction.guild.id, message, card_name, set_code)
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong in the launching of /card_price:\n```{e}```", ephemeral=True)
@card_price_helper.autocomplete("card_name")
async def card_price_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return formatter.card_name_autocomplete(current_input)

@card_price_helper.autocomplete("set_code")
async def card_set_code_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    card_name = interaction.namespace.card_name
    return formatter.card_set_code_autocomplete(card_name, current_input)



# MARK: EXPLAIN MY TIEBREAKERS
@client.tree.command(name="explain_my_tiebreakers", description="Find out what your tiebreakers mean after a tournament")
@app_commands.describe(tiebreaker_id="(Required): The 10-11 digit code found after your name on the tournament standings")
async def explain_my_tiebreakers_helper(interaction: discord.Interaction, tiebreaker_id: app_commands.Range[int, 100000000, 99999999999]):
    # Defer the response so multiple processes can use its webhook
    await interaction.response.defer(thinking=True)

    # Change the tiebreaker from an int (for automatic input validation) to a string
    tiebreaker_id = str(tiebreaker_id)

    # Create the pagination view
    await tiebreakers.explain_my_tiebreakers(interaction, tiebreaker_id)



# MARK: FEEDBACK 
@client.tree.command(name="feedback", description="Send the creator of Duelkit a message!")
@app_commands.describe(input="(Required): Enter your feedback here")
async def feedback_helper(interaction: discord.Interaction, input: str):
    if not await feedback.is_on_feedback_cooldown(interaction):
        await feedback.send_feedback(interaction, input)



# MARK: HELP 
@client.tree.command(name="help", description="Learn more about the list of available commands, with previews!")
async def help_helper(interaction: discord.Interaction):
    # Defer the response so multiple processes can use its webhook
    await interaction.response.defer(thinking=True)

    # Create the pagination view
    await help_pagination.show_help_pagination(interaction)



#MARK: MASTER PACK
@client.tree.command(name="masterpack", description="Posts the links to view and open Master Packs")
async def master_packs_helper(interaction: discord.Interaction):
    await interaction.response.send_message(embed=saga.master_packs())



#MARK: METALTRONUS DECKLISTS
@client.tree.command(name="metaltronus_decklist", description="Lists all the Metaltronus targets your deck has against another deck")
@app_commands.describe(
    opponents_clipboard_ydk="(Use 1 Method Per Player): Paste the copied \"Clipboard YDK\"", 
    your_clipboard_ydk="(Use 1 Method Per Player): Paste the copied \"Clipboard YDK\"", 
    opponents_ydk_file="(Use 1 Method Per Player): Upload a .ydk file", 
    your_ydk_file="(Use 1 Method Per Player): Upload a .ydk file")
async def metaltronus_decklist_helper(
    interaction: discord.Interaction,
    opponents_clipboard_ydk: str = None,
    your_clipboard_ydk: str = None,
    opponents_ydk_file: discord.Attachment = None,
    your_ydk_file: discord.Attachment = None
):
    # Defer the response and show the user that the bot is working on it
    await interaction.response.defer(thinking=True)

    # Get 2 decklists from the various input methods
    opponents_decklist, your_decklist = await formatter.format_two_decklist_inputs(interaction, opponents_clipboard_ydk, your_clipboard_ydk, opponents_ydk_file, your_ydk_file)

    # If a value is None, validation failed and message was already sent
    if opponents_decklist is None or your_decklist is None:
        return

    # Generate and send response
    response = metaltronus.metaltronus_decklist(interaction.guild.id, opponents_decklist, your_decklist)
    file_path = f"guilds/{interaction.guild.id}/docs/metaltronus_deck_compare.txt"
    with open(file_path, "rb") as file:
        await interaction.followup.send(response, file=discord.File(file_path))



#MARK: METALTRONUS SINGLE
@client.tree.command(name="metaltronus_single", description="Lists all the Metaltronus targets in the game for a specific card")
@app_commands.describe(monster_name="(Required): Any Yu-Gi-Oh! monster card name (Partial names work as well)")
async def metaltronus_single_helper(interaction: discord.Interaction, monster_name: str):
    # Defer the response and show the user that the bot is working on it
    await interaction.response.defer(thinking=True)

    # Create the response for the metaltronus output
    response = metaltronus.metaltronus_single(interaction.guild.id, monster_name)
    file_path = f"guilds/{interaction.guild.id}/docs/metaltronus_single.txt"
    with open(file_path, "rb") as file:
        await interaction.followup.send(response, file=discord.File(file_path))
# Adds autocomplete functionality to metaltronus function above
@metaltronus_single_helper.autocomplete("monster_name")
async def metaltronus_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return metaltronus.metaltronus_autocomplete(current_input)



# MARK: REPORT
@client.tree.command(name="report", description="Report a game's result")
@app_commands.describe(pairing="(Required): The text of the game you are reporting")
async def report_helper(interaction: discord.Interaction, pairing: str, ):
    await round_robin.report(interaction, pairing)
@report_helper.autocomplete("pairing")
async def report_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return await round_robin.report_autocomplete(interaction, current_input)



# MARK: ROUND ROBIN
@client.tree.command(name="roundrobin", description="Creates a 3-8 player Round Robin tournament, enter names with spaces in between")
@app_commands.describe(players="(Required): A sequence of player names seperated by spaces (Mike Evan Ben...)")
async def round_robin_bracket_helper(interaction: discord.Interaction, players: str):
    # Defer the response and show the user that the bot is working on it
    await interaction.response.defer(thinking=True)

    # Create the bracket and notify the players
    await round_robin.round_robin_bracket(interaction, players, interaction.guild.id)



# MARK: SEARCH PACK BY ARCHETYPE 
@client.tree.command(name="secretpack_archetype", description="Search for a specific Secret Pack by its contained archetypes")
@app_commands.describe(archetype_name="(Required): Any Yu-Gi-Oh! archetype name (Partial names work as well)")
async def search_by_archetype_helper(interaction: discord.Interaction, archetype_name: str):
    await saga.search_by_archetype(interaction, archetype_name)
@search_by_archetype_helper.autocomplete("archetype_name")
async def search_by_archetype_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return saga.search_by_archetype_autocomplete(current_input)



# MARK: SEARCH PACK BY TITLE 
@client.tree.command(name="secretpack_title", description="Search for a specific Secret Pack by its title")
@app_commands.describe(title="(Required): Any Master Duel Secret Pack title (Partial names work as well)")
async def search_by_title_helper(interaction: discord.Interaction, title: str):
    await saga.search_by_title(interaction, title)
@search_by_title_helper.autocomplete("title")
async def search_by_title_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return saga.search_by_title_autocomplete(current_input)



# MARK: SEVENTH TACHYON 
@client.tree.command(name="seventh_tachyon", description="Creates a list of all the current Seventh Tachyon targets in the game")
async def seventh_tachyon_list_helper(interaction: discord.Interaction):
    # Defer the response and show the user that the bot is working on it
    await interaction.response.defer(thinking=True)

    # Create the response for the metaltronus output
    response = seventh_tachyon.seventh_tachyon_list(interaction.guild.id)
    file_path = f"guilds/{interaction.guild.id}/docs/seventh_tachyon_targets.txt"
    with open(file_path, "rb") as file:
        await interaction.followup.send(response, file=discord.File(file_path))



# MARK: SEVENTH TACHYON DECKLIST 
@client.tree.command(name="seventh_tachyon_decklist", description="Lists all the Seventh Tachyon targets in your decklist")
@app_commands.describe(
    clipboard_ydk="(Use only 1 Method): Paste the copied \"Clipboard YDK\"", 
    ydk_file="(Use only 1 Method): Upload a .ydk file")
async def seventh_tachyon_decklist_helper(interaction: discord.Interaction, clipboard_ydk: str = None, ydk_file: discord.Attachment = None,):
    # Defer the response and show the user that the bot is working on it
    await interaction.response.defer(thinking=True)

    # Get 2 decklists from the various input methods
    decklist = await formatter.format_one_decklist_input(interaction, clipboard_ydk, ydk_file)
    
    # If decklist is None, validation failed and message was already sent
    if decklist is None:
        return

    # Create the response for the metaltronus output
    response = seventh_tachyon.seventh_tachyon_decklist(interaction.guild.id, decklist)
    file_path = f"guilds/{interaction.guild.id}/docs/seventh_tachyon_deck_targets.txt"
    with open(file_path, "rb") as file:
        await interaction.followup.send(response, file=discord.File(file_path))



# MARK: SMALL WORLD 
@client.tree.command(name="small_world", description="Find all the valid Small World bridges between 2 cards")
@app_commands.describe(
    first_card="(Required): Any Yu-Gi-Oh! Main Deck monster name (Partial names work as well)", 
    second_card="(Required): Any Yu-Gi-Oh! Main Deck monster name (Partial names work as well)")
async def small_world_pair_helper(interaction: discord.Interaction, first_card: str, second_card: str):
    # Defer the response and show the user that the bot is working on it
    await interaction.response.defer(thinking=True)

    # Create the response for the metaltronus output
    response = small_world.small_world_pair(interaction.guild.id, first_card, second_card)
    file_path = f"guilds/{interaction.guild.id}/docs/small_world.txt"
    with open(file_path, "rb") as file:
        await interaction.followup.send(response, file=discord.File(file_path))
@small_world_pair_helper.autocomplete("first_card")
@small_world_pair_helper.autocomplete("second_card")
async def small_world_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return small_world.small_world_autocomplete(current_input)



# MARK: SMALL WORLD DECKLIST 
@client.tree.command(name="small_world_decklist", description="Find all the valid Small World bridges within a decklist")
@app_commands.describe(
    clipboard_ydk="(Use only 1 Method): Paste the copied \"Clipboard YDK\"", 
    ydk_file="(Use only 1 Method): Upload a .ydk file")
async def small_world_decklist_helper(interaction: discord.Interaction, clipboard_ydk: str = None, ydk_file: discord.Attachment = None,):
    # Defer the response and show the user that the bot is working on it
    await interaction.response.defer(thinking=True)

    # Get 2 decklists from the various input methods
    decklist = await formatter.format_one_decklist_input(interaction, clipboard_ydk, ydk_file)
    
    # If decklist is None, validation failed and message was already sent
    if decklist is None:
        return

    # Create the response for the metaltronus output
    response = small_world.small_world_decklist(interaction.guild.id, decklist)
    file_path = f"guilds/{interaction.guild.id}/docs/small_world_decklist.txt"
    with open(file_path, "rb") as file:
        await interaction.followup.send(response, file=discord.File(file_path))



# MARK: SPIN
@client.tree.command(name="spin", description="Spin 5 random Secret Packs!")
async def secret_packs_helper(interaction: discord.Interaction):
    await saga.secret_packs(interaction)



# MARK: STANDINGS 
@client.tree.command(name="standings", description="See current season standings")
async def season_standings(interaction: discord.Interaction):
    await standings.graph_season_standings(interaction)



# MARK: TOP ARCHETYPE BREAKDOWN 
@client.tree.command(name="top_archetype_breakdown", description="View a card-by-card breakdown of a top archetype for the current format")
@app_commands.describe(archetype="(Required): Any Yu-Gi-Oh! archetype name (Partial names work as well)")
async def top_archetype_breakdown_helper(interaction: discord.Interaction, archetype: str):
    # Defer the response so multiple processes can use its webhook
    await interaction.response.defer(thinking=True)
    await top_archetype_breakdown.create_single_card_pagination(interaction, archetype)
@top_archetype_breakdown_helper.autocomplete("archetype")
async def archetype_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return await top_archetype_breakdown.archetype_autocomplete(current_input)



# MARK: TOP ARCHETYPES 
@client.tree.command(name="top_archetypes", description="View the top archetypes for the current format and their deck variants")
async def archetypes(interaction: discord.Interaction):
    # Defer the response so multiple processes can use its webhook
    await interaction.response.defer(thinking=True)
    await top_archetypes.get_top_archetypes(interaction)



# MARK: TOP CARDS 
@client.tree.command(name="top_cards", description="View a card's usage across all topping archetypes")
@app_commands.describe(card_name="(Required): Any Yu-Gi-Oh! card name (Partial names work as well)")
async def top_cards_helper(interaction: discord.Interaction, card_name: str):
    # Defer the response so multiple processes can use its webhook
    await interaction.response.defer(thinking=True)
    await top_cards.create_card_usage_pagination(interaction, card_name)
@top_cards_helper.autocomplete("card_name")
async def top_cards_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return await top_cards.card_autocomplete(current_input)



# MARK: TOURNAMENT INFO 
@client.tree.command(name="tournamentinfo", description="Find out what record is needed to receive an Invite or make Top Cut")
@app_commands.describe(number_of_players="(Required): Number of players in the tournament (Must be a whole number 32, 150...)")
async def tournament_info(interaction: discord.Interaction, number_of_players: int):
    await tournament.tournament_info(interaction, number_of_players)



# MARK: UPDATE
@client.tree.command(name="update", description="Updates all the databases found within the bot (takes a while to run)")
async def update_database(interaction: discord.Interaction):
    if update_lock.locked():
        await interaction.response.send_message("The bot is already in the process of updating its information.\nThis may have been triggered in another channel, or in another server.\nPlease wait till it finishes updating as it may take up to 15 minutes", ephemeral=True)
    async with update_lock:
        try:
            await formatter.update(interaction)
        except Exception as e:
            await interaction.response.send_message(f"Something went wrong during update:\n```{e}```", ephemeral=True)

client.run(os.getenv("BOT_TOKEN"))