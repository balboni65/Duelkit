import discord
import json
import math
from collections import Counter

class PaginationView(discord.ui.View):
    current_page: int = 1
    entries_per_page: int = 4

    def __init__(self):
        super().__init__(timeout=None)

    # Sends the pagination view
    async def send(self, interaction: discord.Interaction):
        # First sends a message, this cannot be edited
        # Then sends a followup, which can be edited
        await interaction.response.send_message("Here are the top Archetypes of the current format:")

        self.message = await interaction.followup.send(view=self)
        
        # Check if the message exists, then update the message
        if self.message:
            await self.update_message(self.get_current_page())

    # Updates the button states, as well as changes the view
    async def update_message(self, data):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(data), view=self)

    # Creates the embed of archetype information
    def create_embed(self, data):
        embed = discord.Embed(title="Top Archetypes", color=0xbbaa5e)

        # For every value in the Archetype tuple
        for name, percentage, deck_count, deck_names, deck_names_counter, win_count, deck_win_counter, average_cost in data:
            # Determine sentence structure for deck list(s)
            if deck_count == 1:
                count_text = f"\t**{deck_count}** Deck List"
            elif deck_count == 0: 
                count_text = f"\t**No** Deck Lists"
            else:
                count_text = f"\t**{deck_count}** Deck Lists"

            # Determine sentence structure for deck names
            if deck_names:
                sorted_decks = sorted(deck_names_counter.items(), key=lambda x: x[1], reverse=True)
                deck_names_text = "\n".join(
                    [f"{str(count).rjust(3)} {deck_name} (Wins: {deck_win_counter[deck_name]})" 
                    if deck_win_counter[deck_name] > 0 
                    else f"{str(count).rjust(3)} {deck_name}" 
                    for deck_name, count in sorted_decks]
                )
                deck_names_text = f"\n```{deck_names_text}```"
            else:
                deck_names_text = ""

            if win_count == 1:
                win_text = f" - **{win_count}** Total Win"
            elif win_count == 0:
                win_text = f""
            else:
                win_text = f" - **{win_count}** Total Wins"

            if average_cost != 0:
                cost_text = f" - Avg. Cost: **${average_cost:.2f}**"
            else:
                cost_text = ""

            # Add the field to the embed
            embed.add_field(name=f"> **{name}** (*{percentage}*)", value=f"{count_text}{win_text}{cost_text}{deck_names_text}", inline=False)

        return embed



    # Determines the state of the buttons
    def update_buttons(self):
        # Maximum number of pages
        max_pages = math.ceil(len(self.data) / self.entries_per_page)

        # Setting the page number button values
        self.page_number_button.disabled = True
        self.page_number_button.label = f"{self.current_page}/{max_pages}"

        # Setting button disable conditions
        self.first_page_button.disabled = self.current_page == 1
        self.prev_button.disabled = self.current_page == 1
        self.next_button.disabled = self.current_page == max_pages
        self.last_page_button.disabled = self.current_page == max_pages

        # Update button UI if they are disabled
        self.first_page_button.style = discord.ButtonStyle.gray if self.first_page_button.disabled else discord.ButtonStyle.green
        self.prev_button.style = discord.ButtonStyle.gray if self.prev_button.disabled else discord.ButtonStyle.primary
        self.next_button.style = discord.ButtonStyle.gray if self.next_button.disabled else discord.ButtonStyle.primary
        self.last_page_button.style = discord.ButtonStyle.gray if self.last_page_button.disabled else discord.ButtonStyle.green

    # Gets the current page data
    def get_current_page(self):
        # Maximum number of pages
        max_pages = math.ceil(len(self.data) / self.entries_per_page)

        # If the data changes, this ensures proper bounds
        self.current_page = max(1, min(self.current_page, max_pages))

        # Gets the index of information we want to present per page
        starting_index = (self.current_page - 1) * self.entries_per_page
        ending_index = starting_index + self.entries_per_page

        # Returns the index range
        return self.data[starting_index:ending_index]

    #Discord buttons, first defers a response per discords requirements, then updates the current page, then updates the message
    @discord.ui.button(label="|<", style=discord.ButtonStyle.primary)
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

    @discord.ui.button(label=">|", style=discord.ButtonStyle.primary)
    async def last_page_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = math.ceil(len(self.data) / self.entries_per_page)
        await self.update_message(self.get_current_page())

# Creates a pagination view of the top archetype information
async def get_top_archetypes(interaction: discord.Interaction):
    # Get the archetype tuple information
    archetype_info = get_archetype_data()

    # Define the initial view
    pagination_view = PaginationView()

    # Populate the view with data
    pagination_view.data = archetype_info

    # Send the interaction, to create the view
    await pagination_view.send(interaction)

# Returns a tuple of information about each archetype
def get_archetype_data():
    # Opens the file
    with open('global/json/topping_decklists.json', 'r', encoding="utf-8") as file:
        topping_archetypes = json.load(file)

    archetype_info = []
    
    for name, data in topping_archetypes.items():
        if data["decks"]:
            deck_names_counter = Counter(deck["deck_name"] for deck in data["decks"].values())
            deck_win_counter = Counter()
            total_cost = 0
            total_decks = len(data["decks"])

            for deck in data["decks"].values():
                # Extract and clean up the "total_price" field
                price_str = deck.get("total_price", "").replace("$", "").replace(",", "").strip()

                try:
                    total_cost += float(price_str)  # Convert cleaned string to float
                except ValueError:
                    print(f"Warning: Could not convert price '{deck.get('total_price')}' for {deck.get('deck_name', 'Unknown')}")

                # Count wins
                if deck.get("placement") == "Winner":
                    deck_win_counter[deck["deck_name"]] += 1

            # Calculate the average cost safely
            average_cost = round(total_cost / total_decks, 2) if total_decks > 0 else 0

            win_count = sum(deck_win_counter.values())
        else:
            deck_names_counter = Counter()
            deck_win_counter = Counter()
            win_count = 0
            average_cost = 0

        deck_names = set(deck_names_counter.keys())

        # Append data, now including the corrected average cost
        archetype_info.append((name, data["percentage"], len(data["decks"]), deck_names, deck_names_counter, win_count, deck_win_counter, average_cost))
    
    return archetype_info
