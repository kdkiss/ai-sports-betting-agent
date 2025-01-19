from telegram import Update
from telegram.ext import ContextTypes
from ..services.sportsdb_api import SportsDBAPI
from ..services.parlay_analyzer import ParlayAnalyzer
from ..services.parlay_preprocessor import ParlayPreprocessor
from ..services.image_preprocessor import ImagePreprocessor

sports_api = SportsDBAPI()
parlay_analyzer = ParlayAnalyzer(sports_api)
text_preprocessor = ParlayPreprocessor()
image_preprocessor = ImagePreprocessor()

async def team_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /team command."""
    if not context.args:
        await update.message.reply_text("Please provide a team name. Usage: /team Arsenal")
        return

    team_name = " ".join(context.args)
    teams = await sports_api.search_team(team_name)

    if not teams:
        await update.message.reply_text(f"No teams found matching '{team_name}'")
        return

    team = teams[0]  # Get the first matching team
    team_info = (
        f"🏟️ *{team['strTeam']}*\n"
        f"League: {team['strLeague']}\n"
        f"Country: {team['strCountry']}\n"
        f"Stadium: {team['strStadium']}\n"
        f"Founded: {team['intFormedYear']}\n\n"
        f"Description: {team['strDescriptionEN'][:500]}..."
    )

    await update.message.reply_text(team_info, parse_mode='Markdown')

async def player_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /player command."""
    if not context.args:
        await update.message.reply_text("Please provide a player name. Usage: /player Messi")
        return

    player_name = " ".join(context.args)
    players = await sports_api.search_players(player_name=player_name)

    if not players:
        await update.message.reply_text(f"No players found matching '{player_name}'")
        return

    player = players[0]  # Get the first matching player
    player_info = (
        f"👤 *{player['strPlayer']}*\n"
        f"Team: {player['strTeam']}\n"
        f"Position: {player['strPosition']}\n"
        f"Nationality: {player['strNationality']}\n"
        f"Birth: {player['dateBorn']}\n"
        f"Height: {player['strHeight']}\n"
        f"Weight: {player['strWeight']}\n\n"
        f"Description: {player['strDescriptionEN'][:500] if player['strDescriptionEN'] else 'No description available'}..."
    )

    await update.message.reply_text(player_info, parse_mode='Markdown')

