# PROJECT PHANTOM PURSUIT
import random
import sys
import os
import json
from heapq import heappush, heappop
import networkx as nx
import matplotlib.pyplot as plt
from playsound import playsound
import tkinter as tk
from PIL import Image, ImageTk
import time
from collections import deque
import mysql.connector

def connect_to_db():
    print("db connect")
    return mysql.connector.connect(
        host="localhost",
        user="root",  
        password="Ansh!2005",  
        port=3306,
        database="ghost_game"  
    )

def visualize_game_state(game):
    if not hasattr(game, 'G'):
        game.G = nx.random_geometric_graph(24, 0.2)
        edges = list(game.G.edges())
        game.pos = nx.spring_layout(game.G, k=2, seed=42) 

        for u, v in edges:
            
            x1, y1 = game.pos[u]
            x2, y2 = game.pos[v]
            distance = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
            game.G[u][v]['weight'] = round(distance, 2)  

        while not nx.is_connected(game.G):
            largest_cc = max(nx.connected_components(game.G), key=len)
            for node in game.G.nodes():
                if node not in largest_cc:
                    target = random.choice(list(largest_cc))
                    game.G.add_edge(node, target)

    plt.clf()

    nx.draw_networkx_edges(game.G, game.pos, edge_color='gray', width=1, alpha=0.5)
    nx.draw_networkx_nodes(game.G, game.pos, node_color='white', 
                           node_size=500, edgecolors='gray')
    nx.draw_networkx_nodes(game.G, game.pos, 
                           nodelist=[game.player_position-1],
                           node_color='green', node_size=700, 
                           label='Player', node_shape='o')
    nx.draw_networkx_nodes(game.G, game.pos, 
                           nodelist=[game.ghost_position-1],
                           node_color='red', node_size=700, 
                           label='Ghost', node_shape='h')
    
    labels = {i: str(i+1) for i in game.G.nodes()}
    nx.draw_networkx_labels(game.G, game.pos, labels)

    if game.difficulty == 3:
        edge_labels = nx.get_edge_attributes(game.G, 'weight')  
        nx.draw_networkx_edge_labels(game.G, game.pos, edge_labels=edge_labels, font_size=8, font_color='blue')

    plt.text(0.02, 0.004, f'Sanity: {game.sanity}', 
             transform=plt.gca().transAxes, verticalalignment='top')
    plt.text(0.02, 0.057, f'Current Score: {game.current_score}', 
             transform=plt.gca().transAxes, verticalalignment='top')

    difficulty_name = {1: 'Easy', 2: 'Medium', 3: 'Hard'}[game.difficulty]
    plt.title(f'Ghost Game - {difficulty_name} Mode')

    plt.axis('off')
    plt.pause(0.1)

