import seaborn as sns
import matplotlib.pyplot as plt
from sklearn import linear_model
import numpy as np
from scrape import Game
import pandas as pd
import pickle
import os

def extract_games():
    """
    Extract games from allgames.txt
    
    Returns:
        list: list of games.  Each element is list is [date, home_team, away_team]
        example element: ['01.01.2016', 'TOR', 'CHI']
    """
    games = []
    with open('allgames.txt', 'r') as f:
        for line in f:
            game = line.split('.')
            date = "{game[0]}.{game[1]}.{game[2]}".format(game=game)
            away = game[3]
            home = game[5]
            games.append([date, home, away])
    return games
    
def get_spacing_statistics(date, home_team, away_team, write_file=False, write_score=False, write_game=False):
    """
    Calculates spacing statistics for each frame in game
    
    Args:
        date (str): date of game in form 'MM.DD.YYYY'.  Example: '01.01.2016'
        home_team (str): home team in form 'XXX'. Example: 'TOR'
        away_team (str): away team in form 'XXX'. Example: 'CHI'
        write_file (bool): If True, write pickle file of statistics into data/spacing directory
        
    Returns: 
        tuple: tuple of data (home_offense_areas, home_defense_areas,
               away_offense_areas, away_defense_areas), where each element of the tuple
               is a list of convex hull areas for each frame in the game.
    """
    filename = "{date}-{away_team}-{home_team}.p".format(date=date, away_team=away_team, home_team=home_team)
    if filename in os.listdir('./data/spacing'):
        return
    game = Game(date, home_team, away_team)
    if write_game:
        pickle.dump(game, open( 'data/game/' + filename, "wb"))
    home_offense_areas, home_defense_areas = [], []
    away_offense_areas, away_defense_areas = [], []
    print(date, home_team, away_team)
    for frame in range(len(game.moments)):
        offensive_team = game.get_offensive_team(frame)
        if offensive_team:
            home_area, away_area = game.get_spacing_area(frame)
            if offensive_team == 'home':
                home_offense_areas.append(home_area)
                away_defense_areas.append(away_area)
            if offensive_team == 'away':
                home_defense_areas.append(home_area)
                away_offense_areas.append(away_area)
    results = (home_offense_areas, home_defense_areas,
               away_offense_areas, away_defense_areas)

    if write_file:
        filename = "{date}-{away_team}-{home_team}".format(date=date, away_team=away_team, home_team=home_team)
        pickle.dump(results,  open( 'data/spacing/' + filename + '.p', "wb"))
    
    if write_score:
        score = game.pbp['SCORE'].ix[len(game.pbp) - 1]
        pickle.dump(score,  open( 'data/score/' + filename + '.p', "wb"))

    return(home_offense_areas, home_defense_areas,
           away_offense_areas, away_defense_areas)
           
def write_spacing(gamelist):
    """
    Writes all spacing statistics to data/spacing directory for every game
    """
    for game in gamelist:
        try:
            get_spacing_statistics(game[0], game[1], game[2], write_file=True, write_score=True, write_game=True)
        except:
            with open('errorlog.txt', 'a') as myfile:
                myfile.write("{game} Could not extract spacing data\n".format(game=game))

def plot_spacing(date, home_team, away_team, defense=True):
    """
    Plots team's spacing distrubution in a game.
    
    Args:
        date (str): date of game in form 'MM.DD.YYYY'.  Example: '01.01.2016'
        home_team (str): home team in form 'XXX'. Example: 'TOR'
        away_team (str): away team in form 'XXX'. Example: 'CHI'
        defense (bool): if True, plot defensive spacing.  if False, plot offensive spacing
        
    Returns: None
        Also, shows plt.hist of team spacing during game
        
    """
    filename = "{date}-{away_team}-{home_team}".format(date=date, away_team=away_team, home_team=home_team)
    plt.figure()
    if defense:
        plt.hist(f[1], bins=100, alpha=0.4, label=home_team)
        plt.hist(f[3], bins=100, alpha=0.4, label=away_team)
    else:
        plt.hist(f[0], bins=100, alpha=0.4, label=home_team)
        plt.hist(f[1], bins=100, alpha=0.4, label=away_team)
    plt.xlim(20,100)
    plt.legend(loc='upper right')
    plt.show()
    
def get_spacing_details(game):
    """
    
    """
    fname = "{game[0]}-{game[2]}-{game[1]}.p".format(game=game)
    if fname in os.listdir('data/spacing') and fname in os.listdir('data/score'):
        data = pickle.load(open( "data/spacing/"+fname, "rb" ))
        score = pickle.load(open( "data/score/"+fname, "rb" )).split(' ')
        away_points, home_points = score[0], score[2]
        means = tuple(map(lambda x: np.mean(x), data))
        return (int(home_points), int(away_points), *means)
    else:
        return None

