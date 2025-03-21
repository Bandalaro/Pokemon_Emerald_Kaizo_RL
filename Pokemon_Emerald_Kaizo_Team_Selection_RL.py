# -*- coding: utf-8 -*-
"""Untitled55.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1dhdFfqEoSU3EDUNkQrG7oF52YHwqBJUU
"""

import requests
import json
import numpy as np
import random
import time

# Load player team from JSON file
def load_player_team(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Fetch Pokémon data from PokéAPI with improved error handling and retries
def fetch_pokemon_data(pokemon_name):
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    for attempt in range(3):  # Retry up to 3 times
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print(f"Fetched data for {pokemon_name}: {json.dumps(data, indent=2)[:500]}...")  # Print first 500 characters
            return data
        elif response.status_code == 404:
            print(f"Error: Pokémon '{pokemon_name}' not found in API.")
            return None
        else:
            print(f"Warning: API request failed for {pokemon_name} (Attempt {attempt + 1}/3). Retrying...")
            time.sleep(2)
    print(f"Error: Failed to fetch data for {pokemon_name} after 3 attempts.")
    return None

# Get Pokémon by type from API while ensuring it is fully evolved and non-legendary
def fetch_pokemon_by_type(pokemon_type):
    url = f"https://pokeapi.co/api/v2/type/{pokemon_type.lower()}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        pokemon_list = [p["pokemon"]["name"] for p in data["pokemon"] if "legendary" not in p["pokemon"]["name"]]
        return random.choice(pokemon_list) if pokemon_list else "arcanine"
    print(f"Error: Failed to fetch Pokémon for type '{pokemon_type}'")
    return "arcanine"

# Get Pokémon moveset based on level cap and avoid duplicates
def get_moves(pokemon_data, level_cap):
    if not pokemon_data:
        return ["Tackle"]  # Default move if no data found

    moves = set()
    for move in pokemon_data.get("moves", []):
        for version in move.get("version_group_details", []):
            if version.get("move_learn_method", {}).get("name") == "level-up" and version.get("level_learned_at", 999) <= level_cap:
                moves.add(move["move"]["name"])

    selected_moves = list(moves)[:4]
    print(f"Selected moves: {selected_moves}")
    return selected_moves if selected_moves else ["Tackle"]  # Ensure at least one move

# RL Q-learning Agent for AI Team Selection
class QLearningAgent:
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.2):
        self.q_table = {}
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon

    def get_q_value(self, state, action):
        return self.q_table.get((state, action), 0.0)

    def select_action(self, state):
        if random.uniform(0, 1) < self.epsilon:
            return random.choice(self.actions)
        else:
            q_values = [self.get_q_value(state, a) for a in self.actions]
            return self.actions[np.argmax(q_values)]

    def update(self, state, action, reward, next_state):
        best_next_q = max([self.get_q_value(next_state, a) for a in self.actions], default=0.0)
        current_q = self.get_q_value(state, action)
        self.q_table[(state, action)] = current_q + self.alpha * (reward + self.gamma * best_next_q - current_q)

# Select AI team based on Q-learning and player Pokémon strength
def select_ai_team(player_team):
    ai_team = []
    agent = QLearningAgent(actions=["balanced", "offensive", "defensive"])
    team_strategy = agent.select_action("start")

    for pokemon in player_team["team"]:
        print(f"Fetching data for player Pokémon: {pokemon['name']}")
        data = fetch_pokemon_data(pokemon["name"])
        if data:
            types = [t["type"]["name"] for t in data["types"]]
            print(f"{pokemon['name']} has types: {types}")
            counter_type = random.choice(types)
            counter_pokemon_name = fetch_pokemon_by_type(counter_type)
            print(f"Selected counter Pokémon: {counter_pokemon_name}")
            counter_data = fetch_pokemon_data(counter_pokemon_name)
            ai_team.append({
                "name": counter_pokemon_name,
                "level": max(pokemon["level"], random.randint(pokemon["level"], pokemon["level"] + 5)),
                "hitpoints": random.randint(190, 250),
                "status": "Healthy",
                "ability": counter_data["abilities"][0]["ability"]["name"] if counter_data else "Unknown",
                "moves": get_moves(counter_data, max(pokemon["level"], 50))
            })
    return ai_team

# Main function
def main():
    with open("pokemon_team.json", "r") as file:
        player_team = json.load(file)

    if "team" not in player_team:
        print("Error: Incorrect JSON format. Expected a 'team' key.")
        return

    ai_team = select_ai_team(player_team)

    with open("ai_team_output.json", "w") as file:
        json.dump(ai_team, file, indent=4)

    print("AI team selection and move decisions saved to ai_team_output.json")

if __name__ == "__main__":
    main()