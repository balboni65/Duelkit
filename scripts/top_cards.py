import discord
import json
import math
from collections import Counter
from scripts import formatter


class TopCardsPaginationView(discord.ui.View):
    current_page: int = 1
    entries_per_page: int = 5

    def __init__(self, total_decks_per_archetype: dict, card_name: str, data):
        super().__init__(timeout=None)
        self.total_decks_per_archetype = total_decks_per_archetype
        self.card_name = card_name
        self.data = data
        self.max_pages = math.ceil(len(self.data) / self.entries_per_page)

    # Starts the pagination system and sends the initial message
    async def start(self, interaction: discord.Interaction):
        # Set page on startup
        self.current_page = 1

        # Disabled the page number button
        self.page_number_button.disabled = True

        # Set initial button states
        self.update_buttons()

        # Creates the first embed
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

    def create_embed(self, data):
        embed = discord.Embed(title=f"{self.card_name} Usage:", color=0xbbaa5e)

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
                name=f"**{archetype}** - *{usage_data['deck_percentage']} of decks*",
                value="".join(sections) if sections else "No Data Available",
                inline=False
            )

        return embed

    # Update the button states
    def update_buttons(self):
        # Set current page number
        self.page_number_button.label = f"{self.current_page}/{self.max_pages}"

        # Disable the "previous" button if its the first page
        self.prev_button.disabled = self.current_page == 1

        # Disabled the "next" button if its the last page
        self.next_button.disabled = self.current_page == self.max_pages

        # Set the "previous" button color
        if self.prev_button.disabled:
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.prev_button.style = discord.ButtonStyle.primary
        
        # Set the "next" button color
        if self.next_button.disabled:
            self.next_button.style = discord.ButtonStyle.gray
        else:
            self.next_button.style = discord.ButtonStyle.primary

    # Gets the current page entries from the dataset
    def get_current_page_entries(self):
        self.current_page = max(1, min(self.current_page, self.max_pages))

        # Calculate the start and end indices for the current page
        start = (self.current_page - 1) * self.entries_per_page
        end = start + self.entries_per_page
        return self.data[start:end]

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


async def create_card_usage_pagination(interaction: discord.Interaction, card_name: str):
    card_usage_data, total_decks_per_archetype = count_card_usage_in_all_archetypes(card_name)
    if not card_usage_data:
        await interaction.response.send_message(f"No topping decks include `{formatter.smart_capitalize(card_name)}` in the current format.")
        return

    # Sort alphabetically
    sorted_data = sorted(card_usage_data.items(), key=lambda x: x[0])

    # Define the inital view
    view = TopCardsPaginationView(total_decks_per_archetype, card_name, data=sorted_data)

    await view.start(interaction)


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
