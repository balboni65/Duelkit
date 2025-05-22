import os
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from matplotlib import animation
from datetime import datetime
import discord

async def graph_season_standings(interaction: discord.Interaction):
    guild_id = interaction.guild.id

    # Creates the file path if it doesn't exist
    os.makedirs(f"guilds/{guild_id}/images", exist_ok=True)
    os.makedirs(f"guilds/{guild_id}/json/tournaments", exist_ok=True)   
   

    # Files take too long to generate, so it needs to wait longer than 3 seconds before proceeding
    await interaction.response.defer(thinking=True)
    
    # If the channel does not belong to a category
    if interaction.channel.category is None:
        await interaction.followup.send("You must run this command from within a category")
    else:
        # Get the category name as it would be used in a filename
        category_name = interaction.channel.category.name.replace(" ", "_")

        # Check if a tournament file exists for this category
        tournament_exists = False

        # For each file
        for filename in os.listdir(f"guilds/{guild_id}/json/tournaments"):
            # If the category name is in the file name
            if category_name in filename:
                # Tournament exists
                tournament_exists = True
                break
        
        # If a tournament exists, generate the corresponding graphs
        if tournament_exists:
            # Generate embeds
            embed_line = graph_season_standings_line(category_name, guild_id)
            embed_bar = graph_season_standings_bar(category_name, guild_id)

            # Retrieve the generated files
            file_line = discord.File(f"guilds/{guild_id}/images/{category_name}_standings_line.gif", f"{category_name}_standings_line.gif")
            file_bar = discord.File(f"guilds/{guild_id}/images/{category_name}_standings_bar.gif", f"{category_name}_standings_bar.gif")

            await interaction.followup.send(embeds=[embed_line, embed_bar], files=[file_line, file_bar])
        else:
            await interaction.followup.send("There are currently no tournaments for this category")

# Creates an animated graph of the season standings within the channel category
def graph_season_standings_line(category_name, guild_id):
    weekly_wins = {}
    num_weeks = 0
    all_tournaments = []

    # Get each tournament file
    for filename in os.listdir(f"guilds/{guild_id}/json/tournaments"):
        if category_name in filename:
            with open(f"guilds/{guild_id}/json/tournaments/{filename}", "r") as f:
                data = json.load(f)

                # Get the Date of the Tournament
                date_str = data.get("date")
                if date_str:
                    try:
                        date = datetime.fromisoformat(date_str)
                        all_tournaments.append((date, data))
                    except ValueError:
                        print(f"Invalid date format in {filename}")
                        
                        all_tournaments.append((datetime.max, data))
                else:
                    print(f"No date in {filename}.")
                    all_tournaments.append((datetime.max, data))

    # Sort by Date
    all_tournaments.sort(key=lambda x: x[0])

    # Populate Graph
    for date, tournament in all_tournaments:
        # Count wins for each player
        weekly_results = Counter()
        for round_data in tournament["pairings"]:
            for matches in round_data.values():
                for match in matches:
                    weekly_results[match["result"]] += 1

        # Ensure all players are included, even if they have 0 wins in this tournament
        all_players = set(weekly_results.keys())
        for round_data in tournament["pairings"]:
            for matches in round_data.values():
                for match in matches:
                    for key, value in match.items():
                        if "match" in key:
                            player1, player2 = value.split(" vs ")
                            all_players.update([player1, player2])

        # Update weekly wins for each player
        for player in all_players:
            weekly_wins.setdefault(player, []).append(weekly_results.get(player, 0))

        # Increment the number of weeks played
        num_weeks += 1

    # Ensure all players have a complete history of weeks
    for player in weekly_wins:
        while len(weekly_wins[player]) < num_weeks:
            weekly_wins[player].append(0)

    # Calculate cumulative points
    cumulative_points = {player: np.concatenate(([0], np.cumsum(wins))) for player, wins in weekly_wins.items()}

    # Sort players by final cumulative points (most to least)
    sorted_players = sorted(cumulative_points, key=lambda player: cumulative_points[player][-1], reverse=True)

    # Create an array for weeks
    weeks_array = np.arange(0, num_weeks + 1)

    # Animation settings
    linger_frames = 15
    total_frames = num_weeks + 1 + linger_frames  # Including lingering frames after the final week

    # Create figure
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, num_weeks)
    ax.set_ylim(0, max(max(points) for points in cumulative_points.values()) + 2)
    ax.set_xlabel("Weeks", color="white")
    ax.set_ylabel("Total Wins", color="white")
    ax.tick_params(axis="x", colors="white")
    ax.tick_params(axis="y", colors="white")
    if num_weeks == 1:
        ax.set_title(f"Cumulative Wins Over {num_weeks} Week", color="white")
    else:
        ax.set_title(f"Cumulative Wins Over {num_weeks} Weeks", color="white")
    ax.grid(True, color="#2C2F33", zorder=0)

    # Set background color
    fig.patch.set_facecolor("#2C2F33")
    ax.set_facecolor("#99AAB5")

    # Create lines for each player
    lines = {player: ax.plot([], [], marker="s", label=player, linewidth=2)[0] for player in cumulative_points}

    # Reorder lines based on sorted players
    sorted_lines = [lines[player] for player in sorted_players]

    # Create legend with sorted players
    ax.legend(sorted_lines, sorted_players, loc="upper left", facecolor="#2C2F33", labelcolor="white")

    # Initialize the animation (start with all lines at 0)
    def init():
        for line in lines.values():
            line.set_data([0], [0])  # Start at 0 for each player at week 0
        return list(lines.values())

    # Update the animation for each frame
    def update(frame):
        frame = min(frame, num_weeks)  # Ensure that the last frame is the final week
        for player, line in lines.items():
            line.set_data(weeks_array[:frame + 1], cumulative_points[player][:frame + 1])
        return list(lines.values())

    # Create the animation
    ani = animation.FuncAnimation(fig, update, frames=np.arange(0, total_frames), init_func=init, blit=True)

    # Save the animation as a GIF
    gif_path = f"guilds/{guild_id}/images/{category_name}_standings_line.gif"
    ani.save(gif_path, writer="pillow", fps=2)

    # Send the GIF to Discord
    embed = discord.Embed(title="Tournament Standings", description=f"Cumulative wins over the last {num_weeks} weeks.", color=0xbbaa5e)
    embed.set_image(url=f"attachment://{category_name}_standings_line.gif")
    return embed

