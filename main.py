#TODO: possible get guild id locally rather than passed


import discord
from discord.ext import commands
from scripts import (help_pagination, round_robin, formatter, metaltronus, saga, seventh_tachyon, small_world, standings, top_archetype_breakdown, tournament, top_archetypes, top_cards, card_price_scraper, feedback)
from dotenv import load_dotenv
import os
import time
import asyncio

# Load the environment variables
load_dotenv()

# Variables
intents = discord.Intents.default()
intents.message_content = True
global_command_cooldown_rate = 2  # In seconds
list_of_users_on_cooldown = {}
update_lock = asyncio.Lock() # Lock to prevent multiple instances of the /update command from running at the same time
guild_id_as_int = os.getenv("TEST_SERVER_ID")  # Unique server ID for slash commands to speed up build time
GUILD_ID = discord.Object(id=guild_id_as_int)  # Unique server ID for slash commands to speed up build time

class Client(commands.Bot):
    async def on_ready(self):
        # Logged in successfully
        print(f'Logged on as {self.user}!')

        # Try to sync commands to server
        try:
            guild = GUILD_ID
            synced = await self.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands to guild {guild.id}')
        except Exception as e:
            print(f'Error syncing commands: {e}')

# Create the client
client = Client(command_prefix="!", intents=intents)

# Checks if the user is on cooldown for using too many commands, called before every command
async def is_on_cooldown(interaction: discord.Interaction):
    current_time = time.time()
    user_id = interaction.user.id

    # If the user is already in the cooldowns list
    if user_id in list_of_users_on_cooldown and current_time - list_of_users_on_cooldown[user_id] < global_command_cooldown_rate:
        # Get how much time they have left
        current_cooldown = round(global_command_cooldown_rate - (current_time - list_of_users_on_cooldown[user_id]), 2)
        cooldown_end_timestamp = int(current_time + current_cooldown)
        cooldown_message = f"You're on cooldown! Please Try again <t:{cooldown_end_timestamp}:R>."

        # Respond with how long they have until the cooldown is over, then delete the messages once the cooldown is over
        await interaction.response.send_message(cooldown_message, ephemeral=True)
        await asyncio.sleep(current_cooldown)
        await interaction.delete_original_response()

        # Return a boolean so calling this function returns a usable variable
        return True
    
    # Adds the user to the cooldown array
    list_of_users_on_cooldown[user_id] = current_time

    return False



# ===== UPDATE DATABASES =====
@client.tree.command(name="update", description="NOTE: TAKES UP TO 15 MINUTES, Updates all databases", guild=GUILD_ID)
async def update_database(interaction: discord.Interaction):
    if not await is_on_cooldown(interaction):
        if update_lock.locked():
            await interaction.response.send_message("The bot is already in the process of updating its information.\nThis may have been triggered in another channel, or in another server.\nPlease wait till it finishes updating as it may take up to 15 minutes", ephemeral=True)
        async with update_lock:
            try:
                await formatter.update(interaction)
            except Exception as e:
                await interaction.response.send_message(f"Something went wrong during update:\n```{e}```", ephemeral=True)

# ===== METALTRONUS SINGLE =====
@client.tree.command(name="metaltronus_single", description="Lists all the Metaltronus targets for a specific card", guild=GUILD_ID)
async def metaltronus_single(interaction: discord.Interaction, input: str):
    if not await is_on_cooldown(interaction) and guild_id_as_int:
        # Defer the rersponse and show the user that the bot is working on it
        await interaction.response.defer(thinking=True)

        # Create the response for the metaltronus output
        response = metaltronus.metaltronus_single(guild_id_as_int, input)
        file_path = f"guilds/{guild_id_as_int}/docs/metaltronus_single.txt"
        with open(file_path, "rb") as file:
            await interaction.followup.send(response, file=discord.File(file_path))
# Adds autocomplete functionality to metaltronus function above
@metaltronus_single.autocomplete("input")
async def metaltronus_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return metaltronus.metaltronus_autocomplete(current_input)

# ===== METALTRONUS DECKLISTS =====
@client.tree.command(name="metaltronus_decklist", description="Lists all the Metaltronus targets your deck has against an opponent's deck", guild=GUILD_ID)
async def metaltronus_decklist(
    interaction: discord.Interaction,
    opponents_clipboard_ydk: str = None,
    your_clipboard_ydk: str = None,
    opponents_ydk_file: discord.Attachment = None,
    your_ydk_file: discord.Attachment = None
):
    if not await is_on_cooldown(interaction):
        # Defer the rersponse and show the user that the bot is working on it
        await interaction.response.defer(thinking=True)

        # Get 2 decklists from the varrious imput methods
        opponents_decklist, your_decklist = await formatter.format_two_decklist_inputs(interaction, opponents_clipboard_ydk, your_clipboard_ydk, opponents_ydk_file, your_ydk_file)

        # If a value is None, validation failed and message was already sent
        if opponents_decklist is None or your_decklist is None:
            return

        # Generate and send response
        response = metaltronus.metaltronus_decklist(guild_id_as_int, opponents_decklist, your_decklist)
        file_path = f"guilds/{guild_id_as_int}/docs/metaltronus_deck_compare.txt"
        with open(file_path, "rb") as file:
            await interaction.followup.send(response, file=discord.File(file_path))

