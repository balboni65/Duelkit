import discord
import math

class HelpPaginationView(discord.ui.View):
    def __init__(self):
        # Prevent timeout
        super().__init__(timeout=None)

        # No initial message on startup
        self.message = None

        # List of all commands and their descriptions
        self.commands_info = [
            {"command": "/card_price", "description": "View a card's pricing from TCG Player", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#card_price"},
            {"command": "/feedback", "description": "Send the creator of Duelkit a message!", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#feedback"},
            {"command": "/masterpack", "description": "Posts the links to view and open Master Packs", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#masterpack"},
            {"command": "/metaltronus_decklist", "description": "Lists all the Metaltronus targets your deck has against another deck", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#metaltronus_decklist"},
            {"command": "/metaltronus_single", "description": "Lists all the Metaltronus targets in the game for a specific card", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#metaltronus_single"},
            {"command": "/report", "description": "Report a game's result", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#report"},
            {"command": "/roundrobin", "description": "Creates a 3-8 player Round Robin tournament, enter names with spaces in between", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#roundrobin"},
            {"command": "/secretpack_archetype", "description": "Search for a specific Secret Pack by its contained archetypes", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#secretpack_archetype"},
            {"command": "/secretpack_title", "description": "Search for a specific Secret Pack by its title", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#secretpack_title"},
            {"command": "/seventh_tachyon", "description": "Creates a list of all the current Seventh Tachyon targets in the game", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#seventh_tachyon"},
            {"command": "/seventh_tachyon_decklist", "description": "Lists all the Metaltronus targets your deck has against another deck", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#seventh_tachyon_decklist"},
            {"command": "/small_world", "description": "Find all the valid Small World bridges between 2 cards", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#small_world"},
            {"command": "/small_world_decklist", "description": "Find all the valid Small World bridges within a decklist", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#small_world_decklist"},
            {"command": "/spin", "description": "Spin 5 random Secret Packs!", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#spin"},
            {"command": "/standings", "description": "See current season standings", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#standings"},
            {"command": "/top_archetype_breakdown", "description": "View a card-by-card breakdown of a top archetype for the current format", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#top_archetype_breakdown"},
            {"command": "/top_archetypes", "description": "View the top archetypes for the current format and their deck variants", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#top_archetypes"},
            {"command": "/top_cards", "description": "View a card's usage across all topping archetypes", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#top_cards"},
            {"command": "/tournamentinfo", "description": "Find out what record is needed to receive an Invite or make Top Cut", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#tournamentinfo"},
            {"command": "/update", "description": "Updates all the databases found within the bot (takes a while to run)", "url": "https://github.com/balboni65/Duelkit/tree/main?tab=readme-ov-file#update"}
        ]

        # Set the max number of pages based on the number of commands above
        self.max_pages = 1 + math.ceil(len(self.commands_info))

    # Starts the pagination system and sends the initial message
    async def start(self, interaction: discord.Interaction):
        # Set page on startup
        self.current_page = 1

        # Disabled the page number button
        self.page_number_button.disabled = True

        # Set initial button states
        self.update_buttons()

        # Creates the welcome message embed
        embed, file = self.create_embed()

        # Sends the embed
        self.message = await interaction.followup.send(embed=embed, view=self)

    # Updates the button states, and sends the message
    async def update_message(self):
        # Updates button states
        self.update_buttons()

        # Creates a new embed
        embed, file = self.create_embed()

        # Delete previous message, and send the new embed
        if self.message:
            await self.message.delete()
            if file:
                self.message = await self.message.channel.send(embed=embed, view=self, file=file)
            else:
                self.message = await self.message.channel.send(embed=embed, view=self)

    # Creates the embed
    def create_embed(self):
        # If on the first page, show welcome message
        if self.current_page == 1:
            embed = discord.Embed(
                title="Welcome to Duelkit! :wave:",
                description="I am a program written to provide a variety of commands to help with analysis, alternate game modes, tournaments, deck building and more!\n\n	Please page through this view to get an overview of my available commands.\n\nYou can learn more information about every command by visiting my GitHub page found: [here](https://github.com/balboni65/Duelkit), or by clicking the title of each page.",
                color=0xbbaa5e  
            )
            embed.set_footer(text="Note: Animations may take a moment to load.")
            return embed, None
        
        # Otherwise, show the command information
        else:
            # Get the command name, description, url, file name, and file path
            command_info = self.commands_info[self.current_page - 2]
            command_name = command_info["command"]
            description = command_info["description"]
            command_url = command_info["url"]
            file_name = f"duelkit-{command_name.replace('/', '')}.gif"
            file_path = f"global/images/help_gifs/{file_name}"

            # Create the embed
            embed = discord.Embed(
                title=command_name,
                url=command_url,
                color=0xbbaa5e  
            )

            # Add the description field
            embed.add_field(name="Description:", value=f"> {description}", inline=True)

            # Try to attach the GIF
            try:
                file = discord.File(file_path, filename=file_name)
                embed.set_image(url=f"attachment://{file_name}")
                return embed, file
            except FileNotFoundError:
                return embed, None

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
    @discord.ui.button(label="/", style=discord.ButtonStyle.gray, custom_id="current_page_button")
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

# Creates a pagination view of command previews
async def show_help_pagination(interaction: discord.Interaction):
    view = HelpPaginationView()
    await view.start(interaction)