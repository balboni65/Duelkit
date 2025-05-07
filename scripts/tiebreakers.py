import discord
import math
from itertools import combinations

class TiebreakerPaginationView(discord.ui.View):
    def __init__(self, tiebreaker_id: str = None):
        # Prevent timeout
        super().__init__(timeout=None)

        # Set the tie breaker ID
        self.tiebreaker_id = tiebreaker_id

        # No initial message on startup
        self.message = None

    # Starts the pagination system and sends the initial message
    async def start(self, interaction: discord.Interaction):
        # Set page on startup
        self.current_page = 1
        # Set initial button states
        self.update_buttons()

        if self.current_page == 1:
            embed = create_result_embed(self.tiebreaker_id)
        else:
            embed = create_example_embed(self.tiebreaker_id)

        # Sends the first embed
        self.message = await interaction.followup.send(embed=embed, view=self)

    # Updates the button states, and sends the message
    async def update_message(self):
        # Updates button states
        self.update_buttons()

        if self.current_page == 1:
            embed = create_result_embed(self.tiebreaker_id)
        else:
            embed = create_example_embed(self.tiebreaker_id)
       
        await self.message.edit(embed=embed, view=self)

    # Update the button states
    def update_buttons(self):
        # Disable the "tiebreaker" button if its the first page
        self.tiebreaker_button.disabled = self.current_page == 1
        self.tiebreaker_button.style = (discord.ButtonStyle.gray if self.tiebreaker_button.disabled else discord.ButtonStyle.primary)
        # Disable the "example" button if its the second page
        self.example_button.disabled = self.current_page == 2
        self.example_button.style = (discord.ButtonStyle.gray if self.example_button.disabled else discord.ButtonStyle.green)

    # Previous page button
    @discord.ui.button(label="Your Tiebreakers", style=discord.ButtonStyle.primary, custom_id="tiebreaker_button")
    async def tiebreaker_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update current page, then update message
        self.current_page = 1
        await self.update_message()

        # Prevent buttons from auto-clicking a second time
        await interaction.response.defer()

    # Current page button (No funcitonality)
    @discord.ui.button(label="See More Examples", style=discord.ButtonStyle.gray, custom_id="example_button")
    async def example_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Update current page, then update message
        self.current_page = 2
        await self.update_message()

        # Prevent buttons from auto-clicking a second time
        await interaction.response.defer()
        pass

async def explain_my_tiebreakers(interaction: discord.Interaction, tiebreaker_id: str):
    view = TiebreakerPaginationView(tiebreaker_id)
    await view.start(interaction)
    # "12 345 678 900"
    # "└┬┘└┬┘└┬┘└┬┘"
    # ""
    return