# ===== SEVENTH TACHYON =====
@client.tree.command(name="seventh_tachyon", description="Create list of all the current Seventh Tachyon targets in the game", guild=GUILD_ID)
async def seventh_tachyon_list(interaction: discord.Interaction):
    if not await is_on_cooldown(interaction):
        # Defer the rersponse and show the user that the bot is working on it
        await interaction.response.defer(thinking=True)

        # Create the response for the metaltronus output
        response = seventh_tachyon.seventh_tachyon_list(guild_id_as_int)
        file_path = f"guilds/{guild_id_as_int}/docs/seventh_tachyon_targets.txt"
        with open(file_path, "rb") as file:
            await interaction.followup.send(response, file=discord.File(file_path))

# ===== SEVENTH TACHYON DECKLIST =====
@client.tree.command(name="seventh_tachyon_decklist", description="Lists all the Seventh Tachyon targets in your decklist", guild=GUILD_ID)
async def seventh_tachyon_decklist(interaction: discord.Interaction, clipboard_ydk: str = None, ydk_file: discord.Attachment = None,):
    if not await is_on_cooldown(interaction):
        # Defer the rersponse and show the user that the bot is working on it
        await interaction.response.defer(thinking=True)

        # Get 2 decklists from the varrious imput methods
        decklist = await formatter.format_one_decklist_input(interaction, clipboard_ydk, ydk_file)
        
        # If decklist is None, validation failed and message was already sent
        if decklist is None:
            return

        # Create the response for the metaltronus output
        response = seventh_tachyon.seventh_tachyon_decklist(guild_id_as_int, decklist)
        file_path = f"guilds/{guild_id_as_int}/docs/seventh_tachyon_deck_targets.txt"
        with open(file_path, "rb") as file:
            await interaction.followup.send(response, file=discord.File(file_path))

# ===== SMALL WORLD =====
@client.tree.command(name="small_world", description="Find all the valid Small World bridges between 2 cards", guild=GUILD_ID)
async def small_world_pair(interaction: discord.Interaction, first_card: str, second_card: str):
    if not await is_on_cooldown(interaction):
        # Defer the rersponse and show the user that the bot is working on it
        await interaction.response.defer(thinking=True)

        # Create the response for the metaltronus output
        response = small_world.small_world_pair(guild_id_as_int, first_card, second_card)
        file_path = f"guilds/{guild_id_as_int}/docs/small_world.txt"
        with open(file_path, "rb") as file:
            await interaction.followup.send(response, file=discord.File(file_path))
#Adds autocomplete functionality to small world pair function above
@small_world_pair.autocomplete("first_card")
@small_world_pair.autocomplete("second_card")
async def small_world_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return small_world.small_world_autocomplete(current_input)

# ===== SMALL WORLD DECKLIST =====
@client.tree.command(name="small_world_decklist", description="Find all the valid Small World bridges within a decklist", guild=GUILD_ID)
async def small_world_decklist(interaction: discord.Interaction, clipboard_ydk: str = None, ydk_file: discord.Attachment = None,):
    if not await is_on_cooldown(interaction):
        # Defer the rersponse and show the user that the bot is working on it
        await interaction.response.defer(thinking=True)

        # Get 2 decklists from the varrious imput methods
        decklist = await formatter.format_one_decklist_input(interaction, clipboard_ydk, ydk_file)
        
        # If decklist is None, validation failed and message was already sent
        if decklist is None:
            return

        # Create the response for the metaltronus output
        response = small_world.small_world_decklist(guild_id_as_int, decklist)
        file_path = f"guilds/{guild_id_as_int}/docs/small_world_decklist.txt"
        with open(file_path, "rb") as file:
            await interaction.followup.send(response, file=discord.File(file_path))

# ===== TOURNAMENT INFO =====
@client.tree.command(name="tournamentinfo", description="Find out what record is needed to receive an Invite or make Top Cut, for a given number of players", guild=GUILD_ID)
async def tournament_info(interaction: discord.Interaction, players: int):
    if not await is_on_cooldown(interaction):
        await tournament.tournament_info(interaction, players)

# ===== SPIN SECRET PACKS =====
@client.tree.command(name="spin", description="Spin 5 random Secret Packs!", guild=GUILD_ID)
async def secret_packs(interaction: discord.Interaction):
    if not await is_on_cooldown(interaction):
        await saga.secret_packs(interaction)

# ===== MASTER PACK INFO =====
@client.tree.command(name="masterpack", description="Posts the link to open Master Packs", guild=GUILD_ID)
async def master_packs(interaction: discord.Interaction):
    if not await is_on_cooldown(interaction):
        await interaction.response.send_message(embed=saga.master_packs())

