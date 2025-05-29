import streamlit as st
import random
import string
import time
import json
import os
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="WhoSpies?",
    page_icon="🕵️",
    layout="wide"
)

# File to store game data (shared across all sessions)
GAMES_FILE = "games_data.json"

def load_games():
    """Load games from file"""
    try:
        if os.path.exists(GAMES_FILE):
            with open(GAMES_FILE, 'r') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_games(games):
    """Save games to file"""
    try:
        with open(GAMES_FILE, 'w') as f:
            json.dump(games, f, default=str, indent=2)
    except Exception as e:
        st.error(f"Error saving games: {e}")

def get_games():
    """Get current games (always fresh from file)"""
    return load_games()

def update_game(game_id, game_data):
    """Update a specific game"""
    games = load_games()
    games[game_id] = game_data
    save_games(games)

# Initialize session state
def init_session_state():
    if 'current_game_id' not in st.session_state:
        st.session_state.current_game_id = None
    if 'player_name' not in st.session_state:
        st.session_state.player_name = None
    if 'is_host' not in st.session_state:
        st.session_state.is_host = False

def generate_game_id():
    """Generate a 6-character game ID"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def create_new_game():
    """Create a new game room"""
    game_id = generate_game_id()
    games = load_games()
    
    # Make sure game_id is unique
    while game_id in games:
        game_id = generate_game_id()
    
    games[game_id] = {
        'players': {},
        'ready_players': [],
        'host': None,
        'game_started': False,
        'game_ended': False,
        'spy': None,
        'location': None,
        'created_at': str(datetime.now()),
        'start_time': None,
        'votes': {},
        'voting_phase': False,
        'winner': None,
        'elimination_target': None
    }
    save_games(games)
    return game_id

def join_game(game_id, player_name, is_host=False):
    """Join a game room"""
    games = load_games()
    if game_id in games:
        games[game_id]['players'][player_name] = {
            'joined_at': str(datetime.now()),
            'is_ready': False
        }
        if is_host:
            games[game_id]['host'] = player_name
        save_games(games)
        return True
    return False

def toggle_ready(game_id, player_name):
    """Toggle player ready status"""
    games = load_games()
    if game_id in games and player_name in games[game_id]['players']:
        current_status = games[game_id]['players'][player_name]['is_ready']
        games[game_id]['players'][player_name]['is_ready'] = not current_status
        
        # Update ready_players list
        ready_players = games[game_id]['ready_players']
        if not current_status:
            if player_name not in ready_players:
                ready_players.append(player_name)
        else:
            if player_name in ready_players:
                ready_players.remove(player_name)
        
        games[game_id]['ready_players'] = ready_players
        save_games(games)
        return True
    return False

def leave_game(game_id, player_name):
    """Remove player from game"""
    games = load_games()
    if game_id in games and player_name in games[game_id]['players']:
        del games[game_id]['players'][player_name]
        if player_name in games[game_id]['ready_players']:
            games[game_id]['ready_players'].remove(player_name)
        
        # Remove from votes
        if player_name in games[game_id]['votes']:
            del games[game_id]['votes'][player_name]
        
        # If no players left, delete the game
        if not games[game_id]['players']:
            del games[game_id]
        else:
            # If host left, assign new host
            if games[game_id]['host'] == player_name:
                remaining_players = list(games[game_id]['players'].keys())
                if remaining_players:
                    games[game_id]['host'] = remaining_players[0]
        
        save_games(games)

def start_game(game_id):
    """Start the game - assign spy and location"""
    games = load_games()
    if game_id not in games:
        return False
    
    game = games[game_id]
    players = list(game['players'].keys())
    
    if len(players) < 3:
        return False
    
    # Assign spy randomly
    spy = random.choice(players)
    game['spy'] = spy
    
    # Sample locations (you can expand this)
    locations = [
        "Restaurant", "School", "Hospital", "Bank", "Airport",
        "Beach", "Casino", "Circus", "Embassy", "Hotel",
        "Military Base", "Movie Studio", "Museum", "Ocean Liner",
        "Passenger Train", "Pirate Ship", "Polar Station", "Police Station",
        "Space Station", "Submarine", "Supermarket", "Theater", "University"
    ]
    
    game['location'] = random.choice(locations)
    game['game_started'] = True
    game['start_time'] = str(datetime.now())
    game['votes'] = {}
    game['voting_phase'] = False
    game['winner'] = None
    game['game_ended'] = False
    
    save_games(games)
    return True

def vote_player(game_id, voter, target):
    """Vote to eliminate a player"""
    games = load_games()
    if game_id in games:
        games[game_id]['votes'][voter] = target
        save_games(games)
        return True
    return False

def start_voting(game_id):
    """Start the voting phase"""
    games = load_games()
    if game_id in games:
        games[game_id]['voting_phase'] = True
        games[game_id]['votes'] = {}
        save_games(games)

def end_game(game_id, winner, elimination_target=None):
    """End the game with a winner"""
    games = load_games()
    if game_id in games:
        games[game_id]['game_ended'] = True
        games[game_id]['winner'] = winner
        if elimination_target:
            games[game_id]['elimination_target'] = elimination_target
        save_games(games)

def calculate_time_remaining(start_time_str):
    """Calculate remaining time from start"""
    try:
        start_time = datetime.fromisoformat(start_time_str)
        elapsed = datetime.now() - start_time
        total_seconds = 600  # 10 minutes
        remaining_seconds = total_seconds - elapsed.total_seconds()
        return max(0, remaining_seconds)
    except:
        return 600

def format_time(seconds):
    """Format seconds into MM:SS"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

