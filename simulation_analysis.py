import pandas as pd
from itertools import combinations_with_replacement
import pygame
import sys
import os
from twoD import *

# Redirect pygame output to devnull to suppress hello message
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


def run_multiple_games(red_def, red_att, blue_def, blue_att, num_games=50):
    results = []
    
    print(f"Running {num_games} games with:")
    print(f"Red team: {red_def} defenders, {red_att} attackers")
    print(f"Blue team: {blue_def} defenders, {blue_att} attackers")
    
    for game in range(num_games):
        print(f"Running game {game + 1}/{num_games}", end='\r')
        
        # Initialize simulation
        simulation = FootballSimulation(red_defenders=red_def, red_attackers=red_att,
                                      blue_defenders=blue_def, blue_attackers=blue_att)
        
        # Run without visual display for speed
        pygame.display.set_mode((f_length, f_width), flags=pygame.HIDDEN)
        
        # Run single game
        while not simulation.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
            
            if time.time() - simulation.start_time >= GAME_DURATION:
                simulation.game_over = True
            
            simulation.update_pursuers()
            for player in simulation.players:
                player.move(simulation.ball, simulation.players)
            
            simulation.ball.move()
            if simulation.ball.is_ball_stuck():
                simulation.reset_after_goal()
            simulation.check_goal()
            
            simulation.clock.tick(120)
        
        # Record results
        winner = "Red" if simulation.red_score > simulation.blue_score else "Blue"
        if simulation.red_score == simulation.blue_score:
            winner = "Draw"
            
        results.append({
            'game_number': game + 1,
            'red_defenders': red_def,
            'red_attackers': red_att,
            'blue_defenders': blue_def,
            'blue_attackers': blue_att,
            'red_score': simulation.red_score,
            'blue_score': simulation.blue_score,
            'winner': winner
        })
    
    # Create DataFrame and save to Excel
    df = pd.DataFrame(results)
    filename = 'simulation_results_GK_Strstegy.xlsx'
    
    # Calculate summary statistics
    summary = {
        'Total Games': len(df),
        'Red Wins': (df['winner'] == 'Red').sum(),
        'Blue Wins': (df['winner'] == 'Blue').sum(),
        'Draws': (df['winner'] == 'Draw').sum(),
        'Average Red Score': df['red_score'].mean(),
        'Average Blue Score': df['blue_score'].mean()
    }
    
    summary_df = pd.DataFrame([summary])
    
    # Save both detailed results and summary to Excel
    with pd.ExcelWriter(filename) as writer:
        df.to_excel(writer, sheet_name='Detailed Results', index=False)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
    
    print(f"\nResults saved to {filename}")
    
    # Print summary
    print("\nSummary of Results:")
    print(f"Red Wins: {summary['Red Wins']} ({summary['Red Wins']/summary['Total Games']*100:.1f}%)")
    print(f"Blue Wins: {summary['Blue Wins']} ({summary['Blue Wins']/summary['Total Games']*100:.1f}%)")
    print(f"Draws: {summary['Draws']} ({summary['Draws']/summary['Total Games']*100:.1f}%)")
    print(f"Average Score - Red: {summary['Average Red Score']:.2f}, Blue: {summary['Average Blue Score']:.2f}")

# Example usage
if __name__ == "__main__":
    # You can change these values to whatever combination you want to test
    run_multiple_games(red_def=2, red_att=1, blue_def=2, blue_att=1, num_games=20)