# ===== EARCH PACK BY ARCHETYPE =====
@client.tree.command(name="secretpack_archetype", description="Search for a specific Secret Pack by archetype", guild=GUILD_ID)
async def search_by_archetype(interaction: discord.Interaction, input: str):
    if not await is_on_cooldown(interaction):
        await saga.search_by_archetype(interaction, input)
@search_by_archetype.autocomplete("input")
async def search_by_archetype_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return saga.search_by_archetype_autocomplete(current_input)

# ===== SEARCH PACK BY TITLE =====
@client.tree.command(name="secretpack_title", description="Search for a specific Secret Pack by its title", guild=GUILD_ID)
async def search_by_title(interaction: discord.Interaction, input: str):
    if not await is_on_cooldown(interaction):
        await saga.search_by_title(interaction, input)
@search_by_title.autocomplete("input")
async def search_by_title_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return saga.search_by_title_autocomplete(current_input)

# ===== ROUND ROBIN TOURNAMENT =====
@client.tree.command(name="roundrobin", description="Create a 3-8 player Round Robin tournament, please enter names with spaces inbetween", guild=GUILD_ID)
async def round_robin_bracket(interaction: discord.Interaction, players: str):
    if not await is_on_cooldown(interaction):
        # Defer the rersponse and show the user that the bot is working on it
        await interaction.response.defer(thinking=True)

        # Create the bracket and notify the players
        await round_robin.round_robin_bracket(interaction, players, guild_id_as_int)

# ===== REPORT TOURNAMENT =====
@client.tree.command(name="report", description="Report a game's result", guild=GUILD_ID)
async def report(interaction: discord.Interaction, result: str, ):
    if not await is_on_cooldown(interaction):
        await round_robin.report(interaction, result)
@report.autocomplete("result")
async def report_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return await round_robin.report_autocomplete(interaction, current_input)

# ===== SEASON STANDINGS =====
@client.tree.command(name="standings", description="See current season standings", guild=GUILD_ID)
async def season_standings(interaction: discord.Interaction):
    if not await is_on_cooldown(interaction):
        await standings.graph_season_standings(interaction)

# ===== TOP ARCHETYPES =====
@client.tree.command(name="top_archetypes", description="View the top archetypes for the current format", guild=GUILD_ID)
async def archetypes(interaction: discord.Interaction):
    if not await is_on_cooldown(interaction):
        await top_archetypes.get_top_archetypes(interaction)

# ===== TOP ARCHETYPE BREAKDOWN =====
@client.tree.command(name="top_archetype_breakdown", description="View a card-by-card breakdown of a top archetype for the current format", guild=GUILD_ID)
async def top_archetype_breakdown_helper(interaction: discord.Interaction, archetype: str):
    if not await is_on_cooldown(interaction):
        await top_archetype_breakdown.create_single_card_pagination(interaction, archetype)
@top_archetype_breakdown_helper.autocomplete("archetype")
async def archetype_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return await top_archetype_breakdown.archetype_autocomplete(current_input)

# ===== TOP CARDS =====
@client.tree.command(name="top_cards", description="View a card's usage across all topping archetypes", guild=GUILD_ID)
async def top_cards_helper(interaction: discord.Interaction, card_name: str):
    if not await is_on_cooldown(interaction):
        await top_cards.create_card_usage_pagination(interaction, card_name)
@top_cards_helper.autocomplete("card_name")
async def top_cards_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return await top_cards.card_autocomplete(current_input)

# ===== CARD PRICE =====
@client.tree.command(name="card_price", description="View a card's pricing from TCG Player", guild=GUILD_ID)
async def card_price_helper(interaction: discord.Interaction, card_name: str):
    if not await is_on_cooldown(interaction):
        # Defer the response so multiple processes can use its webhook
        await interaction.response.defer(thinking=True)

        message = await interaction.followup.send("Starting script...")
        await card_price_scraper.pull_data_from_tcg_player(guild_id_as_int, message, card_name)
@card_price_helper.autocomplete("card_name")
async def card_price_autocomplete_handler(interaction: discord.Interaction, current_input: str):
    return formatter.card_name_autocomplete(current_input)

# ===== FEEDBACK =====
@client.tree.command(name="feedback", description="Send the creator of Duelkit a message!", guild=GUILD_ID)
async def feedback_helper(interaction: discord.Interaction, input: str):
    if not await is_on_cooldown(interaction) and not await feedback.is_on_feedback_cooldown(interaction):
        await feedback.send_feedback(interaction, input)

# ===== HELP =====
@client.tree.command(name="help", description="Learn more about the list of available commands", guild=GUILD_ID)
async def help_helper(interaction: discord.Interaction):
    if not await is_on_cooldown(interaction):
        # Defer the response so multiple processes can use its webhook
        await interaction.response.defer(thinking=True)

        await help_pagination.show_help_pagination(interaction)

client.run(os.getenv("BOT_TOKEN"))