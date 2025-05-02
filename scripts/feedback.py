import discord
from dotenv import load_dotenv
import os
import time
import asyncio

feedback_command_cooldown_rate = 1800  # In seconds (30 minutes)
list_of_users_on_feedback_cooldown = {}

# Directly pms ... me!
async def send_feedback(interaction: discord.Interaction, message_text: str):
    # Load the environment variables
    load_dotenv()
    CREATOR_ID  = os.getenv("CREATOR_ID")

    # Try to send the message
    try:
        # Get my account
        owner = await interaction.client.fetch_user(CREATOR_ID)

        if owner:
            await owner.send(
                f"📩 New Feedback from **{interaction.user}** (Discriminator tag: *{interaction.user.discriminator}*) (ID: *{interaction.user.id}*),\nFrom the **{interaction.guild.name}** Guild. (*{interaction.guild.id}*)\nMessage:\n\t{message_text}"
            )
            await interaction.response.send_message("✅ Feedback sent to the developer!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Couldn't find the developer user.", ephemeral=True)

    except discord.Forbidden:
        await interaction.response.send_message("❌ I can't DM the developer (probably DMs are disabled).", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error sending DM: `{e}`", ephemeral=True)

async def is_on_feedback_cooldown(interaction: discord.Interaction):
    current_time = time.time()
    user_id = interaction.user.id

    # If the user is already in the cooldowns list
    if user_id in list_of_users_on_feedback_cooldown and current_time - list_of_users_on_feedback_cooldown[user_id] < feedback_command_cooldown_rate:
        # Get how much time they have left
        current_cooldown = round(feedback_command_cooldown_rate - (current_time - list_of_users_on_feedback_cooldown[user_id]), 2)
        cooldown_end_timestamp = int(current_time + current_cooldown)
        cooldown_message = f"You're on cooldown! Thank you for your previous feedback and please try again <t:{cooldown_end_timestamp}:R>."

        # Respond with how long they have until the cooldown is over, then delete the messages once the cooldown is over
        await interaction.response.send_message(cooldown_message, ephemeral=True)
        await asyncio.sleep(current_cooldown)
        await interaction.delete_original_response()

        # Return a boolean so calling this function returns a usable variable
        return True
    
    # Adds the user to the cooldown array
    list_of_users_on_feedback_cooldown[user_id] = current_time

    return False