def create_result_embed(tiebreaker_id: str):
    aa, bbb, ccc, ddd = get_tiebreaker_sections(tiebreaker_id)
    if len(aa) == 1:
        description_message = f"Your tiebreaker code is ```{tiebreaker_id}```\nThis is then broken into 4 parts: ``` A  |  B  |  C  |  D \n {aa} | {bbb} | {ccc} | {ddd}```\nEach section represents a different aspect of your performance, and\n**higher values** are better.\n\nPlacement is determined by comparing **Section A** first.\nIf there's still a tie, it proceeds in order to **Sections B**, **C**, and finally **D**."
    else:
        description_message = f"Your tiebreaker code is ```{tiebreaker_id}```\nThis is then broken into 4 parts: ``` A |  B  |  C  |  D \n {aa} | {bbb} | {ccc} | {ddd}```\nEach section represents a different aspect of your performance, and\n**higher values** are better.\n\nPlacement is determined by comparing **Section A** first.\nIf there's still a tie, it proceeds in order to **Sections B**, **C**, and finally **D**."

    embed = discord.Embed( 
                title="Here's a breakdown of your tiebreakers:",
                description=description_message,
                color=0xbbaa5e,
            )

    # Spacer (forces line break)
    embed.add_field(name="\u200b", value="\u200b", inline=False)
    
    # Section AA
    aa_message = f"This value represents the \n**total points** you earned\nthroughout the tournament.\n```Win:  3 Points\nTie:  1 Point\nLoss: 0 Points```\nYou earned **{aa} Points** through a combination of wins and draws."
    embed.add_field(name=f"Section A", value=aa_message)

    # Section BB
    bbb_message = f"This value represents\nthe **average win rate** of all the opponents you faced during the tournament.\n\nIn most cases, this value is sufficient to separate final standings.\n\nYour opponents won an average of **{get_bbb_percentage(tiebreaker_id)}** of their matches."
    embed.add_field(name=f"Section B", value=bbb_message)

    # Spacer (forces line break)
    embed.add_field(name="\u200b", value="\u200b", inline=False)

    # Section CC
    ccc_message = f"This value represents\nthe **average win rate** of all your \n**opponents' opponents** in the tournament.\n\nThis tiebreaker accounts for significantly more players than the previous section.\n\nYour **opponents' opponents** won an average of **{get_ccc_percentage(tiebreaker_id)}** of their matches."
    embed.add_field(name=f"Section C", value=ccc_message)

    # Section DD
    ddd_message = f"This value represents the\n**sum of the squares of the specific rounds in which you lost.**\n\n*(Note: Only losses are considered—draws do not affect this score.*)"
    # tuple_list_of_squares = predict_sum_of_squares(ddd)
    tuple_of_squares = predict_first_sum_of_squares(ddd)

    first_line = ""
    second_line = ""
    if tuple_of_squares and tuple_of_squares != 0:
        # If the sum of the squares is 1 integer
        if len(tuple_of_squares) == 1:
            first_line = f"\n\nAn example that results in your value of **{ddd}** would be a loss in **round {tuple_of_squares[0]}**:"
            second_line += f"{tuple_of_squares[0]}² = {ddd.lstrip('0')}"
        
        # If the sum of the squares is the sum of multiple integers
        else:
            first_line = f"\n\nAn example that results in your value of **{ddd}** would be losses in **round "
            # For every value in the tuple
            for value in tuple_of_squares:
                # Build a string showing the rounds lost
                first_line += f"{value}** and ** "
                # Build a string showing the values squared and added together
                second_line += f"{value}² + "
            # Remove the trailing +
            second_line = second_line.rstrip('+ ')
            # Add the equals sign
            second_line += f"= {ddd.lstrip('0')}"
            # Remove the trailing ` and **round `
            first_line = first_line.rstrip(' and ** ')
            # Close the bold wrapper
            first_line += "**:"
        ddd_message += f"{first_line}\n```{second_line}```"
    elif tuple_of_squares == 0:
        ddd_message += f"\n\nYour tiebreaker value is ✨**{ddd}**✨\nThis means you never lost a round!"
    else:
        ddd_message += f"\n\nYour tiebreaker value of **{ddd}** is not possible to achieve in a tournament, you may have copied the code incorrectly"
    
    embed.add_field(name=f"Section D", value=ddd_message)


    return embed

def create_example_embed(tiebreaker_id: str):
    embed = discord.Embed(
                title="Here's more examples to understand tiebreakers better:",
                color=0xbbaa5e  
            )
    return embed

# Breaks the tiebreaker into its individual values
def get_tiebreaker_sections(tiebreaker_id: str):
    # These variables are abreviated as codes, as they would otherwise be very long and cumbersome

    # Set the digit length of the earned points, (9, 21...)
    aa_len = 2 if len(tiebreaker_id) == 11 else 1

    # aa is your earned points
    aa = tiebreaker_id[:aa_len]

    # bbb is your opponent's winrate
    bbb = tiebreaker_id[aa_len:aa_len+3]

    # ccc is your opponent's opponent's winrate
    ccc = tiebreaker_id[aa_len+3:aa_len+6]

    # ddd is the sum of the squares of the rounds you lost in
    ddd = tiebreaker_id[aa_len+6:aa_len+9]

    return aa, bbb, ccc, ddd
        
# Gets the first valid example of a sum of squares
def predict_first_sum_of_squares(ddd: str):
    sum_of_squares = int(ddd)
    if sum_of_squares == 0:
        return 0

    # Try all possible numbers of rounds lost (1 to 12)
    for num_losses in range(1, 13):
        # Try every combination of loss rounds from 1 to 12
        for combination in combinations(range(1, 13), num_losses):
            # Square the round numbers and sum them
            if sum(r**2 for r in combination) == sum_of_squares:
                return combination
    return None

def get_bbb_percentage(tiebreaker_id: str):
    # These variables are abreviated as codes, as they would otherwise be very long and cumbersome

    # Set the digit length of the earned points, (9, 21...)
    aa_len = 2 if len(tiebreaker_id) == 11 else 1

    # bbb is your opponent's winrate
    bbb = f"{tiebreaker_id[aa_len:aa_len+2]}.{tiebreaker_id[aa_len+2:aa_len+3]}%"

    return bbb

def get_ccc_percentage(tiebreaker_id: str):
    # These variables are abreviated as codes, as they would otherwise be very long and cumbersome

    # Set the digit length of the earned points, (9, 21...)
    aa_len = 2 if len(tiebreaker_id) == 11 else 1

    # ccc is your opponent's opponent's winrate
    ccc = f"{tiebreaker_id[aa_len+3:aa_len+5]}.{tiebreaker_id[aa_len+5:aa_len+6]}%"

    return ccc