class Game:
    def __init__(self, player_name):
        self.player_name = player_name
        self.load_user_stats()
        self.reset_stats()
        self.difficulty = 1  
        self.history = []  
        
    def reset_stats(self):
        self.sanity = 0
        self.hearts_of_dead = self.user_stats.get('hearts_of_dead', 0)
        self.current_score = 0  
        self.booster_chance = 45
        self.heart_of_dead_chance = 10
        self.player_position = random.randint(1, 25)
        self.ghost_position = self.get_distant_ghost_position()
        self.ghost_hunt = False
        self.hunt_duration = 0
        self.ghost_move_counter = 0

    def get_distant_ghost_position(self):
        while True:
            pos = random.randint(1, 25)
            if self.manhattan_distance(pos, self.player_position) >= 4:
                return pos

    def manhattan_distance(self, pos1, pos2):
        if pos1 == 24:
            pos1 = 23
        if pos2 == 24:
            pos2 = 23
        if hasattr(self, 'G'):
            try:
                return nx.shortest_path_length(self.G, pos1-1, pos2-1)
            except nx.NetworkXNoPath:
                return float('inf')
        return abs((pos1-1) - (pos2-1))  

    def get_neighbors(self, position):
        if hasattr(self, 'G'):
            return [n+1 for n in self.G.neighbors(position-1)]
        return []

    def bfs_pathfinding(self, start, goal):
        if start == 24:
            start = 23
        if goal == 24:
            goal = 23
        if not hasattr(self, 'G'):
            return start

        visited = set()
        queue = deque([(start-1, [start-1])])

        while queue:
            current, path = queue.popleft()
            if current == goal-1:
                return path[1]+1 if len(path) > 1 else start
            if current in visited:
                continue
            visited.add(current)

            for neighbor in self.G.neighbors(current):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))
        return start

    def dijkstra_pathfinding(self, start, goal):
        if start == 24:
            start = 23
        if goal == 24:
            goal = 23
        if not hasattr(self, 'G'):
            return start

        try:
            path = nx.dijkstra_path(self.G, start-1, goal-1)
            return path[1]+1 if len(path) > 1 else start
        except nx.NetworkXNoPath:
            return start

    def astar_pathfinding(self, start, goal):
        if start == 24:
            start = 23
        if goal == 24:
            goal = 23
        if not hasattr(self, 'G'):
            return start

        try:
            path = nx.astar_path(self.G, start-1, goal-1, weight='weight')
            # graph is zero indexed , while start and goal might be 1
            return path[1]+1 if len(path) > 1 else start
        except nx.NetworkXNoPath:
            return start

    def move_ghost(self):
        status_text1 = plt.text(0.5, 1.03, "", transform=plt.gca().transAxes, ha="center", fontsize=12, color="green")
        status_text2 = plt.text(0.5, 1.05, "", transform=plt.gca().transAxes, ha="center", fontsize=12, color="red")
        """Logic to move the ghost based on difficulty level."""
        if self.ghost_hunt:
            self.hunt_duration -= 1
            self.ghost_position = self.select_pathfinding(self.ghost_position, self.player_position)
            if self.hunt_duration == 0:
                self.ghost_hunt = False
                self.ghost_move_counter = 0
                print("The ghost has stopped hunting. You're safe... for now.")
                status_text1.set_text("The ghost has stopped hunting. You're safe... for now.")
                plt.draw()  
                plt.pause(0.1)
                
        else:
            if self.ghost_move_counter >= 5:
                if not self.ghost_hunt:
                    print("The ghost is hunting you! Sanity will decrease by 6 each move.")
                    status_text2.set_text("The ghost is hunting you!")
                    plt.draw()  
                    plt.pause(0.1)
                    playsound("Sound/iseeyou.mp3")
                self.ghost_hunt = True
                self.hunt_duration = random.randint(2, 5)
            else:
                self.ghost_move_counter += 1
                if self.difficulty == 1:
                    if random.random() < 0.6:
                        self.ghost_position = self.select_pathfinding(self.ghost_position, self.player_position)
                elif self.difficulty == 2:
                    if random.random() < 0.8:
                        self.ghost_position = self.select_pathfinding(self.ghost_position, self.player_position)
                else:
                    self.ghost_position = self.select_pathfinding(self.ghost_position, self.player_position)

    def select_pathfinding(self, start, goal):
        """Selects the appropriate pathfinding algorithm based on difficulty."""
        if self.difficulty == 1:
            return self.bfs_pathfinding(start, goal)
        elif self.difficulty == 2:
            return self.dijkstra_pathfinding(start, goal)
        elif self.difficulty == 3:
            return self.astar_pathfinding(start, goal)
        return start

    def load_user_stats(self):
        db = connect_to_db()

        cursor = db.cursor(dictionary=True)
    
        try:
            cursor.execute("SELECT * FROM user_stats WHERE player_name = %s", (self.player_name,))
            result = cursor.fetchone()
        
            if result:
                self.user_stats = result
            else:
                self.user_stats = {
                    "games_played": 0,
                    "total_score": 0,
                    "best_score": 0,
                    "hearts_of_dead": 0
                }
                cursor.execute(
                    "INSERT INTO user_stats (player_name) VALUES (%s)", 
                    (self.player_name,)
            )
                db.commit()
        except mysql.connector.Error as err:
            print(f"Error loading stats: {err}")
            self.user_stats = {
                "games_played": 0,
                "total_score": 0,
                "best_score": 0,
                "hearts_of_dead": 0
            }
        finally:
            cursor.close()
            db.close()

    def save_user_stats(self):
        db = connect_to_db()
        cursor = db.cursor()
    
        try:
            cursor.execute("""
                UPDATE user_stats
                SET games_played = %s, total_score = %s, best_score = %s, hearts_of_dead = %s
                WHERE player_name = %s
            """, (
                self.user_stats['games_played'],
                self.user_stats['total_score'],
                self.user_stats['best_score'],
                self.user_stats['hearts_of_dead'],
                self.player_name
            ))
            db.commit()
        except mysql.connector.Error as err:
            print(f"Error saving stats: {err}")
        finally:
            cursor.close()
            db.close()

    def store(self):
        print("\nWelcome to the store!")
        print("You can exchange 29 points for 1 Heart of the Dead.")
        print(f"Total Score: {self.user_stats['total_score']}")
        print(f"Current Hearts of the Dead: {self.hearts_of_dead}")

        if self.user_stats['total_score'] < 29:
            print("\nYou don't have enough points to exchange for a Heart of the Dead.")
            print("You need at least 29 points.\n")
            return

        while True:
            choice = input("Do you want to exchange points for Hearts of the Dead? (y/n): ").strip().lower()
            if choice == 'y':
                possible_exchanges = self.user_stats['total_score'] // 29
                print(f"You can exchange up to {possible_exchanges} Hearts of the Dead.")
                num_exchanges = input(f"How many Hearts of the Dead would you like to purchase (1-{possible_exchanges})? ").strip()

                if num_exchanges.isdigit():
                    num_exchanges = int(num_exchanges)
                    if 1 <= num_exchanges <= possible_exchanges:
                        self.user_stats['total_score'] -= num_exchanges * 29
                        self.hearts_of_dead += num_exchanges
                        self.user_stats['hearts_of_dead'] = self.hearts_of_dead 
                        self.save_user_stats()
                        playsound("Sound/revive.mp3")
                        print(f"You successfully exchanged {num_exchanges * 29} points for {num_exchanges} Hearts of the Dead!")
                        print(f"Remaining Total Score: {self.user_stats['total_score']}")
                        print(f"Current Hearts of the Dead: {self.hearts_of_dead}")
                    else:
                        print("Invalid number of exchanges. Please enter a valid amount.")
                else:
                    print("Invalid input. Please enter a valid number.")

                continue_shopping = input("Do you want to continue shopping? (y/n): ").strip().lower()
                if continue_shopping == 'n':
                    break
            elif choice == 'n':
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

    def update_stats_on_game_over(self):
        self.user_stats["games_played"] += 1
        
        if self.current_score > self.user_stats["best_score"]:
            self.user_stats["best_score"] = self.current_score
            print(f"New Best Score: {self.current_score}!")
        
        self.user_stats["total_score"] += self.current_score
        self.user_stats["hearts_of_dead"] = self.hearts_of_dead
        self.save_user_stats()

    def display_user_stats(self):
        print(f"\nUser Stats for {self.player_name}:")
        print(f"Games Played: {self.user_stats['games_played']}")
        print(f"Total Score: {self.user_stats['total_score']}")
        print(f"Best Score: {self.user_stats['best_score']}")
        print(f"Hearts of the Dead Collected: {self.user_stats['hearts_of_dead']}")

    def start_game(self):
        self.display_user_stats()

        store_choice = input("\nWould you like to visit the store and exchange points for Hearts of the Dead? (y/n): ").strip().lower()
        if store_choice == 'y':
            self.store()

        self.reset_stats()

        while True:
            try:
                self.difficulty = int(input("Select difficulty level (1-Easy, 2-Medium, 3-Hard): "))
                if self.difficulty in [1, 2, 3]:
                    break
                print("Please enter a valid difficulty level (1, 2, or 3)")
            except ValueError:
                print("Please enter a valid number")

        self.sanity = {1: 100, 2: 70, 3: 50}.get(self.difficulty, 50)
        self.play()

    def handle_ghost_encounter(self):
        status_text = plt.text(0.5, 1.01, "", transform=plt.gca().transAxes, ha="center", fontsize=12, color="red")
        print("The ghost caught you!")
        while self.hearts_of_dead > 0:
            while True:
                respawn_choice = input("You have a Heart of the Dead. Do you want to respawn? (y/n): ").strip().lower()
                status_text.set_text("You Died!")
                if respawn_choice in ('y', 'n'):
                    break
                print("Invalid input. Please enter 'y' or 'n'.")

            if respawn_choice == 'y':
                playsound("Sound/breath.mp3")
                self.hearts_of_dead -= 1
                respawn_sanity = {
                    1: 50,
                    2: 35,  
                    3: 25 
                }
                self.sanity = respawn_sanity.get(self.difficulty, 50)
                print(f"You have been respawned with {self.sanity} sanity points!")
                print(f"Remaining Hearts of the Dead: {self.hearts_of_dead}")
                
                self.player_position = random.randint(1, 25) 
                self.ghost_position = self.get_distant_ghost_position()  
                print(f"Player respawned at position {self.player_position}. Ghost is at {self.ghost_position}.")

                
                return True
            else:
                print("You chose not to respawn. Game Over.")
                status_text.set_text("You Died!")
                playsound("Sound/end.mp3")
                plt.close()
                self.update_stats_on_game_over()
                replay_choice = input("Would you like to view your game history and replay the moves? (y/n): ").strip().lower()
                if replay_choice == 'y':
                    self.review_history()
                else:
                    exit(0)
                exit(0)
        else:
            print("You have no Hearts of the Dead to respawn. Game Over.")
            status_text.set_text("You Died!")
            playsound("Sound/end.mp3")
            plt.close()
            self.update_stats_on_game_over()
            replay_choice = input("Would you like to view your game history and replay the moves? (y/n): ").strip().lower()
            if replay_choice == 'y':
                self.review_history()
            else:
                exit(0)
            exit(0)

    def collect_powerup(self):
        status_text = plt.text(0.5, 1.07, "", transform=plt.gca().transAxes, ha="center", fontsize=12, color="blue")
        if random.randint(1, 100) <= self.booster_chance:
            print("You found a booster tablet! Your sanity is restored.")
            status_text.set_text("You found a booster tablet! Your sanity is restored.")
            plt.draw()  
            plt.pause(0.1)
            self.sanity += 20
        elif random.randint(1, 100) <= self.heart_of_dead_chance:
            print("You found a Heart of the Dead!")
            status_text.set_text("You found a Heart of the Dead!")
            plt.draw() 
            plt.pause(0.1)
            playsound("Sound/revive.mp3")
            self.hearts_of_dead += 1

    def display_loading_screen(self):
        root = tk.Tk()
        root.title("Loading Ghost Game")
        root.geometry("700x800")
        
        image = Image.open("Sound/loading.png")  
        image = image.resize((700, 800))
        photo = ImageTk.PhotoImage(image)
        
        label = tk.Label(root, image=photo)
        label.pack()
        
        def close_loading_screen():
            root.destroy()
        
        root.after(3000, close_loading_screen)
        root.mainloop()


    def record_history(self):
        self.history.append({"player": self.player_position,"ghost": self.ghost_position})

    def review_history(self):
        player_moves = [move["player"] for move in self.history]
        ghost_moves = [move["ghost"] for move in self.history]

        print("Reviewing game history...")
        print(f"Player Moves: {player_moves}")
        print(f"Ghost Moves: {ghost_moves}")
        print("Review completed.")

    def play(self):
        plt.figure(figsize=(10, 10))
        visualize_game_state(self)  
        status_text = plt.text(0.5, 1.03, "", transform=plt.gca().transAxes, ha="center", fontsize=12, color="blue")
        status_text1 = plt.text(0.5, 1.03, "", transform=plt.gca().transAxes, ha="center", fontsize=12, color="red")

        def on_mouse_click(event):
            nonlocal status_text
            if self.sanity <= 0:
                print("Game Over!")
                status_text1.set_text("You Died!")
                playsound("Sound/end.mp3")
                plt.close()
                self.update_stats_on_game_over()

                replay_choice = input("Would you like to view your game history and replay the moves? (y/n): ").strip().lower()
                if replay_choice == 'y':
                    self.review_history()
                    exit(0)

            x, y = event.xdata, event.ydata
            if x is None or y is None:
                status_text.set_text("Click inside the plot area!")
                plt.draw()  
                plt.pause(0.1)
                return
            
            distances = {node: ((pos[0] - x) ** 2 + (pos[1] - y) ** 2) for node, pos in self.pos.items()}
            closest_node = min(distances, key=distances.get) + 1  

            available_moves = self.get_neighbors(self.player_position)

            if closest_node in available_moves:
               
                self.player_position = closest_node
                self.collect_powerup()
                self.move_ghost()
                self.record_history()

                distance_to_ghost = self.manhattan_distance(self.player_position, self.ghost_position)
                base_sanity_loss = {1: 8, 2: 10, 3: 12}.get(self.difficulty, 8)
                proximity_penalty = max(0, (5 - distance_to_ghost) * 2)
                self.sanity -= (base_sanity_loss + proximity_penalty)

                if self.ghost_hunt:
                    self.sanity -= 6  

                self.current_score += 10

                if self.player_position == self.ghost_position:
                    if not self.handle_ghost_encounter():
                        return 

                plt.cla()
                visualize_game_state(self)
                status_text.set_text(
                    f"Position: {self.player_position}, Score: {self.current_score}, "
                    f"Ghost: {self.ghost_position}, Sanity: {self.sanity}"
                )
                plt.draw()
            else:
               
                status_text.set_text("Invalid move! Click on a valid adjacent node.")
                plt.draw() 
                plt.pause(0.1)

        plt.gcf().canvas.mpl_connect('button_press_event', on_mouse_click)

        while self.sanity > 0:
            plt.pause(0.1)  

        print("Game Over!")
        status_text1.set_text("You Died!")
        playsound("Sound/end.mp3")
        plt.close()
        self.update_stats_on_game_over()

        replay_choice = input("Would you like to view your game history and replay the moves? (y/n): ").strip().lower()
        if replay_choice == 'y':
            self.review_history()
            exit(0)

if __name__ == "__main__":
    while True:
        player_name = input("Enter your name: ").strip()
        if player_name:
            print(f"User name is set to: {player_name}")
            break
        else:
            print("Name cannot be empty. Please enter a valid name.")
    
    ready = input(f"Hello {player_name}, are you ready to start the game? (yes/no): ").strip().lower()
    if ready in ["yes", "y"]:
       
        while True:
            print("\nChoose your game mode:")
            print("1. Player vs AI")
            print("2. Player vs Player")
            mode = input("Enter your choice (1 or 2): ").strip()
            
            if mode == "1":
                print("\nYou chose Player vs AI. Good luck against the computer!")
                game = Game(player_name)  
                game.display_loading_screen()
                game.start_game()
                break
            elif mode == "2":
                pass
                """print("\nYou chose Player vs Player. Let the duel begin!")
                game = Game(player_name)  # Player vs Player logic can be handled inside the Game class
                break"""
            else:
                print("Invalid choice. Please enter 1 for Player vs AI or 2 for Player vs Player.")
        
        game.display_user_stats()  
        game.reset_stats() 
        game.play()  

    else:
        print("Come back when you're ready to face the challenge!")


