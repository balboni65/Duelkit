import discord
import json
import math
from scripts import formatter
from collections import Counter, defaultdict


class PaginationView(discord.ui.View):
    current_page: int = 1
    entries_per_page: int = 5  # Show 5 cards per page

    def __init__(self, total_decks: int, archetype: str):
        super().__init__(timeout=None)
        self.total_decks = total_decks  # Store total_decks value
        self.archetype = archetype

    async def send(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Here are all the cards played in topping {formatter.smart_capitalize(self.archetype)} decks:")
        self.message = await interaction.followup.send(view=self)

        if self.message:
            await self.update_message(self.get_current_page())

    async def update_message(self, data):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)

    def create_embed(self, data):
        embed = discord.Embed(title=f"{formatter.smart_capitalize(self.archetype)} Card Usage - {self.total_decks} Decks", color=discord.Color.dark_gold())

        for card_name, usage_data in data:
            sections = []

            def format_counts(count_dict):
                return "\n".join(f"{copies}x: {count}" for copies, count in sorted(count_dict.items(), reverse=True))

            if usage_data["main"]:
                sections.append(f"```Main Deck:\n{format_counts(usage_data['main'])}```")
            if usage_data["extra"]:
                sections.append(f"```Extra Deck:\n{format_counts(usage_data['extra'])}```")
            if usage_data["side"]:
                sections.append(f"```Side Deck:\n{format_counts(usage_data['side'])}```")

            embed.add_field(
                name=f"**{card_name}** - *{usage_data['deck_percentage']}*",
                value="".join(sections) if sections else "No data available",
                inline=False
            )

        return embed


    def update_buttons(self):
        max_pages = math.ceil(len(self.data) / self.entries_per_page)

        self.page_number_button.disabled = True
        self.page_number_button.label = f"{self.current_page}/{max_pages}"

        self.first_page_button.disabled = self.current_page == 1
        self.prev_button.disabled = self.current_page == 1
        self.next_button.disabled = self.current_page == max_pages
        self.last_page_button.disabled = self.current_page == max_pages

        self.first_page_button.style = discord.ButtonStyle.gray if self.first_page_button.disabled else discord.ButtonStyle.green
        self.prev_button.style = discord.ButtonStyle.gray if self.prev_button.disabled else discord.ButtonStyle.primary
        self.next_button.style = discord.ButtonStyle.gray if self.next_button.disabled else discord.ButtonStyle.primary
        self.last_page_button.style = discord.ButtonStyle.gray if self.last_page_button.disabled else discord.ButtonStyle.green

    def get_current_page(self):
        max_pages = math.ceil(len(self.data) / self.entries_per_page)
        self.current_page = max(1, min(self.current_page, max_pages))

        start = (self.current_page - 1) * self.entries_per_page
        end = start + self.entries_per_page
        return self.data[start:end]

    @discord.ui.button(label="|<", style=discord.ButtonStyle.green)
    async def first_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 1
        await self.update_message(self.get_current_page())

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.current_page > 1:
            self.current_page -= 1
        await self.update_message(self.get_current_page())

    @discord.ui.button(label="/", style=discord.ButtonStyle.grey)
    async def page_number_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.update_message(self.get_current_page())

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        max_pages = math.ceil(len(self.data) / self.entries_per_page)
        if self.current_page < max_pages:
            self.current_page += 1
        await self.update_message(self.get_current_page())

    @discord.ui.button(label=">|", style=discord.ButtonStyle.green)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = math.ceil(len(self.data) / self.entries_per_page)
        await self.update_message(self.get_current_page())


async def create_single_card_pagination(interaction: discord.Interaction, archetype: str):
    card_data, total_decks = count_card_occurrences(archetype)
    if total_decks == 0:
        await interaction.response.send_message(f"There are no topping decklists for `{formatter.smart_capitalize(archetype)}` in the current format") 
        return

    pagination_view = PaginationView(total_decks=total_decks, archetype=archetype)
    pagination_view.data = sorted(card_data.items(), key=lambda x: x[0])  # Sort alphabetically by card name

    await pagination_view.send(interaction)


def load_decklists(archetype: str):
    with open('global/json/topping_decklists.json', 'r', encoding="utf-8") as file:
        data = json.load(file)
    archetype_name = formatter.smart_capitalize(archetype)

    return {deck_key: deck_value["deck_list"] for deck_key, deck_value in data.get(archetype_name, {}).get("decks", {}).items()}


def initialize_card_counters():
    return {
        "main": defaultdict(Counter),
        "extra": defaultdict(Counter),
        "side": defaultdict(Counter)
    }


def count_cards_in_deck(deck, card_counts, card_deck_appearances, deck_id):
    for deck_type, count_type in [("main_deck", "main"), ("extra_deck", "extra"), ("side_deck", "side")]:
        if deck_type in deck:
            card_counter = Counter(deck[deck_type])
            for card_name, count in card_counter.items():
                card_counts[count_type][card_name][count] += 1
                card_deck_appearances[card_name].add(deck_id)  # Track unique decks




def count_card_occurrences(archetype: str):
    ryzeal_decks = load_decklists(archetype)
    card_counts = initialize_card_counters()
    card_deck_appearances = defaultdict(set)  # Track in how many decks each card appeared

    for deck_id, deck in ryzeal_decks.items():
        count_cards_in_deck(deck, card_counts, card_deck_appearances, deck_id)

    total_decks = len(ryzeal_decks)  # Count total number of decks

    return (
        {
            card_name: {
                "main": card_counts["main"][card_name],
                "extra": card_counts["extra"][card_name],
                "side": card_counts["side"][card_name],
                "deck_percentage": f"{(len(card_deck_appearances[card_name]) / total_decks) * 100:.1f}%"  # Convert to percentage
            }
            for card_name in sorted(set(card_counts["main"]) | set(card_counts["extra"]) | set(card_counts["side"]))  # Sort alphabetically
        },
        total_decks
    )

def get_all_archetypes():
    with open('global/json/topping_decklists.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    return list(data.keys())


async def archetype_autocomplete(current_input: str):
    archetypes = sorted(get_all_archetypes())
    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in archetypes
        if current_input.lower() in name.lower()
    ][:25]