# Initialize
init_session_state()

# Add CSS for animations and styling
st.markdown("""
<style>
.timer-normal {
    font-size: 2rem;
    font-weight: bold;
    color: #0066cc;
    text-align: center;
    padding: 10px;
    border: 2px solid #0066cc;
    border-radius: 10px;
    margin: 10px 0;
}

.timer-danger {
    font-size: 2rem;
    font-weight: bold;
    color: #ff0000;
    text-align: center;
    padding: 10px;
    border: 2px solid #ff0000;
    border-radius: 10px;
    margin: 10px 0;
    animation: pulse 1s infinite;
}

@keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.5; }
    100% { opacity: 1; }
}

.winner-announcement {
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
    padding: 20px;
    border-radius: 15px;
    margin: 20px 0;
    animation: celebrate 2s ease-in-out;
}

.spy-wins {
    background: linear-gradient(45deg, #ff6b6b, #ff8e8e);
    color: white;
}

.non-spy-wins {
    background: linear-gradient(45deg, #4ecdc4, #44a08d);
    color: white;
}

@keyframes celebrate {
    0% { transform: scale(0.5); opacity: 0; }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); opacity: 1; }
}

.vote-section {
    background-color: #f0f2f6;
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# Main UI
st.title("🕵️ WhoSpies?")
st.markdown("*A Spyfall-inspired social deduction game*")

# Sidebar for game controls
with st.sidebar:
    st.header("Game Controls")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("Auto-refresh (Live Updates)", value=True)
    if auto_refresh:
        refresh_rate = st.slider("Refresh rate (seconds)", 1, 5, 2)

# Main game logic
if st.session_state.current_game_id is None:
    # Landing page - Create or Join game
    st.header("Welcome to WhoSpies!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎮 Create New Game")
        player_name_create = st.text_input("Your Name:", key="create_name")
        
        if st.button("Create Game", type="primary"):
            if player_name_create.strip():
                game_id = create_new_game()
                join_game(game_id, player_name_create.strip(), is_host=True)
                st.session_state.current_game_id = game_id
                st.session_state.player_name = player_name_create.strip()
                st.session_state.is_host = True
                st.success(f"Game created! Game ID: {game_id}")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Please enter your name!")
    
    with col2:
        st.subheader("🚪 Join Existing Game")
        game_id_join = st.text_input("Game ID:", key="join_id").upper()
        player_name_join = st.text_input("Your Name:", key="join_name")
        
        if st.button("Join Game"):
            if not game_id_join.strip():
                st.error("Please enter a Game ID!")
            elif not player_name_join.strip():
                st.error("Please enter your name!")
            else:
                games = get_games()
                if game_id_join not in games:
                    st.error("Game not found!")
                elif player_name_join.strip() in games[game_id_join]['players']:
                    st.error("Name already taken in this game!")
                elif games[game_id_join]['game_started'] and not games[game_id_join]['game_ended']:
                    st.error("Game already started!")
                else:
                    join_game(game_id_join, player_name_join.strip())
                    st.session_state.current_game_id = game_id_join
                    st.session_state.player_name = player_name_join.strip()
                    st.success(f"Joined game {game_id_join}!")
                    time.sleep(1)
                    st.rerun()

else:
    # In-game interface
    game_id = st.session_state.current_game_id
    player_name = st.session_state.player_name
    games = get_games()
    game = games.get(game_id)
    
    if not game:
        st.error("Game not found!")
        st.session_state.current_game_id = None
        st.rerun()
    
    # Update host status
    st.session_state.is_host = (game['host'] == player_name)
    
    # Game header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.header(f"Game Room: {game_id}")
    with col2:
        if st.button("Leave Game", type="secondary"):
            leave_game(game_id, player_name)
            st.session_state.current_game_id = None
            st.session_state.player_name = None
            st.session_state.is_host = False
            st.rerun()
    with col3:
        st.write(f"**You:** {player_name}")
    
    # Game status
    if not game['game_started']:
        # Waiting room
        st.subheader("Waiting Room")
        
        # Ready button
        current_ready = player_name in game['ready_players']
        ready_button_text = "✅ Ready!" if current_ready else "⏳ Not Ready"
        ready_button_type = "secondary" if current_ready else "primary"
        
        if st.button(ready_button_text, type=ready_button_type):
            toggle_ready(game_id, player_name)
            st.rerun()
        
        # Players list with live updates
        st.subheader("Players in Game")
        
        if game['players']:
            for p_name, p_info in game['players'].items():
                ready_status = "✅ Ready" if p_name in game['ready_players'] else "⏳ Not Ready"
                host_badge = " 👑" if p_name == game['host'] else ""
                you_badge = " (You)" if p_name == player_name else ""
                
                st.write(f"**{p_name}**{host_badge}{you_badge}: {ready_status}")
        else:
            st.write("No players in game")
        
        # Start game button (host only)
        if st.session_state.is_host:
            total_players = len(game['players'])
            ready_count = len(game['ready_players'])
            
            st.markdown("---")
            st.write(f"Players ready: {ready_count}/{total_players}")
            
            if total_players >= 3 and ready_count == total_players:
                if st.button("🚀 Start Game!", type="primary"):
                    if start_game(game_id):
                        st.success("Game started!")
                        time.sleep(1)
                        st.rerun()
            else:
                if total_players < 3:
                    st.info("Need at least 3 players to start")
                else:
                    st.info("Waiting for all players to be ready")
    
    elif game['game_ended']:
        # Game ended - show results
        st.markdown(f"""
        <div class="winner-announcement {'spy-wins' if game['winner'] == 'spy' else 'non-spy-wins'}">
            🎉 {game['winner'].upper()} WINS! 🎉
        </div>
        """, unsafe_allow_html=True)
        
        # Reveal the spy
        st.markdown("### 🕵️ The Spy Was:")
        st.markdown(f"## **{game['spy']}**")
        
        st.markdown(f"### 📍 The Location Was:")
        st.markdown(f"## **{game['location']}**")
        
        # Show elimination results if applicable
        if 'elimination_target' in game and game['elimination_target']:
            st.markdown(f"### 🗳️ Eliminated Player:")
            st.markdown(f"**{game['elimination_target']}**")
        
        # Show all players and their roles
        st.markdown("### 👥 All Players:")
        for p_name in game['players']:
            role = "🕵️ SPY" if p_name == game['spy'] else "👥 NON-SPY"
            st.write(f"**{p_name}**: {role}")
        
        # New game button (host only)
        if st.session_state.is_host:
            st.markdown("---")
            if st.button("🔄 Start New Game", type="primary"):
                # Reset game state
                games = get_games()
                games[game_id]['game_started'] = False
                games[game_id]['game_ended'] = False
                games[game_id]['spy'] = None
                games[game_id]['location'] = None
                games[game_id]['start_time'] = None
                games[game_id]['votes'] = {}
                games[game_id]['voting_phase'] = False
                games[game_id]['winner'] = None
                games[game_id]['elimination_target'] = None
                games[game_id]['ready_players'] = []
                
                # Reset all players to not ready
                for p_name in games[game_id]['players']:
                    games[game_id]['players'][p_name]['is_ready'] = False
                
                save_games(games)
                st.rerun()
    
    else:
        # Game in progress
        st.subheader("🎯 Game in Progress!")
        
        # Timer
        if game['start_time']:
            time_remaining = calculate_time_remaining(game['start_time'])
            time_display = format_time(time_remaining)
            
            # Check if time is up
            if time_remaining <= 0:
                if not game['game_ended']:
                    end_game(game_id, "spy")  # Spy wins if time runs out
                    st.rerun()
            
            # Display timer with different styles
            timer_class = "timer-danger" if time_remaining <= 10 else "timer-normal"
            st.markdown(f"""
            <div class="{timer_class}">
                ⏰ {time_display}
            </div>
            """, unsafe_allow_html=True)
            
            # Audio countdown for last 10 seconds
            if time_remaining <= 10 and time_remaining > 0:
                st.markdown(f"""
                <audio autoplay>
                    <source src="data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+HyvmEePDmH1ezQgC0HlK7w5n9WzGGh7+SXSA+hk7Tlv2IcPzuM1+jPeiwFJXfH8N2QQAoTXrTp66hVFApHn+HyvmQaPz6M1+jPeSsFJXfH8N2QQgkUXrTp6qhWEgpHn+LyvmEcPzqL1+nQeSMGJn" type="audio/wav">
                </audio>
                """, unsafe_allow_html=True)
        
        # Show role (without revealing spy to others)
        if player_name == game['spy']:
            st.error("🕵️ You are the SPY! Try to figure out the location without being caught!")
            st.write("Ask questions to figure out where you are, but don't be too obvious!")
        else:
            st.success(f"📍 Location: **{game['location']}**")
            st.write("You know the location! Ask questions to find the spy, but don't make it too obvious what the location is!")
        
        # Voting section
        if not game['voting_phase']:
            # Start voting button (any player can start voting)
            if st.button("🗳️ Start Voting Phase", type="primary"):
                start_voting(game_id)
                st.rerun()
        else:
            # Voting interface
            st.markdown("""
            <div class="vote-section">
                <h3>🗳️ Voting Phase - Who is the spy?</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Show current votes
            vote_counts = {}
            for voter, target in game['votes'].items():
                vote_counts[target] = vote_counts.get(target, 0) + 1
            
            st.write("**Current Votes:**")
            for target, count in vote_counts.items():
                st.write(f"• **{target}**: {count} vote(s)")
            
            # Voting form
            if player_name not in game['votes']:
                other_players = [p for p in game['players'].keys() if p != player_name]
                selected_target = st.selectbox("Vote to eliminate:", other_players)
                
                if st.button(f"Vote for {selected_target}", type="primary"):
                    vote_player(game_id, player_name, selected_target)
                    st.success(f"You voted for {selected_target}")
                    st.rerun()
            else:
                st.info(f"You voted for: **{game['votes'][player_name]}**")
            
            # Check if all players have voted
            total_players = len(game['players'])
            votes_cast = len(game['votes'])
            st.write(f"Votes cast: {votes_cast}/{total_players}")
            
            if votes_cast == total_players:
                # Determine elimination
                max_votes = max(vote_counts.values())
                most_voted = [player for player, votes in vote_counts.items() if votes == max_votes]
                
                if len(most_voted) == 1:
                    eliminated_player = most_voted[0]
                    
                    # Determine winner
                    if eliminated_player == game['spy']:
                        winner = "non-spies"
                    else:
                        winner = "spy"
                    
                    end_game(game_id, winner, eliminated_player)
                    st.rerun()
                else:
                    st.warning("Tie vote! No one is eliminated. Continue playing!")
                    # Reset voting
                    games = get_games()
                    games[game_id]['voting_phase'] = False
                    games[game_id]['votes'] = {}
                    save_games(games)
                    st.rerun()
        
        # Game instructions
        with st.expander("How to Play"):
            st.markdown("""
            ### For Non-Spies:
            - You know the location
            - Ask questions to identify the spy
            - Don't make the location too obvious
            - Vote to eliminate the spy
            
            ### For the Spy:
            - You don't know the location
            - Ask questions to figure out where you are
            - Try to blend in and not get caught
            - Survive until time runs out to win
            
            ### General Rules:
            - Game lasts 10 minutes
            - Take turns asking each other questions
            - Questions should be related to the location
            - Any player can start a voting phase
            - All players must vote to eliminate someone
            - Spy wins if they survive or if a non-spy is eliminated
            - Non-spies win if they eliminate the spy
            """)
        
        # Players in game
        st.subheader("Players")
        for p_name in game['players']:
            role_hint = " 🕵️" if p_name == game['spy'] and player_name == game['spy'] else ""
            you_badge = " (You)" if p_name == player_name else ""
            st.write(f"• **{p_name}**{you_badge}{role_hint}")

# Auto-refresh functionality
if auto_refresh and st.session_state.current_game_id:
    time.sleep(refresh_rate)
    st.rerun()

# Footer
st.markdown("---")
st.markdown("**Made with ❤️ using Streamlit. Good luck finding the spy in WhoSpies?!**")