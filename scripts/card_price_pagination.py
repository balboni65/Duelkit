import discord
import json
import math
from scripts import formatter


class CardPricePaginationView(discord.ui.View):
    def __init__(self, printing_data=None, message=None):
        super().__init__(timeout=None)
        if printing_data is None or message is None:
            return

        # Save the printing data
        self.printing_data = printing_data
        self.current_page = 1
        self.data = []
        self.discount_labels = ["100%", "90%", "80%", "70%", "60%"]

        # Save the message
        self.message = message

        # Flatten the list of dicts into a list of (name, data) tuples
        for entry in printing_data:
            for name, data in entry.items():
                self.data.append((name, data))
        
        # Set the max number of pages based on the number of commands above
        
        self.max_pages = math.ceil(len(self.data))

    # Starts the pagination system and sends the initial message
    async def start(self):
        # Set page on startup
        self.current_page = 1

        # Disabled the page number button
        self.page_number_button.disabled = True

        # Create the initial message
        await self.update_message()

    # Updates the button states, and sends the message
    async def update_message(self):
        # Updates button states
        self.update_buttons()

        # Creates a new embed
        embed = self.create_embed()

        # Edit previous message, and send the new embed
        await self.message.edit(embed=embed, view=self)

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
            color=0xbbaa5e  
        )
        #bbaa5e

        # Add the model code and rarity fields
        embed.add_field(name="Code", value=info.get("printing_code", "N/A"), inline=True)
        embed.add_field(name="Rarity", value=info.get("printing_rarity", "N/A"), inline=True)
        embed.set_footer(text=f"As of: {formatter.get_current_date()}")

        # embed.add_field(name="Price Breakdown by Discount", value="```" + )

        # Add the listings section
        for edition_type in ["first_edition", "unlimited", "limited"]:
            listings = info.get(edition_type)
            if listings:
                # Add a gap in the embed for readability
                embed.add_field(name="\u200b", value="\u200b", inline=False)

                # Adds the lowest listings
                value = "\n".join(
                    f"`{listing['card_price']}` - `{listing['condition']}`"
                    for listing in listings
                )
                embed.add_field(
                    name=f"{edition_type.replace('_', ' ').title()} Listings",
                    value=value,
                    inline=True
                )

                # Adds a table of discount prices
                discount_title = f"{edition_type.replace('_', ' ').title()} Price Breakdown"
                discount_array = get_price_breakdown_by_discount(listings)
                discount_table = create_discount_table(discount_array)
                embed.add_field(name=discount_title, value=discount_table, inline=True)

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

    # Previous page button
    @discord.ui.button(label="<", style=discord.ButtonStyle.primary, custom_id="prev_page_button")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update current page, then update message
        self.current_page -= 1
        await self.update_message()

        # Prevent buttons from auto-clicking a second time
        await interaction.response.defer()

    # Current page button (No funcitonality)
    @discord.ui.button(label="/", style=discord.ButtonStyle.gray, custom_id="page_number_button")
    async def page_number_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    # Next page button
    @discord.ui.button(label=">", style=discord.ButtonStyle.primary, custom_id="next_page_button")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update current page, then update message
        self.current_page += 1
        await self.update_message()

        # Prevent buttons from auto-clicking a second time
        await interaction.response.defer()


# Creates a pagination view of card prices
async def show_card_listings(message: discord.Message, guild_id_as_int: int, formatted_card_name: str):
    # Try and get the printing data
    try:
        with open(f"guilds/{guild_id_as_int}/json/card_prices/{formatted_card_name}.json", "r", encoding="utf-8") as f:
            printing_data = json.load(f)

        # If there isn't any data found
        if not printing_data:
            await message.edit(content="Error: No listings in saved data.")
            return

        # Generate the view
        view = CardPricePaginationView(printing_data, message)
        await view.start()

    # If the file itself isn't found
    except FileNotFoundError:
        await message.edit(content="No listing data found.")

# Creates an array of discount prices
def get_price_breakdown_by_discount(listings):
    list_of_prices = []
    for listing in listings:
        # Convert the price to a float and round it to 2 decimal places
        list_of_prices.append(round(float(listing["card_price"].strip('$')), 2))
    average_price = sum(list_of_prices) / len(list_of_prices)
    price_breakdown = [average_price, average_price * 0.9, average_price * 0.8, average_price * 0.7, average_price * 0.6]
    for price in price_breakdown:
        price_breakdown[price_breakdown.index(price)] = f"${price:.2f}"

    return price_breakdown

# Creates a table for the discount prices
def create_discount_table(discount_array):
    discount_labels = ["100%", "90% ", "80% ", "70% ", "60% "]

    # Calculate max width per column
    max_price_length = max(len(price) for price in discount_array)

    # Build the header and value rows with padding
    table = ""
    for i in range(len(discount_array)):
        label = discount_labels[i]
        price = discount_array[i]
        table += f"| {label} : {price}{(max_price_length - len(price)) * ' '} |\n"

    return f"```{table}```"