async def match_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /match command."""
    if len(context.args) < 3:
        await update.message.reply_text(
            "Please provide two team names. Usage: /match Arsenal vs Chelsea"
        )
        return

    try:
        # Find the 'vs' or 'VS' in the arguments
        vs_index = [i for i, arg in enumerate(context.args) if arg.lower() == 'vs'][0]
        team1_name = " ".join(context.args[:vs_index])
        team2_name = " ".join(context.args[vs_index + 1:])

        # Get team IDs
        team1_data = await sports_api.search_team(team1_name)
        team2_data = await sports_api.search_team(team2_name)

        if not team1_data or not team2_data:
            await update.message.reply_text("One or both teams not found.")
            return

        team1 = team1_data[0]
        team2 = team2_data[0]

        # Get next events for both teams
        team1_events = await sports_api.get_team_next_events(team1['idTeam'])
        team2_events = await sports_api.get_team_next_events(team2['idTeam'])

        # Find matching events between teams
        matching_events = [
            event for event in team1_events
            if team2['strTeam'] in event['strEvent']
        ]

        if matching_events:
            event = matching_events[0]
            match_info = (
                f"⚽ *Upcoming Match*\n"
                f"{event['strEvent']}\n"
                f"📅 Date: {event['dateEvent']}\n"
                f"🏟️ Venue: {event['strVenue']}\n"
                f"🏆 League: {event['strLeague']}\n"
            )
        else:
            # If no upcoming matches, show team comparison
            match_info = (
                f"🆚 *Team Comparison*\n\n"
                f"*{team1['strTeam']}*\n"
                f"League: {team1['strLeague']}\n"
                f"Stadium: {team1['strStadium']}\n\n"
                f"*{team2['strTeam']}*\n"
                f"League: {team2['strLeague']}\n"
                f"Stadium: {team2['strStadium']}\n\n"
                f"No upcoming matches found between these teams."
            )

        await update.message.reply_text(match_info, parse_mode='Markdown')

    except (IndexError, KeyError):
        await update.message.reply_text(
            "Error processing the command. Please use the format: /match Arsenal vs Chelsea"
        ) 

async def analyze_parlay_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /analyze command for parlay analysis."""
    if not context.args and not update.message.reply_to_message and not update.message.photo:
        await update.message.reply_text(
            "Please provide your bet slip in one of these ways:\n"
            "1. Reply to a message containing the bet slip\n"
            "2. Send a screenshot of your bet slip\n"
            "3. Type the bets after the /analyze command\n\n"
            "I can handle:\n"
            "• Screenshots from most betting apps\n"
            "• Copy/pasted bet slips\n"
            "• Multiple parlays at once\n"
            "• Various odds formats (+150, 2.50, 3/2)\n\n"
            "Just send me your bets and I'll analyze them!"
        )
        return

    try:
        # Initial response to show we're working
        processing_msg = await update.message.reply_text(
            "🔄 Processing your bet slip...\n"
            "This might take a moment as I analyze the bets."
        )
        
        try:
            # Handle image input
            if update.message.photo:
                # Get the largest photo (best quality)
                photo = update.message.photo[-1]
                # Download the photo
                photo_file = await context.bot.get_file(photo.file_id)
                photo_bytes = await photo_file.download_as_bytearray()
                # Process the image
                formatted_text = image_preprocessor.process_image(photo_bytes)
            else:
                # Handle text input
                parlay_text = " ".join(context.args) if context.args else update.message.reply_to_message.text
                formatted_text = text_preprocessor.preprocess(parlay_text)
            
            if not formatted_text:
                await processing_msg.edit_text(
                    "❌ I couldn't identify any valid bets.\n"
                    "Please make sure your bet slip includes:\n"
                    "• The bet type (total, player prop, etc.)\n"
                    "• The line or value (if applicable)\n"
                    "• The odds for each bet\n\n"
                    "You can send either a screenshot or text!"
                )
                return
            
            # Try to parse and analyze the formatted parlay
            parlay = await parlay_analyzer.parse_parlay_text(formatted_text)
            analysis = await parlay_analyzer.analyze_parlay(parlay)
            
            # Format the response
            response = (
                f"📊 *Parlay Analysis*\n\n"
                f"Overall Rating: {analysis['overall_rating']}/10\n"
                f"Risk Level: {analysis['risk_level']}\n"
                f"Expected Value: {analysis['expected_value']}%\n\n"
                f"*Individual Legs:*\n"
            )

            for leg in analysis['legs_analysis']:
                response += (
                    f"\n{leg['team']} - Strength: {leg['strength']}/10\n"
                    f"Confidence: {leg['confidence'].upper()}\n"
                    f"Factors:\n"
                )
                for factor in leg['factors']:
                    response += f"• {factor}\n"

            response += "\n*Recommendations:*\n"
            for rec in analysis['recommendations']:
                response += f"• {rec}\n"

            # Delete processing message and send analysis
            await processing_msg.delete()
            await update.message.reply_text(response, parse_mode='Markdown')

        except ValueError as ve:
            # Handle specific parsing errors with helpful messages
            error_msg = str(ve)
            if "division by zero" in error_msg:
                error_msg = "I couldn't find valid odds in the parlay. Please make sure odds are included for each bet."
            elif "invalid literal for int" in error_msg:
                error_msg = "I had trouble reading some numbers in your bet slip. Please check the format."
            elif "Error processing image" in error_msg:
                error_msg = "I had trouble reading the screenshot. Please make sure it's clear and well-lit, or try sending the text instead."
            
            await processing_msg.edit_text(
                f"❌ I ran into an issue analyzing your parlay:\n{error_msg}\n\n"
                "You can try:\n"
                "• Sending a clearer screenshot\n"
                "• Copying and pasting the text\n"
                "• Sending each bet on a new line"
            )
            
        except Exception as e:
            # Handle unexpected errors
            await processing_msg.edit_text(
                "❌ Something unexpected happened while analyzing your parlay.\n"
                "This might be because:\n"
                "• The image quality is too low\n"
                "• The format is unclear or missing information\n"
                "• There are special characters I can't process\n\n"
                "Please try sending a clearer image or the text directly."
            )
            logger.error(f"Parlay analysis error: {str(e)}")

    except Exception as e:
        await update.message.reply_text(
            "❌ Sorry, I couldn't process that bet slip.\n"
            "Please make sure you're either:\n"
            "• Sending a clear screenshot\n"
            "• Replying to a message with the bet slip\n"
            "• Including the bet slip after the /analyze command\n\n"
            "Need help? Use /help to see example formats."
        )