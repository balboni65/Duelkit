import discord
from dotenv import load_dotenv
import os

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
                f"📩 **New Feedback from {interaction.user}:**\n{message_text}"
            )
            await interaction.response.send_message("✅ Feedback sent to the developer!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ Couldn't find the developer user.", ephemeral=True)

    except discord.Forbidden:
        await interaction.response.send_message("❌ I can't DM the developer (probably DMs are disabled).", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error sending DM: `{e}`", ephemeral=True)
