import discord
import json
import random

# Creates the random secret packs
async def secret_packs(interaction: discord.Interaction, number_of_spins: int = None):
    # Read the master_data JSON
    with open('global/json/master_data.json', 'r', encoding="utf-8") as file:
        master_data = json.load(file)
        
    # Set Default
    num_spins = 5

    # Check if Default is changed
    if number_of_spins:
        # Enforce Discord's limit of 10 spins per interaction
        if number_of_spins > 10:
            num_spins = 10
        else :
            num_spins = number_of_spins

    # Get all packs
    all_packs = master_data["packs"]

    # "random.sample" does not return duplicates
    selected_packs = random.sample(all_packs, num_spins)

    # Send out embeds
    embeds_list = [create_secret_pack_embed(pack) for pack in selected_packs]
    await interaction.response.send_message(embeds=embeds_list)

# Creates the master pack embed
def master_packs():
    embed = discord.Embed(title="Master Pack", url="https://ygoprodeck.com/pack/Master%20Pack/MD/", color=0xbbaa5e)
    embed.add_field(name="**Included Archetypes:**", value="```Everything```", inline=True)
    embed.add_field(name="https://ygoprodeck.com/pack-sim/", value="```Master Pack```", inline=False)
    embed.set_image(url="https://images.ygoprodeck.com/images/sets/Master_Pack.jpg")
    return embed

# Generates the secret pack information for a given archetype
async def search_by_archetype(interaction: discord.Interaction, input: str):
    # Read the master_data JSON
    with open('global/json/master_data.json', 'r', encoding="utf-8") as file:
        master_data = json.load(file)
        
    embeds_list = []

    # List of packs that match the query
    matching_packs = find_matching_packs(master_data["packs"], input)

    # For every pack with that archetype
    for pack in matching_packs:
        # Create the secret pack embed
        embeds_list.append(create_secret_pack_embed(pack))

        # If all the secret pack embeds have been generated
        if (len(embeds_list) == len(matching_packs)):
            await interaction.response.send_message(embeds=embeds_list) 

# Returns a list of secret packs that contain the given archetype
def find_matching_packs(packs, search_input):
    return [
        pack for pack in packs
        if any(search_input.lower().strip() in archetype.lower().strip() for archetype in pack.get("archetypes", []))
    ]

# Generates the secret pack information for a given pack title
async def search_by_title(interaction: discord.Interaction, input: str):
    # Read the master_data JSON
    with open('global/json/master_data.json', 'r', encoding="utf-8") as file:
        master_data = json.load(file)
        
    # Embedded list for multiple results
    embeds_list = []

    # List of packs that match the query
    matching_packs = find_matching_packs_by_title(master_data["packs"], input)

    # For every pack with that title
    for pack in matching_packs:
        # Create the secret pack embed
        embeds_list.append(create_secret_pack_embed(pack))

        # If all the secret pack embeds have been generated
        if (len(embeds_list) == len(matching_packs)):
            await interaction.response.send_message(embeds=embeds_list) 

# Returns a list of secret packs that contain the given title
def find_matching_packs_by_title(packs, search_input):
    return [
        pack for pack in packs
        if search_input.lower().strip() in pack.get("title", "").lower().strip()
    ]

# Creates the secret pack embed from a "packs" object, see master_data.json
def create_secret_pack_embed(secret_pack):
    embed = discord.Embed(title=secret_pack["title"], url=secret_pack["view_url"], color=0xbbaa5e)
        
    # Set archetype text
    archetypes = ""
    for item in secret_pack["archetypes"]:
        archetypes = f"{archetypes}```{item}```"
    embed.add_field(name="**Included Archetypes:**", value=archetypes)
    
    # Set ygopro link
    embed.add_field(name="https://ygoprodeck.com/pack-sim/", value=f"```{secret_pack['title']}```", inline=False)

    # Set card image
    embed.set_image(url=secret_pack["image_url"])

    return embed

def search_by_archetype_autocomplete(current_input: str):
    with open('global/json/master_data.json', 'r', encoding="utf-8") as file:
        secret_pack_database = json.load(file)
    archetypes = set()
    for pack in secret_pack_database["packs"]:
        archetypes.update(pack["archetypes"])
    unique_archetypes = sorted(archetypes)
    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in unique_archetypes
        if current_input.lower() in name.lower()
    ][:25]

def search_by_title_autocomplete(current_input: str):
    with open('global/json/master_data.json', 'r', encoding="utf-8") as file:
        secret_pack_database = json.load(file)
    
    secret_pack_titles = [pack['title'] for pack in secret_pack_database['packs']]

    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in secret_pack_titles
        if current_input.lower() in name.lower()
    ][:25]