def get_spacing_df(gamelist):
    details = []
    for game in gamelist:
        detail = get_spacing_details(game)
        if detail:
            details.append((*detail,game[1], game[2]) )
    df = pd.DataFrame(details)
    df.columns = ['home_points', 'away_points', 'home_offense_areas',
                         'home_defense_areas', 'away_offense_areas', 'away_defense_areas',
                         'away_team', 'home_team']
    df['space_dif'] = df.away_defense_areas - df.home_defense_areas
    df['home_win'] = np.sign(df.home_points - df.away_points)
    df = df[df.home_offense_areas >80]
    return df

def plot_offense_vs_defense_spacing(spacing_data):
    sns.regplot(spacing_data.away_offense_areas, spacing_data.home_defense_areas, fit_reg=True, color=sns.color_palette()[0], ci=None)
    sns.regplot(spacing_data.home_offense_areas, spacing_data.away_defense_areas, fit_reg=False, color=sns.color_palette()[0], ci=None)
    plt.xlabel('Average Offensive Spacing (sq ft)', fontsize=16)
    plt.ylabel('Average Defensive Spacing (sq ft)', fontsize=16)
    plt.title('Offensive spacing robustly induces defensive spacing', fontsize=16)
    
def plot_defense_spacing_vs_score(spacing_data):
    y = spacing_data.home_points - spacing_data.away_points
    x = spacing_data.away_defense_areas - spacing_data.home_defense_areas
    sns.regplot(x, y, ci=False)
    plt.xlabel(' Home Team Defensive Spacing Differential (sq ft)', fontsize=16)
    plt.ylabel('Home Team Score Differential (pts)', fontsize=16)
    plt.title('Spacing the defense correlates with outscoring opponents', fontsize=16)
    
def plot_defense_spacing_vs_wins(spacing_data):
    clf = linear_model.LogisticRegression(C=1)
    X = np.array(spacing_data.space_dif)
    X = X[:, np.newaxis]
    y = np.array(spacing_data.home_win)
    y_adjusted = (y+1) / 2
    clf.fit(X, y)
    plt.scatter(X.ravel(), y_adjusted, color=sns.color_palette()[0], s=600, alpha=1, marker='|' )
    plt.xlim(-10, 10)
    X_test = np.linspace(-10, 10, 300)
    X_test = X_test[:, np.newaxis]
    clf.predict(X_test)
    amount = X_test * clf.coef_ 
    def model(x):
        return 1 / (1 + np.exp(-x))
    loss = model(X_test * clf.coef_ + clf.intercept_).ravel()
    plt.scatter(X_test.ravel(), loss)
    plt.xlabel('Home Team Defensive Spacing Differential (sq ft)', fontsize=16)
    plt.ylabel('Home Team Win', fontsize=16)
    plt.title('Spacing the Defense Correlates with winning', fontsize=16)

def plot_team_defensive_spacing(spacing_data):
    df=pd.DataFrame()
    df['home']  = spacing_data.groupby('home_team')['away_defense_areas'].sum()
    df['home_count'] = spacing_data.groupby('home_team')['away_defense_areas'].count()
    df['away'] = spacing_data.groupby('away_team')['home_defense_areas'].sum()
    df['away_count'] = spacing_data.groupby('away_team')['home_defense_areas'].count()
    df['average_induced_space'] = (df.home + df.away) / (df.away_count + df.home_count)
    df['average_induced_space'].sort_values().plot(kind='bar', color=sns.color_palette()[0])
    plt.xlabel('Team', fontsize=16)
    plt.ylabel("Opponent's Defensive Spacing", fontsize=16)
    plt.ylim(60,70)

def plot_teams_ability_to_space_defense(spacing_data):
    df=pd.DataFrame()
    df['home']  = spacing_data.groupby('home_team')['away_defense_areas'].sum()
    df['home_count'] = spacing_data.groupby('home_team')['away_defense_areas'].count()
    df['away'] = spacing_data.groupby('away_team')['home_defense_areas'].sum()
    df['away_count'] = spacing_data.groupby('away_team')['home_defense_areas'].count()
    df['average_induced_space'] = (df.home + df.away) / (df.away_count + df.home_count)
    
    df['home_offense']  = spacing_data.groupby('home_team')['home_offense_areas'].sum()
    df['home_offesne_count'] = spacing_data.groupby('home_team')['home_offense_areas'].count()
    df['away_offense'] = spacing_data.groupby('away_team')['away_offense_areas'].sum()
    df['away_count'] = spacing_data.groupby('away_team')['away_offense_areas'].count()

    plt.xlabel('Team', fontsize=16)
    plt.ylabel("Opponent's Defensive Spacing", fontsize=16)
    plt.ylim(60,70)


if __name__ == "__main__":
    games = extract_games()
    #write_spacing(games)
    spacing_data = get_spacing_df(games)
    #plot_offense_vs_defense_spacing(spacing_data)
    #plot_defense_spacing_vs_score(spacing_data)
    #plot_defense_spacing_vs_wins(spacing_data)
    #plot_team_defensive_spacing(spacing_data)

    
