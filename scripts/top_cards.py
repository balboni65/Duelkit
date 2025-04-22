import discord
import json
import math
from scripts import formatter
from collections import Counter, defaultdict


class PaginationView(discord.ui.View):
    current_page: int = 1
    entries_per_page: int = 5

    def __init__(self, total_decks_per_archetype: dict, card_name: str):
        super().__init__(timeout=None)
        self.total_decks_per_archetype = total_decks_per_archetype
        self.card_name = card_name

    async def send(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Here is how **{self.card_name}** is used across all topping archetypes:")
        self.message = await interaction.followup.send(view=self)

        if self.message:
            await self.update_message(self.get_current_page())

    async def update_message(self, data):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)

    def create_embed(self, data):
        embed = discord.Embed(title=f"{self.card_name} Usage:", color=discord.Color.dark_gold())

        for archetype, usage_data in data:
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
                name=f"**{archetype}** - {usage_data['deck_percentage']}",
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


async def create_card_usage_pagination(interaction: discord.Interaction, card_name: str):
    card_usage_data, total_decks_per_archetype = count_card_usage_in_all_archetypes(card_name)
    if not card_usage_data:
        await interaction.response.send_message(f"No topping decks include {card_name} in the current format.")
        return

    pagination_view = PaginationView(total_decks_per_archetype, card_name)
    pagination_view.data = sorted(card_usage_data.items(), key=lambda x: x[0])

    await pagination_view.send(interaction)


def count_card_usage_in_all_archetypes(target_card_name: str):
    with open('global/json/topping_decklists.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    results = {}
    total_decks_per_archetype = {}

    for archetype, archetype_data in data.items():
        card_counts = {
            "main": Counter(),
            "extra": Counter(),
            "side": Counter()
        }
        deck_appearances = set()

        decks = archetype_data.get("decks", {})
        total_decks = len(decks)
        total_decks_per_archetype[archetype] = total_decks

        for deck_id, deck_info in decks.items():
            deck_list = deck_info.get("deck_list", {})

            for section, key in [("main", "main_deck"), ("extra", "extra_deck"), ("side", "side_deck")]:
                if key in deck_list:
                    card_counter = Counter(deck_list[key])
                    if target_card_name in card_counter:
                        card_counts[section][card_counter[target_card_name]] += 1
                        deck_appearances.add(deck_id)

        if deck_appearances:
            results[archetype] = {
                "main": card_counts["main"],
                "extra": card_counts["extra"],
                "side": card_counts["side"],
                "deck_percentage": f"{(len(deck_appearances) / total_decks) * 100:.1f}%"
            }

    return results, total_decks_per_archetype


def get_all_card_names():
    with open('global/json/topping_decklists.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

    card_set = set()
    for archetype_data in data.values():
        for deck_data in archetype_data.get("decks", {}).values():
            deck = deck_data.get("deck_list", {})
            for part in ["main_deck", "extra_deck", "side_deck"]:
                card_set.update(deck.get(part, []))

    return sorted(card_set)


async def card_autocomplete(current_input: str):
    card_names = get_all_card_names()
    return [
        discord.app_commands.Choice(name=name, value=name)
        for name in card_names
        if current_input.lower() in name.lower()
    ][:25]
