import discord
import json
import math
from scripts import formatter
from collections import Counter, defaultdict


class TopArchetypeBreakdownPaginationView(discord.ui.View):
    def __init__(self, total_decks: int, archetype: str, card_data):
        # Prevent Timeout
        super().__init__(timeout=None)

        # Set values
        self.total_decks = total_decks
        self.archetype = archetype
        self.current_page = 1
        self.entries_per_page = 5
        self.card_data = card_data
        self.max_pages = math.ceil(len(self.card_data) / self.entries_per_page)
        self.message = None     # No initial message on startup

    # Starts the pagination system and sends the initial message
    async def start(self, interaction: discord.Interaction):
        # Set page on startup
        self.current_page = 1

        # Disabled the page number button
        self.page_number_button.disabled = True

        # Set initial button states
        self.update_buttons()

        # Creates the welcome message embed
        embed = self.create_embed(self.get_current_page_entries())

        # Sends the embed
        self.message = await interaction.followup.send(embed=embed, view=self)

    # Updates the button states, and sends the message
    async def update_message(self):
        # Updates button states
        self.update_buttons()

        # Creates a new embed
        embed = self.create_embed(self.get_current_page_entries())

        # Edit previous message, and send the new embed
        await self.message.edit(embed=embed, view=self)

    # Creates the embed
    def create_embed(self, card_data):
        embed = discord.Embed(title=f"{formatter.smart_capitalize(self.archetype)} Card Usage - {self.total_decks} Decks", color=discord.Color.dark_gold())

        # For every card
        for card_name, usage_data in card_data:
            sections = []

            # Formats the text for the main, extra, and side deck counts
            def format_deck_counts(count_dict):
                return "\n".join(f"{copies}x: {count}" for copies, count in sorted(count_dict.items(), reverse=True))

            if usage_data["main"]:
                sections.append(f"```Main Deck:\n{format_deck_counts(usage_data['main'])}```")
            if usage_data["extra"]:
                sections.append(f"```Extra Deck:\n{format_deck_counts(usage_data['extra'])}```")
            if usage_data["side"]:
                sections.append(f"```Side Deck:\n{format_deck_counts(usage_data['side'])}```")

            embed.add_field(
                name=f"**{card_name}** - *{usage_data['deck_percentage']}*",
                value="".join(sections) if sections else "No data available",
                inline=False
            )
        embed.set_footer(text=f"As of: {formatter.get_current_date()}")

        return embed

    # Updates the button states
    def update_buttons(self):
        # Set current page number
        self.page_number_button.label = f"{self.current_page}/{self.max_pages}"

        # Disable the "previous" and "first page" buttons if its the first page
        self.first_page_button.disabled = self.current_page == 1
        self.first_page_button.style = discord.ButtonStyle.gray if self.first_page_button.disabled else discord.ButtonStyle.green
        self.prev_button.disabled = self.current_page == 1
        self.prev_button.style = discord.ButtonStyle.gray if self.prev_button.disabled else discord.ButtonStyle.primary

        # Disable the "next" and "last page" buttons if its the last page
        self.last_page_button.disabled = self.current_page == self.max_pages
        self.last_page_button.style = discord.ButtonStyle.gray if self.last_page_button.disabled else discord.ButtonStyle.green
        self.next_button.disabled = self.current_page == self.max_pages
        self.next_button.style = discord.ButtonStyle.gray if self.next_button.disabled else discord.ButtonStyle.primary

    # Gets the current page entries from the dataset
    def get_current_page_entries(self):
        self.current_page = max(1, min(self.current_page, self.max_pages))

        # Calculate the start and end indices for the current page
        start = (self.current_page - 1) * self.entries_per_page
        end = start + self.entries_per_page
        return self.card_data[start:end]

    @discord.ui.button(label="|<", style=discord.ButtonStyle.green)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update current page, then update message
        self.current_page = 1
        await self.update_message()

        # Prevent buttons from auto-clicking a second time
        await interaction.response.defer()

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update current page, then update message
        self.current_page -= 1
        await self.update_message()

        # Prevent buttons from auto-clicking a second time
        await interaction.response.defer()

    @discord.ui.button(label="/", style=discord.ButtonStyle.grey)
    async def page_number_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update current page, then update message
        self.current_page += 1
        await self.update_message()

        # Prevent buttons from auto-clicking a second time
        await interaction.response.defer()

    @discord.ui.button(label=">|", style=discord.ButtonStyle.green)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update current page, then update message
        self.current_page = self.max_pages
        await self.update_message()

        # Prevent buttons from auto-clicking a second time
        await interaction.response.defer()


async def create_single_card_pagination(interaction: discord.Interaction, archetype: str):
    card_data, total_decks = count_card_occurrences(archetype)
    if total_decks == 0:
        await interaction.response.send_message(f"There are no topping decklists for `{formatter.smart_capitalize(archetype)}` in the current format") 
        return

    card_data = sorted(card_data.items(), key=lambda x: x[0])  # Sort alphabetically by card name
    view = TopArchetypeBreakdownPaginationView(total_decks=total_decks, archetype=archetype, card_data=card_data)

    # await view.send(interaction)
    await view.start(interaction)

# Returns all the decklists for a given archetype
def load_decklists(archetype: str):
    with open('global/json/topping_decklists.json', 'r', encoding="utf-8") as file:
        data = json.load(file)
    archetype_name = formatter.smart_capitalize(archetype)

    return {deck_key: deck_value["deck_list"] for deck_key, deck_value in data.get(archetype_name, {}).get("decks", {}).items()}

# Defines the structure of the card counters
def initialize_card_counters():
    return {
        "main": defaultdict(Counter),
        "extra": defaultdict(Counter),
        "side": defaultdict(Counter)
    }

# Counts the cards in the deck and updates the card counts and appearances
def count_cards_in_deck(deck, card_counts, card_deck_appearances, deck_id):
    for deck_type, count_type in [("main_deck", "main"), ("extra_deck", "extra"), ("side_deck", "side")]:
        if deck_type in deck:
            card_counter = Counter(deck[deck_type])
            for card_name, count in card_counter.items():
                card_counts[count_type][card_name][count] += 1
                card_deck_appearances[card_name].add(deck_id)  # Track unique decks

# Get the card name and its info from the deck
def count_card_occurrences(archetype: str):
    archetype_decks = load_decklists(archetype)
    card_counts = initialize_card_counters()
    card_deck_appearances = defaultdict(set)  # Track how many decks each card appeared in

    for deck_id, deck in archetype_decks.items():
        count_cards_in_deck(deck, card_counts, card_deck_appearances, deck_id)

    total_decks = len(archetype_decks)  # Count total number of decks

    return (
        {
            card_name: {
                "main": card_counts["main"][card_name],
                "extra": card_counts["extra"][card_name],
                "side": card_counts["side"][card_name],
                "deck_percentage": f"{(len(card_deck_appearances[card_name]) / total_decks) * 100:.1f}%"  # Convert to a percentage
            }
            for card_name in sorted(set(card_counts["main"]) | set(card_counts["extra"]) | set(card_counts["side"]))  # Sort alphabetically
        },
        total_decks
    )

# Get all archetypes from the JSON file
def get_all_archetypes():
    with open('global/json/topping_decklists.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    return list(data.keys())

# Autocomplete function for archetypes
async def archetype_autocomplete(current_input: str):
    archetypes = sorted(get_all_archetypes())
    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in archetypes
        if current_input.lower() in name.lower()
    ][:25]