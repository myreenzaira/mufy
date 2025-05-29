import streamlit as st
import random
import string
import time
import json
import os
from datetime import datetime, timedelta

# Page config
st.set_page_config(
    page_title="🕵️ WhoSpies? - The Ultimate Spy Hunt!",
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
    if 'location_guesses' not in st.session_state:
        st.session_state.location_guesses = []

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
        'elimination_target': None,
        'location_guesses': {}
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
        
        # Remove from location guesses
        if player_name in games[game_id]['location_guesses']:
            del games[game_id]['location_guesses'][player_name]
        
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
    
    # Expanded locations list
    locations = [
        "Restaurant", "School", "Hospital", "Bank", "Airport",
        "Beach", "Casino", "Circus", "Embassy", "Hotel",
        "Military Base", "Movie Studio", "Museum", "Ocean Liner",
        "Passenger Train", "Pirate Ship", "Polar Station", "Police Station",
        "Space Station", "Submarine", "Supermarket", "Theater", "University",
        "Library", "Zoo", "Gym", "Spa", "Bakery", "Farm", "Prison",
        "Art Gallery", "Nightclub", "Workshop", "Cathedral", "Laboratory"
    ]
    
    game['location'] = random.choice(locations)
    game['game_started'] = True
    game['start_time'] = str(datetime.now())
    game['votes'] = {}
    game['voting_phase'] = False
    game['winner'] = None
    game['game_ended'] = False
    game['location_guesses'] = {}
    
    save_games(games)
    return True

def vote_player(game_id, voter, target):
    """Vote to eliminate a player (anonymously)"""
    games = load_games()
    if game_id in games:
        # Create anonymous vote ID
        vote_id = f"vote_{len(games[game_id]['votes']) + 1}"
        games[game_id]['votes'][vote_id] = {'voter': voter, 'target': target}
        save_games(games)
        return True
    return False

def guess_location(game_id, player_name, guessed_location):
    """Submit a location guess (spy only)"""
    games = load_games()
    if game_id in games:
        games[game_id]['location_guesses'][player_name] = guessed_location
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
        total_seconds = 300  # 5 minutes
        remaining_seconds = total_seconds - elapsed.total_seconds()
        return max(0, remaining_seconds)
    except:
        return 300

def format_time(seconds):
    """Format seconds into MM:SS"""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"

def get_funny_role_description(is_spy):
    """Get funny role descriptions"""
    if is_spy:
        descriptions = [
            "🕵️ You're the SPY! Time to channel your inner 007... or Mr. Bean!",
            "🕵️ CONGRATULATIONS! You're officially lost and confused!",
            "🕵️ You're the SPY! Your mission: Figure out where you are without looking like a tourist!",
            "🕵️ SPY ALERT! You're about as undercover as a giraffe in a zoo!",
            "🕵️ You're the SPY! Try not to ask 'Where am I?' directly... that's a dead giveaway!"
        ]
    else:
        descriptions = [
            "👥 You're NOT the spy! Time to play detective and catch that sneaky impostor!",
            "👥 Congrats! You actually know where you are (shocking, we know)!",
            "👥 You're a REGULAR PERSON! Your job: Spot the clueless spy among you!",
            "👥 NOT A SPY! Now go catch that suspicious person asking weird questions!",
            "👥 You're in the clear! Time to hunt down the person who clearly doesn't belong!"
        ]
    return random.choice(descriptions)

def get_funny_game_over_message(winner, spy_name, location, eliminated_player=None):
    """Get funny game over messages"""
    if winner == "spy":
        messages = [
            f"🎉 {spy_name} pulls off the ultimate bamboozle! The spy wins by being sneakier than a cat burglar!",
            f"🕵️ PLOT TWIST! {spy_name} was the spy all along and fooled everyone! Master of disguise or just lucky?",
            f"🎭 {spy_name} deserves an Oscar for that performance! The spy wins by pure deception!",
            f"🤡 Everyone got played by {spy_name}! The spy wins and probably can't stop laughing!",
            f"🎪 Ladies and gentlemen, {spy_name} just pulled off the heist of the century... of confusion!"
        ]
        if eliminated_player:
            messages.append(f"💀 Poor {eliminated_player} got voted out while {spy_name} was laughing in the shadows!")
    else:
        messages = [
            f"🔍 BUSTED! {spy_name} got caught red-handed! The detectives win this round!",
            f"👮 Justice is served! {spy_name}'s cover was blown harder than a birthday candle!",
            f"🎯 GOTCHA! {spy_name} was about as subtle as a bull in a china shop!",
            f"🕵️‍♀️ Case closed! {spy_name} should probably stick to their day job!",
            f"🏆 The good guys win! {spy_name} got exposed faster than a bad lie!"
        ]
    
    return random.choice(messages)

# Initialize
init_session_state()

# Add enhanced CSS for animations and styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Creepster&family=Righteous:wght@400&display=swap');

.main-title {
    font-family: 'Creepster', cursive;
    font-size: 4rem;
    text-align: center;
    background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #ffeaa7);
    background-size: 300% 300%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: gradient-shift 3s ease-in-out infinite;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    margin-bottom: 10px;
}

.subtitle {
    font-family: 'Righteous', cursive;
    font-size: 1.5rem;
    text-align: center;
    color: #666;
    font-style: italic;
    margin-bottom: 30px;
}

@keyframes gradient-shift {
    0% { background-position: 0% 50%; }
    50% { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

.timer-normal {
    font-size: 2.5rem;
    font-weight: bold;
    color: #0066cc;
    text-align: center;
    padding: 15px;
    border: 3px solid #0066cc;
    border-radius: 15px;
    margin: 15px 0;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    box-shadow: 0 4px 15px rgba(0,102,204,0.3);
}

.timer-danger {
    font-size: 2.5rem;
    font-weight: bold;
    color: #ff0000;
    text-align: center;
    padding: 15px;
    border: 3px solid #ff0000;
    border-radius: 15px;
    margin: 15px 0;
    background: linear-gradient(135deg, #ffefef 0%, #ffcccc 100%);
    animation: pulse-danger 1s infinite;
    box-shadow: 0 4px 15px rgba(255,0,0,0.4);
}

@keyframes pulse-danger {
    0% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.7; transform: scale(1.05); }
    100% { opacity: 1; transform: scale(1); }
}

.winner-announcement {
    font-size: 3rem;
    font-weight: bold;
    text-align: center;
    padding: 30px;
    border-radius: 20px;
    margin: 30px 0;
    animation: celebrate 2s ease-in-out;
    box-shadow: 0 8px 25px rgba(0,0,0,0.2);
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
    0% { transform: scale(0.5) rotate(-180deg); opacity: 0; }
    50% { transform: scale(1.1) rotate(0deg); }
    100% { transform: scale(1) rotate(0deg); opacity: 1; }
}

.vote-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 15px;
    margin: 15px 0;
    box-shadow: 0 6px 20px rgba(102,126,234,0.3);
}

.role-card {
    padding: 20px;
    border-radius: 15px;
    margin: 15px 0;
    text-align: center;
    font-size: 1.2rem;
    font-weight: bold;
    box-shadow: 0 6px 20px rgba(0,0,0,0.1);
    animation: role-reveal 1s ease-out;
}

.spy-card {
    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
    color: white;
    border: 3px solid #d63031;
}

.non-spy-card {
    background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
    color: white;
    border: 3px solid #00b894;
}

@keyframes role-reveal {
    0% { opacity: 0; transform: translateY(-20px); }
    100% { opacity: 1; transform: translateY(0); }
}

.location-guess-section {
    background: linear-gradient(135deg, #fda085 0%, #f093fb 100%);
    padding: 20px;
    border-radius: 15px;
    margin: 15px 0;
    color: white;
    box-shadow: 0 6px 20px rgba(253,160,133,0.3);
}

.game-over-message {
    font-size: 1.5rem;
    text-align: center;
    padding: 20px;
    margin: 20px 0;
    border-radius: 15px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    animation: message-bounce 1s ease-out;
}

@keyframes message-bounce {
    0% { transform: translateY(-30px); opacity: 0; }
    50% { transform: translateY(5px); }
    100% { transform: translateY(0); opacity: 1; }
}

.player-list {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    padding: 15px;
    border-radius: 10px;
    margin: 10px 0;
    color: white;
}

/* Button enhancements */
.stButton > button {
    border-radius: 10px !important;
    font-weight: bold !important;
    transition: all 0.3s ease !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px rgba(0,0,0,0.2) !important;
}
</style>
""", unsafe_allow_html=True)

# Add background sound effect
st.markdown("""
<audio autoplay loop>
    <source src="data:audio/wav;base64,UklGRnYBAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YVIBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" type="audio/wav">
</audio>
""", unsafe_allow_html=True)

# Enhanced main title
st.markdown("""
<div class="main-title">
    🕵️ WHOSPIES? 🕵️
</div>
<div class="subtitle">
    The Ultimate Social Deduction Game of Secrets, Lies, and Questionable Acting Skills!
</div>
""", unsafe_allow_html=True)

# Sidebar for game controls
with st.sidebar:
    st.header("🎮 Game Controls")
    
    # Auto-refresh toggle
    auto_refresh = st.checkbox("🔄 Auto-refresh (Live Updates)", value=True)
    if auto_refresh:
        refresh_rate = st.slider("⚡ Refresh rate (seconds)", 1, 5, 2)
    
    # Sound toggle
    sound_enabled = st.checkbox("🔊 Sound Effects", value=True)

# Main game logic
if st.session_state.current_game_id is None:
    # Landing page - Create or Join game
    st.header("🎭 Welcome to the World of Espionage!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎮 Create New Game")
        st.write("*Become the master of ceremonies!*")
        player_name_create = st.text_input("Your Secret Agent Name:", key="create_name", placeholder="Agent 007, Master Spy, etc.")
        
        if st.button("🚀 Create Game", type="primary"):
            if player_name_create.strip():
                game_id = create_new_game()
                join_game(game_id, player_name_create.strip(), is_host=True)
                st.session_state.current_game_id = game_id
                st.session_state.player_name = player_name_create.strip()
                st.session_state.is_host = True
                st.success(f"🎉 Game created! Game ID: **{game_id}**")
                time.sleep(1)
                st.rerun()
            else:
                st.error("🚨 Please enter your secret agent name!")
    
    with col2:
        st.subheader("🚪 Join Existing Game")
        st.write("*Infiltrate an ongoing operation!*")
        game_id_join = st.text_input("🔐 Game ID:", key="join_id", placeholder="Enter 6-character code").upper()
        player_name_join = st.text_input("Your Secret Agent Name:", key="join_name", placeholder="Agent Smith, Double-O-Fun, etc.")
        
        if st.button("🎯 Join Mission"):
            if not game_id_join.strip():
                st.error("🚨 Please enter a Game ID!")
            elif not player_name_join.strip():
                st.error("🚨 Please enter your agent name!")
            else:
                games = get_games()
                if game_id_join not in games:
                    st.error("❌ Game not found! Double-check that code!")
                elif player_name_join.strip() in games[game_id_join]['players']:
                    st.error("👥 Agent name already taken in this mission!")
                elif games[game_id_join]['game_started'] and not games[game_id_join]['game_ended']:
                    st.error("🚫 Mission already in progress!")
                else:
                    join_game(game_id_join, player_name_join.strip())
                    st.session_state.current_game_id = game_id_join
                    st.session_state.player_name = player_name_join.strip()
                    st.success(f"✅ Infiltrated game {game_id_join}!")
                    time.sleep(1)
                    st.rerun()

else:
    # In-game interface
    game_id = st.session_state.current_game_id
    player_name = st.session_state.player_name
    games = get_games()
    game = games.get(game_id)
    
    if not game:
        st.error("💥 Game not found! It might have been terminated.")
        st.session_state.current_game_id = None
        st.rerun()
    
    # Update host status
    st.session_state.is_host = (game['host'] == player_name)
    
    # Game header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.header(f"🎯 Mission Room: {game_id}")
    with col2:
        if st.button("🚪 Abort Mission", type="secondary"):
            leave_game(game_id, player_name)
            st.session_state.current_game_id = None
            st.session_state.player_name = None
            st.session_state.is_host = False
            st.rerun()
    with col3:
        st.write(f"**Agent:** {player_name}")
    
    # Game status
    if not game['game_started']:
        # Waiting room
        st.subheader("🕴️ Agent Briefing Room")
        st.write("*Agents are gathering for the mission briefing...*")
        
        # Ready button
        current_ready = player_name in game['ready_players']
        ready_button_text = "✅ Ready for Action!" if current_ready else "⏳ Still Preparing..."
        ready_button_type = "secondary" if current_ready else "primary"
        
        if st.button(ready_button_text, type=ready_button_type):
            toggle_ready(game_id, player_name)
            st.rerun()
        
        # Players list with live updates
        st.subheader("🕵️ Active Agents")
        
        if game['players']:
            agents_ready = []
            agents_not_ready = []
            
            for p_name, p_info in game['players'].items():
                ready_status = "✅ Ready" if p_name in game['ready_players'] else "⏳ Preparing"
                host_badge = " 👑" if p_name == game['host'] else ""
                you_badge = " (You)" if p_name == player_name else ""
                
                agent_info = f"**{p_name}**{host_badge}{you_badge}: {ready_status}"
                
                if p_name in game['ready_players']:
                    agents_ready.append(agent_info)
                else:
                    agents_not_ready.append(agent_info)
            
            # Show ready agents first
            for agent in agents_ready:
                st.write(f"🟢 {agent}")
            for agent in agents_not_ready:
                st.write(f"🔴 {agent}")
        else:
            st.write("👻 No agents in the briefing room")
        
        # Start game button (host only)
        if st.session_state.is_host:
            total_players = len(game['players'])
            ready_count = len(game['ready_players'])
            
            st.markdown("---")
            st.write(f"🎯 Agents ready: **{ready_count}/{total_players}**")
            
            if total_players >= 3 and ready_count == total_players:
                if st.button("🚀 Launch Mission!", type="primary"):
                    if start_game(game_id):
                        st.success("🎯 Mission is a GO!")
                        time.sleep(1)
                        st.rerun()
            else:
                if total_players < 3:
                    st.info("🔢 Need at least 3 agents to start the mission")
                else:
                    st.info("⏳ Waiting for all agents to gear up")
    
    elif game['game_ended']:
        # Game ended - show results with funny messages
        funny_message = get_funny_game_over_message(
            game['winner'], 
            game['spy'], 
            game['location'], 
            game.get('elimination_target')
        )
        
        st.markdown(f"""
        <div class="winner-announcement {'spy-wins' if game['winner'] == 'spy' else 'non-spy-wins'}">
            🎉 {game['winner'].upper().replace('NON-SPIES', 'DETECTIVES')} WIN! 🎉
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class="game-over-message">
            {funny_message}
        </div>
        """, unsafe_allow_html=True)
        
        # Reveal the spy with dramatic flair
        st.markdown("### 🎭 The Master of Disguise Was:")
        st.markdown(f"## **🕵️ {game['spy']} 🕵️**")
        
        st.markdown(f"### 📍 The Secret Location Was:")
        st.markdown(f"## **🏢 {game['location']} 🏢**")
        
        # Show elimination results if applicable
        if 'elimination_target' in game and game['elimination_target']:
            st.markdown(f"### 🗳️ Eliminated Agent:")
            st.markdown(f"**💀 {game['elimination_target']} 💀**")
            st.write("*They fought bravely but fell to democracy!*")
        
        # Show location guesses if any
        if game.get('location_guesses'):
            st.markdown("### 🎯 Spy's Location Guesses:")
            for player, guess in game['location_guesses'].items():
                correct = "✅" if guess == game['location'] else "❌"
                st.write(f"**{player}**: {guess} {correct}")
        
        # Show all players and their roles
        st.markdown("### 👥 Final Agent Roster:")
        for p_name in game['players']:
            role = "🕵️ SPY" if p_name == game['spy'] else "🔍 DETECTIVE"
            st.write(f"**{p_name}**: {role}")
        
        # New game button (host only)
        if st.session_state.is_host:
            st.markdown("---")
            if st.button("🔄 Start New Mission", type="primary"):
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
                games[game_id]['location_guesses'] = {}
                
                # Reset all players to not ready
                for p_name in games[game_id]['players']:
                    games[game_id]['players'][p_name]['is_ready'] = False
                
                save_games(games)
                st.rerun()
    
    else:
        # Game in progress
        st.subheader("🎯 Mission in Progress!")
        
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
            timer_class = "timer-danger" if time_remaining <= 30 else "timer-normal"
            st.markdown(f"""
            <div class="{timer_class}">
                ⏰ {time_display}
            </div>
            """, unsafe_allow_html=True)
            
            # Tension sound for last 30 seconds
            if time_remaining <= 30 and time_remaining > 0 and sound_enabled:
                st.markdown("""
                <audio autoplay>
                    <source src="data:audio/wav;base64,UklGRnYBAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YVIBAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=" type="audio/wav">
                </audio>
                """, unsafe_allow_html=True)
        
        # Show role with funny descriptions
        role_description = get_funny_role_description(player_name == game['spy'])
        
        if player_name == game['spy']:
            st.markdown(f"""
            <div class="role-card spy-card">
                {role_description}
            </div>
            """, unsafe_allow_html=True)
            
            # Location guessing section for spy
            st.markdown("""
            <div class="location-guess-section">
                <h3>🎯 Location Guessing HQ</h3>
                <p>Try to figure out where you are! You can eliminate locations you think it's NOT.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # All possible locations
            all_locations = [
                "Restaurant", "School", "Hospital", "Bank", "Airport",
                "Beach", "Casino", "Circus", "Embassy", "Hotel",
                "Military Base", "Movie Studio", "Museum", "Ocean Liner",
                "Passenger Train", "Pirate Ship", "Polar Station", "Police Station",
                "Space Station", "Submarine", "Supermarket", "Theater", "University",
                "Library", "Zoo", "Gym", "Spa", "Bakery", "Farm", "Prison",
                "Art Gallery", "Nightclub", "Workshop", "Cathedral", "Laboratory"
            ]
            
            # Show eliminated locations
            if st.session_state.location_guesses:
                st.write("❌ **Eliminated Locations:**")
                for loc in st.session_state.location_guesses:
                    st.write(f"• {loc}")
            
            # Location selection
            remaining_locations = [loc for loc in all_locations if loc not in st.session_state.location_guesses]
            
            if remaining_locations:
                col1, col2 = st.columns([3, 1])
                with col1:
                    selected_location = st.selectbox("Choose a location:", remaining_locations)
                with col2:
                    if st.button("❌ Eliminate"):
                        if selected_location not in st.session_state.location_guesses:
                            st.session_state.location_guesses.append(selected_location)
                            st.success(f"Eliminated {selected_location}!")
                            st.rerun()
                
                # Final guess button
                if len(remaining_locations) <= 5:
                    st.write("🎯 **Ready to make your final guess?**")
                    final_guess = st.selectbox("Final location guess:", remaining_locations, key="final_guess")
                    
                    if st.button("🎯 FINAL GUESS!", type="primary"):
                        if guess_location(game_id, player_name, final_guess):
                            if final_guess == game['location']:
                                end_game(game_id, "spy")
                                st.success("🎉 CORRECT! You win!")
                            else:
                                st.error(f"❌ Wrong! The location was {game['location']}")
                                end_game(game_id, "non-spies")
                            st.rerun()
            else:
                st.error("You've eliminated all locations! That's... not how this works! 😅")
        
        else:
            st.markdown(f"""
            <div class="role-card non-spy-card">
                {role_description}
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="text-align: center; font-size: 2rem; padding: 20px; margin: 15px 0; 
                       background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%); 
                       color: white; border-radius: 15px; font-weight: bold;">
                📍 SECRET LOCATION: {game['location']}
            </div>
            """, unsafe_allow_html=True)
            
            st.write("🕵️ **Your Mission:** Ask clever questions to expose the spy without giving away the location!")
        
        # Voting section
        if not game['voting_phase']:
            # Start voting button (any player can start voting)
            if st.button("🗳️ Initiate Elimination Protocol", type="primary"):
                start_voting(game_id)
                st.rerun()
        else:
            # Anonymous voting interface
            st.markdown("""
            <div class="vote-section">
                <h3>🗳️ ANONYMOUS ELIMINATION VOTE</h3>
                <p>Vote to eliminate someone! Your vote is completely anonymous.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Show vote count (anonymous)
            total_votes = len([v for v in game['votes'].values() if v['voter']])
            total_players = len(game['players'])
            
            st.write(f"🗳️ **Anonymous votes cast:** {total_votes}/{total_players}")
            
            # Check if current player has voted
            player_voted = any(v['voter'] == player_name for v in game['votes'].values())
            
            # Voting form
            if not player_voted:
                other_players = [p for p in game['players'].keys() if p != player_name]
                selected_target = st.selectbox("🎯 Vote to eliminate:", other_players)
                
                if st.button(f"🗳️ Cast Anonymous Vote", type="primary"):
                    vote_player(game_id, player_name, selected_target)
                    st.success("✅ Your anonymous vote has been cast!")
                    st.rerun()
            else:
                st.info("✅ You have already cast your anonymous vote!")
            
            # Check if all players have voted
            if total_votes == total_players:
                # Count votes by target
                vote_counts = {}
                for vote_data in game['votes'].values():
                    target = vote_data['target']
                    vote_counts[target] = vote_counts.get(target, 0) + 1
                
                # Show results
                st.write("📊 **Final Vote Results:**")
                for target, count in sorted(vote_counts.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"• **{target}**: {count} vote(s)")
                
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
                    st.warning("🤝 It's a tie! No one gets eliminated. The mission continues!")
                    # Reset voting
                    games = get_games()
                    games[game_id]['voting_phase'] = False
                    games[game_id]['votes'] = {}
                    save_games(games)
                    st.rerun()
        
        # Game instructions
        with st.expander("🎮 Mission Briefing & Rules"):
            st.markdown("""
            ### 🕵️ For the SPY:
            - You DON'T know the location (you're lost!)
            - Ask questions to figure out where you are
            - Try to blend in and not get caught
            - Use the location elimination tool to narrow down possibilities
            - Make a final guess when you're confident
            - Survive the vote to win!
            
            ### 🔍 For the DETECTIVES:
            - You KNOW the secret location
            - Ask questions to identify the confused spy
            - Don't make the location too obvious in your questions
            - Vote to eliminate the spy when you're ready
            - Work together to catch the impostor!
            
            ### ⚖️ General Rules:
            - Game lasts 5 minutes ⏰
            - Take turns asking each other questions about the location
            - Questions should be location-related but not too obvious
            - Any player can start the elimination vote
            - All votes are completely anonymous 🤐
            - **SPY WINS:** If time runs out OR if a detective gets eliminated
            - **DETECTIVES WIN:** If they successfully eliminate the spy
            
            ### 🎯 Pro Tips:
            - Spies: Listen carefully to answers for location clues
            - Detectives: Watch for players giving vague or confused answers
            - Everyone: Be creative with your questions!
            """)
        
        # Players in game with enhanced display
        st.markdown("""
        <div class="player-list">
            <h3>🕵️ Active Agents in Mission</h3>
        </div>
        """, unsafe_allow_html=True)
        
        for p_name in game['players']:
            role_hint = " 🕵️" if p_name == game['spy'] and player_name == game['spy'] else ""
            you_badge = " (You)" if p_name == player_name else ""
            host_badge = " 👑" if p_name == game['host'] else ""
            st.write(f"• **{p_name}**{you_badge}{host_badge}{role_hint}")

# Auto-refresh functionality
if auto_refresh and st.session_state.current_game_id:
    time.sleep(refresh_rate)
    st.rerun()

# Enhanced footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; font-style: italic; color: #666; padding: 20px;">
    <strong>🎭 Made with ❤️ and a lot of suspicious behavior using Streamlit</strong><br>
    <em>May the best spy win... or may the best detectives catch them! 🕵️‍♀️🔍</em>
</div>
""", unsafe_allow_html=True)