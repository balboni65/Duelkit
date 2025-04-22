import discord
import json
import math


class PaginationView(discord.ui.View):
    current_page: int = 1
    entries_per_page: int = 1  # One entry per page

    def __init__(self, printing_data):
        super().__init__(timeout=None)
        # Save the printing data in context
        self.printing_data = printing_data
        self.current_page = 1
        self.data = []

        # Flatten the list of dicts into a list of (name, data) tuples
        for entry in printing_data:
            for name, data in entry.items():
                self.data.append((name, data))

    # Updates the message and buttons
    async def send(self, message):
        self.message = await message.edit(view=self)

        if self.message:
            self.update_buttons()
            await self.update_message()

    # Updates the message
    async def update_message(self):
        self.update_buttons()
        await self.message.edit(embed=self.create_embed(), view=self)

    # Creates the embed
    def create_embed(self):
        # If it can't find data
        if not self.data:
            return discord.Embed(title="No data", description="No listings found.", color=discord.Color.red())

        # Get the printing info
        name, info = self.data[self.current_page - 1]

        # Create the embed
        embed = discord.Embed(
            title=name,
            url=info.get("printing_url", ""),
            color=discord.Color.dark_gold()
        )

        # Add the model code and rarity fields
        embed.add_field(name="Code", value=info.get("printing_code", "N/A"), inline=True)
        embed.add_field(name="Rarity", value=info.get("printing_rarity", "N/A"), inline=True)

        # Add the listings section
        for edition_type in ["first_edition", "unlimited", "limited"]:
            listings = info.get(edition_type)
            if listings:
                value = "\n".join(
                    f"`{l['card_price']}` - `{l['condition']}` : {l['vendor']}-(*{l['rating']}%*)"
                    for l in listings
                )
                embed.add_field(
                    name=f"{edition_type.replace('_', ' ').title()} Listings",
                    value=value,
                    inline=False
                )

        return embed

    # Update the button logic
    def update_buttons(self):
        max_pages = math.ceil(len(self.data) / self.entries_per_page)

        self.page_number_button.disabled = True
        self.page_number_button.label = f"{self.current_page}/{max_pages}"

        self.prev_button.disabled = self.current_page == 1
        self.next_button.disabled = self.current_page == max_pages

        self.prev_button.style = discord.ButtonStyle.gray if self.prev_button.disabled else discord.ButtonStyle.primary
        self.next_button.style = discord.ButtonStyle.gray if self.next_button.disabled else discord.ButtonStyle.primary

    # Get the current page
    def get_current_page(self):
        max_pages = math.ceil(len(self.data) / self.entries_per_page)
        self.current_page = max(1, min(self.current_page, max_pages))
        return self.data[self.current_page - 1]

    @discord.ui.button(label="<", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        if self.current_page > 1:
            self.current_page -= 1
            await self.update_message()

    @discord.ui.button(label="/", style=discord.ButtonStyle.gray)
    async def page_number_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        await self.update_message()

    @discord.ui.button(label=">", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        max_pages = math.ceil(len(self.data) / self.entries_per_page)
        if self.current_page < max_pages:
            self.current_page += 1
            await self.update_message()


# Creates a pagination view of card prices
async def show_card_listings(message: discord.Message, guild_id_as_int: int):
    try:
        # Get printing data
        with open(f"guilds/{guild_id_as_int}/json/card_price.json", "r", encoding="utf-8") as f:
            printing_data = json.load(f)

        # If there isn't any data found
        if not printing_data:
            await message.edit(content="No listings in saved data.")
            return

        # Generate the view
        view = PaginationView(printing_data)
        await view.send(message)

    # If the file itself isn't found
    except FileNotFoundError:
        await message.edit(content="No listing data found.")
