import discord
import math

class PaginationView(discord.ui.View):
    current_page: int = 1
    entries_per_page: int = 1  # One entry per page

    def __init__(self):
        super().__init__(timeout=None)
        self.message = None
        self.current_page = 1
        self.help_channels_created = False

        # List of all commands and their descriptions
        self.commands_info = [
            {"command": "/card_price", "description": "View a card's pricing from TCG Player"},
            {"command": "/feedback", "description": "Send the creator of Duelkit a message!"},
            {"command": "/masterpack", "description": "Posts the links to view and open Master Packs"},
            {"command": "/metaltronus_decklist", "description": "Lists all the Metaltronus targets your deck has against another deck"},
            {"command": "/metaltronus_single", "description": "Lists all the Metaltronus targets in the game for a specific card"},
            {"command": "/report", "description": "Report a game's result"},
            {"command": "/roundrobin", "description": "Creates a 3-8 player Round Robin tournament, enter names with spaces in between"},
            {"command": "/secretpack_archetype", "description": "Search for a specific Secret Pack by its contained archetypes"},
            {"command": "/secretpack_title", "description": "Search for a specific Secret Pack by its title"},
            {"command": "/seventh_tachyon", "description": "Creates a list of all the current Seventh Tachyon targets in the game"},
            {"command": "/seventh_tachyon_decklist", "description": "Lists all the Metaltronus targets your deck has against another deck"},
            {"command": "/spin", "description": "Spin 5 random Secret Packs!"},
            {"command": "/standings", "description": "See current season standings"},
            {"command": "/top_archetype_breakdown", "description": "View a card-by-card breakdown of a top archetype for the current format"},
            {"command": "/top_archetypes", "description": "View the top archetypes for the current format and their deck variants"},
            {"command": "/top_cards", "description": "View a card's usage across all topping archetypes"},
            {"command": "/tournamentinfo", "description": "Find out what record is needed to receive an Invite or make Top Cut"},
            {"command": "/update", "description": "Updates all the databases found within the bot (takes a while to run)"}
        ]

    # Starts the pagination system and sends the initial message
    async def start(self, interaction: discord.Interaction):
        embed, file = self.create_embed()
        if file:
            self.message = await interaction.followup.send(embed=embed, view=self, file=file)
        else:
            self.message = await interaction.followup.send(embed=embed, view=self)

    # Updates the message and buttons
    async def send(self):
        self.update_buttons()
        await self.update_message()

    # Updates the message
    async def update_message(self):
        self.update_buttons()
        embed, file = self.create_embed()

        # Delete old message
        if self.message:
            await self.message.delete()
            if file:
                self.message = await self.message.channel.send(embed=embed, view=self, file=file)
            else:
                self.message = await self.message.channel.send(embed=embed, view=self)

    # Creates the embed
    def create_embed(self):
        # If on the first page, show a special welcome/help message
        if self.current_page == 1:
            embed = discord.Embed(
                title="Welcome to Duelkit! :wave:",
                description="I am a program written to provide a variety of commands to help with analysis, alternate game modes, tournaments, deck building and more!\n\n	Please page through this view to get an overview of my available commands.\n\nYou may also view this documentation on my github's home page, found [here](https://github.com/balboni65/Duelkit)",
                color=discord.Color.dark_gold()
            )
            embed.set_footer(text="Note: Animations may take a moment to load.")
            return embed, None
        # Get the command name and description
        command_info = self.commands_info[self.current_page - 2]
        command = command_info["command"]
        description = command_info["description"]
        file_name = f"duelkit-{command.replace('/', '')}.gif"
        file_path = f"global/images/help_gifs/{file_name}"

        # Create the embed
        embed = discord.Embed(
            title=command,
            color=discord.Color.dark_gold()
        )

        # Add the description field
        embed.add_field(name="Description:", value=f"> {description}", inline=True)

        # Try to attach the GIF if it exists
        try:
            file = discord.File(file_path, filename=file_name)
            embed.set_image(url=f"attachment://{file_name}")
            return embed, file
        except FileNotFoundError:
            return embed, None

    # Update the button logic
    def update_buttons(self):
        max_pages = 1 + math.ceil(len(self.commands_info) / self.entries_per_page)

        self.page_number_button.disabled = True
        self.page_number_button.label = f"{self.current_page}/{max_pages}"

        self.prev_button.disabled = self.current_page == 1
        self.next_button.disabled = self.current_page == max_pages

        self.prev_button.style = discord.ButtonStyle.gray if self.prev_button.disabled else discord.ButtonStyle.primary
        self.next_button.style = discord.ButtonStyle.gray if self.next_button.disabled else discord.ButtonStyle.primary

        # Add/remove special button depending on page number
        if self.current_page == 1 and not self.help_channels_created and not any(btn.label == "Click me to create a Duelkit help channel!" for btn in self.children):
            self.add_item(self.help_button)
        elif self.current_page != 1 and any(btn.label == "Click me to create a Duelkit help channel!" for btn in self.children):
            self.remove_item(self.help_button)

    # Get the current page
    # Version that causes it to load the next page smoothly, but the gif is in the middle idk
    def get_current_page(self):
        if self.current_page == 1:
            return None
        else: 
            max_pages = 1 + math.ceil(len(self.commands_info) / self.entries_per_page)
            self.current_page = max(1, min(self.current_page, max_pages))
            return self.commands_info[self.current_page - 1]["command"]

    # Version that causes it to delete the embed and resend
    # def get_current_page(self):
    #     if self.current_page == 1:
    #         return None
    #     index = self.current_page - 2
    #     return self.commands_info[index]["command"] if 0 <= index < len(self.commands_info) else None

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
        max_pages = math.ceil(len(self.commands_info) / self.entries_per_page)
        if self.current_page < max_pages:
            self.current_page += 1
            await self.update_message()

    # Special button that only shows up on page 1
    @discord.ui.button(label="Click me to create a Duelkit help channel!", style=discord.ButtonStyle.success)
    async def help_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.help_channels_created = True
        self.remove_item(self.help_button)

        # Get the guild (server) where the interaction occurred
        guild = interaction.guild

        category = discord.utils.get(guild.categories, name="testing-category")

        # Check if the bot has permission to create channels
        if guild and interaction.user.guild_permissions.manage_channels:

            # Create the private channel with the permissions set
            # channel = await guild.create_text_channel('duelkit-help', category=category)

            await create_help_channels(interaction, category, guild)

            # Send a confirmation message to the user who clicked the button
            await interaction.response.send_message("A new Duelkit Help Category has been created!", ephemeral=True)
        else:
            # Inform the user if the bot doesn't have permission to create channels
            await interaction.response.send_message("I don't have permission to create channels in this server.", ephemeral=True)

            await self.update_message()


