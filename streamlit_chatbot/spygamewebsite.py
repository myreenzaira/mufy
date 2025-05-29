import streamlit as st
import random
import time

# Sample list of locations
locations = ["Beach", "Airport", "School", "Hospital", "Cinema"]

# Initialize session state
if "roles" not in st.session_state:
    st.session_state.roles = ["Spy"] + ["Player"] * 4
    random.shuffle(st.session_state.roles)
    st.session_state.location = random.choice(locations)
    st.session_state.start_time = time.time()
    st.session_state.show_roles = [False] * 5
    st.session_state.timer_started = False

st.title("Spy Game")

# Start the game
if st.button("Start Game") and not st.session_state.timer_started:
    st.session_state.timer_started = True
    st.session_state.start_time = time.time()

# Show each player's role
for i in range(5):
    if st.button(f"Reveal Role for Player {i + 1}", key=f"btn_{i}"):
        st.session_state.show_roles[i] = True

    if st.session_state.show_roles[i]:
        role = st.session_state.roles[i]
        if role == "Spy":
            st.write(f"Player {i + 1}: You are the **Spy**!")
        else:
            st.write(f"Player {i + 1}: Your location is **{st.session_state.location}**.")

# Timer display
if st.session_state.timer_started:
    elapsed = int(time.time() - st.session_state.start_time)
    remaining = 300 - elapsed  # 5 minutes = 300 seconds
    if remaining > 0:
        st.write(f"Time Remaining: {remaining // 60}:{remaining % 60:02}")
    else:
        st.write("⏰ Time's up!")
        st.session_state.timer_started = False

# Manual end button
if st.button("Reveal All Roles"):
    for i in range(5):
        role = st.session_state.roles[i]
        if role == "Spy":
            st.write(f"Player {i + 1}: **Spy**")
        else:
            st.write(f"Player {i + 1}: Location - **{st.session_state.location}**")