# Creates an animated bar chart of the season standings
def graph_season_standings_bar(category_name, guild_id):
    weekly_wins = {}
    num_weeks = 0
    all_tournaments = []

    # Get each tournament file
    for filename in os.listdir(f"guilds/{guild_id}/json/tournaments"):
        if category_name in filename:
            with open(f"guilds/{guild_id}/json/tournaments/{filename}", "r") as f:
                data = json.load(f)

                # Get the Date of the Tournament
                date_str = data.get("date")
                if date_str:
                    try:
                        date = datetime.fromisoformat(date_str)
                        all_tournaments.append((date, data))
                    except ValueError:
                        print(f"Invalid date format in {filename}")
                        
                        all_tournaments.append((datetime.max, data))
                else:
                    print(f"No date in {filename}.")
                    all_tournaments.append((datetime.max, data))

    # Sort by Date
    all_tournaments.sort(key=lambda x: x[0])

    # Populate Graph
    for date, tournament in all_tournaments:
        # Count wins for each player
        weekly_results = Counter()
        for round_data in tournament["pairings"]:
            for matches in round_data.values():
                for match in matches:
                    weekly_results[match["result"]] += 1

        # Ensure all players are included, even if they have 0 wins in this tournament
        all_players = set(weekly_results.keys())
        for round_data in tournament["pairings"]:
            for matches in round_data.values():
                for match in matches:
                    for key, value in match.items():
                        if "match" in key:
                            player1, player2 = value.split(" vs ")
                            all_players.update([player1, player2])

        # Update weekly wins for each player
        for player in all_players:
            weekly_wins.setdefault(player, []).append(weekly_results.get(player, 0))

        # Increment the number of weeks played
        num_weeks += 1

    # Ensure every player has a full history of weeks (fill missing weeks with 0)
    for player in weekly_wins:
        while len(weekly_wins[player]) < num_weeks:
            weekly_wins[player].append(0)

    # Calculate cumulative points and ensure every player starts at 0
    cumulative_points = {
        player: np.concatenate(([0], np.cumsum(wins)))  # Prepend a 0 to start at week 0
        for player, wins in weekly_wins.items()
    }

    # Sort players by final cumulative points (most to least)
    sorted_players = sorted(cumulative_points, key=lambda player: cumulative_points[player][-1], reverse=True)

    # Animation settings
    linger_frames = 15
    total_frames = num_weeks + 1 + linger_frames  # +1 for the starting frame (Week 0)

    # Create figure
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlim(-0.5, len(sorted_players) - 0.5)
    ax.set_ylim(0, max(max(points) for points in cumulative_points.values()) + 2)
    ax.set_ylabel("Total Wins", color="white")
    ax.set_xticks(range(len(sorted_players)))
    ax.set_xticklabels(sorted_players, rotation=45, ha="right", color="white")
    ax.tick_params(axis="y", colors="white")
    ax.set_title(f"Cumulative Wins Over {num_weeks} Weeks", color="white")
    ax.grid(color="#2C2F33", zorder=0)
    
    # Create initial bars, all starting at 0
    bar_container = ax.bar(sorted_players, [0] * len(sorted_players), color="#7289D7", zorder=3)

    # Set background color
    fig.patch.set_facecolor("#2C2F33")
    ax.set_facecolor("#99AAB5")


    # Initialization function (ensures all bars start at 0)
    def init():
        for bar in bar_container:
            bar.set_height(0)
        return bar_container

    # Update function for animation
    def update(frame):
        if frame < total_frames - linger_frames:  # Ensure it doesn't go beyond available data
            for i, player in enumerate(sorted_players):
                bar_container[i].set_height(cumulative_points[player][frame])
        return bar_container

    # Create animation
    ani = animation.FuncAnimation(fig, update, frames=total_frames, init_func=init, blit=False)

    # Save animation
    gif_path = f"guilds/{guild_id}/images/{category_name}_standings_bar.gif"
    ani.save(gif_path, writer="pillow", fps=2)

    # Send graph to Discord
    embed = discord.Embed(title="Tournament Standings", description=f"Cumulative wins over the last {num_weeks} weeks.", color=0xbbaa5e)
    embed.set_image(url=f"attachment://{category_name}_standings_bar.gif")
    return embed