# Creates a pagination view of card prices
async def show_help_pagination(interaction: discord.Interaction):
    view = PaginationView()
    view.update_buttons()
    await view.start(interaction)

async def create_help_channels(interaction: discord.Interaction, category, guild):
    overwrites={
            guild.default_role: discord.PermissionOverwrite(send_messages=False),  # Disable sending messages for @everyone
            guild.me: discord.PermissionOverwrite(send_messages=True)  # Allow bot to send messages
        }

    channel = await guild.create_text_channel('start-here', category=category)
    await channel.set_permissions(guild.default_role, send_messages=False)  # Disable sending messages for @everyone

    # ===== Intro block =====
    await channel.send(
        """**Welcome to Duelkit! :wave:**

**Duelkit** is a custom-built Discord bot created to assist the entire Yu-Gi-Oh! community. It offers features not found anywhere else such as:
- Accurate and up-to-date card prices
- In-depth meta analysis for archetypes and individual cards
- Information on what record you need to make top cut or secure your invite
- Server tournament and season standing functionality
- Support for alternate formats, including Master Duel
- and much much more!

I created **Duelkit** as a passion project and I'm always taking feedback and suggestions to improve the experience for everyone. Please don't hesitate to reach out!

(*PS: You can reach out through the bot itself with the* `/feedback` *command!*)"""
    )

    # ===== Commands block =====
    await channel.send(
    """
    ========================================
            
    **List of Commands:**

    \* This will be populated in a moment...
    """
    )

    channel_card_price = await guild.create_text_channel('card-price', category=category, overwrites=overwrites)
    message_card_price = await channel_card_price.send("# /card_price", file=discord.File("global/images/help_gifs/duelkit-card_price.gif"))
    await channel_card_price.send("""
## Function:
Returns the 5 lowest priced listings for every printing of a Yu-Gi-Oh! card
- Returns multiple lists if there are multiple editions of that printing (*1st Edition, Unlimited, Limited*)
- Filters out OCG listings (*Korean, Japanese, Chinese, OCG, etc.*)
- Uses only verified sellers
- Filters out closely named cards (*Dark Hole -> ❌Dark Hole Dragon*)
- Checks for rarities in the card name. (*✅Dark Hole (UR)*)

## Usage: `/card_price <card_name>`
- `card_name` (**Required**): Any Yu-Gi-Oh! card name. (*Partial names work as well*)

## Examples:
- `/card_price <Dark Hole>`
- `/card_price <ash blossom>`
- `/card_price <infinite imperm>`

## Run time:
- `20s` to `4min` depending on number of printings

## Notes:
- This feature depends on <https://www.tcgplayer.com> being online                       
""")





































    # ===== Commands block =====
#     await channel.send(
#         """
# ========================================
        
# **List of Commands:**

# ```/card_price```\t- View a card's pricing from TCG Player\n
# ```/feedback```\t- Send the creator of Duelkit a message!\n
# ```/help```\t- Learn more about the list of available commands, with previews!\n
# ```/masterpack```\t- Posts the links to view and open Master Packs\n
# ```/metaltronus_decklist```\t- Lists all the Metaltronus targets your deck has against another deck\n
# ```/metaltronus_single```\t- Lists all the Metaltronus targets in the game for a specific card\n
# ```/report```\t- Report a game's result\n
# ```/roundrobin```\t- Creates a 3-8 player Round Robin tournament, enter names with spaces in between\n
# ```/secretpack_archetype```\t- Search for a specific Secret Pack by its contained archetypes\n
# """)
#     await channel.send(
# """
# ```/secretpack_title```\t- Search for a specific Secret Pack by its title\n
# ```/seventh_tachyon```\t- Creates a list of all the current Seventh Tachyon targets in the game\n
# ```/seventh_tachyon_decklist```\t- Lists all the Seventh Tachyon targets in your decklist\n
# ```/small_world```\t- Find all the valid Small World bridges between 2 cards\n
# ```/small_world_decklist```\t- Find all the valid Small World bridges within a decklist\n
# ```/spin```\t- Spin 5 random Secret Packs!\n
# ```/standings```\t- See current season standings\n
# ```/top_archetype_breakdown```\t- View a card-by-card breakdown of a top archetype for the current format\n
# ```/top_archetypes```\t- View the top archetypes for the current format and their deck variants\n
# ```/top_cards```\t- View a card's usage across all topping archetypes\n
# ```/tournamentinfo```\t- Find out what record is needed to receive an Invite or make Top Cut\n
# ```/update```\t- Updates all the databases found within the bot (takes a while to run)\n
#     """)