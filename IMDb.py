import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import warnings
import bs4
import requests
import time
import random as ran
import sys
import pandas as pd
import plotly.graph_objects as go
import dash_bootstrap_components as dbc

warnings.filterwarnings('ignore')

url = 'https://www.imdb.com/search/title?release_date=2023&sort=boxoffice_gross_us,desc&start=1'

source = requests.get(url).text
#print(source)

soup = bs4.BeautifulSoup(source, 'html.parser')
#print(soup)
movie_blocks = soup.findAll('div', {'class': 'lister-item-content'})


def scrape_mblock(movie_block):
    movieb_data = {}
    try:
        movieb_data['name'] = movie_block.find('a').get_text()  # Name of the movie
    except:
        movieb_data['name'] = None

    try:
        movieb_data['year'] = str(movie_block.find('span', {'class': 'lister-item-year'}).contents[0][1:-1])  # Release year
    except:
        movieb_data['year'] = None

    try:
        movieb_data['duration'] = int(movie_block.find('span', {'class': 'runtime'}).contents[0].strip(' min'))  # duration
    except:
        movieb_data['duration'] = None

    try:
        movieb_data['genre'] = ''.join(movie_block.find('span', {'class': 'genre'}).contents[0].split(',')[0].strip('\n '))  # genre
    except:
        movieb_data['genre'] = None

    try:
        movieb_data['rating'] = float(movie_block.find('div', {'class': 'inline-block ratings-imdb-rating'}).get('data-value'))  # rating
    except:
        movieb_data['rating'] = None

    try:
        movieb_data['m_score'] = float(movie_block.find('span', {'class': 'metascore favorable'}).contents[0].strip())  # meta score
    except:
        movieb_data['m_score'] = None

    try:
        movieb_data['votes'] = int(movie_block.find('span', {'name': 'nv'}).get('data-value'))  # votes
    except:
        movieb_data['votes'] = None

    return movieb_data


def scrape_m_page(movie_blocks):
    page_movie_data = []
    num_blocks = len(movie_blocks)

    for block in range(num_blocks):
        page_movie_data.append(scrape_mblock(movie_blocks[block]))

    return page_movie_data


#print(movie_blocks)
scrape_m_page(movie_blocks)


def scrape_this(link, t_count):

    #from IPython.core.debugger import set_trace

    base_url = link
    target = t_count

    current_mcount_start = 0
    current_mcount_end = 0
    remaining_mcount = target - current_mcount_end

    new_page_number = 1

    movie_data = []

    while remaining_mcount > 0:

        url = base_url + str(new_page_number)

        #set_trace()

        source = requests.get(url).text
        soup = bs4.BeautifulSoup(source, 'html.parser')

        movie_blocks = soup.findAll('div', {'class': 'lister-item-content'})

        movie_data.extend(scrape_m_page(movie_blocks))

        current_mcount_start = int(soup.find("div", {"class": "nav"}).find("div", {"class": "desc"}).contents[1].get_text().split("-")[0])

        current_mcount_end = int(soup.find("div", {"class": "nav"}).find("div", {"class": "desc"}).contents[1].get_text().split("-")[1].split(" ")[0])

        remaining_mcount = target - current_mcount_end

        print('\r' + "currently scraping movies from: " + str(current_mcount_start) + " - " + str(current_mcount_end), "| remaining count: " + str(remaining_mcount), flush=True, end="")

        new_page_number = current_mcount_end + 1

        time.sleep(ran.randint(0, 10))

    return movie_data



base_scraping_link = "https://www.imdb.com/search/title?release_date=2018-01-01,2018-12-31&sort=boxoffice_gross_us,desc&start="

top_movies = 50
films = []

films = scrape_this(base_scraping_link, int(top_movies))

#Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Scrape movie data
df = pd.DataFrame(films)

# Calculate genre counts
genre_counts = df['genre'].value_counts()

# Calculate genre percentages
genre_percentages = genre_counts / len(df) * 100

#pie chart
fig = go.Figure(data=[go.Pie(labels=genre_percentages.index, values=genre_percentages.values)])

# Sort DataFrame by votes in descending order
df_sorted = df.sort_values(by='votes', ascending=False)

#bar plot
bar_fig = px.bar(df_sorted, x='name', y='votes', labels={'name': 'Movie', 'votes': 'Votes'})
bar_fig.update_layout(height=600, width=900)

df_sorted_rates = df.sort_values(by='rating', ascending=False)

#bar plot for movie rankings
ranking_fig = px.bar(df_sorted_rates, x='name', y='rating', labels={'name': 'Movie', 'rating': 'Rating'})
ranking_fig.update_layout(height=600, width=1400)

scatter_fig = go.Figure(data=go.Scatter(x=df_sorted_rates['votes'], y=df_sorted_rates['rating'],
                                       mode='markers', marker=dict(size=8, color=df_sorted_rates['votes'],
                                                                   colorscale='Viridis'),
                                       hovertemplate='<b>%{text}</b><br><br>' +
                                                     'Votes: %{x}<br>' +
                                                     'Rating: %{y}<extra></extra>',
                                       text=df_sorted_rates['name']))

scatter_fig.update_layout(title='Votes vs. Ratings',
                          xaxis_title='Votes', yaxis_title='Rating', height=600, width=1400)

#app layout
app.layout = dbc.Container(
    fluid=True,
    style={'background-color': 'black', 'padding': '20px'},
    children=[
        html.H1('IMDb Dashboard', className='text-center mt-4 mb-4', style={'color': 'red'}),

        html.Div(
            style={
                'text-align': 'center',
                'color': 'white'
            },
            children=[
                html.H2('Movie to Watch:', style={'color': 'blue'}),
                html.H3('Movie Name: {}'.format(df_sorted_rates.iloc[0]['name']),
                        style={'font-weight': 'bold', 'color': 'red', 'border': '2px solid red', 'padding': '5px'}),
                html.H3('Type: {}'.format(df_sorted_rates.iloc[0]['genre']),
                        style={'font-weight': 'bold', 'color': 'red', 'border': '2px solid red', 'padding': '5px'}),
                html.H3('Duration: {} min'.format(df_sorted_rates.iloc[0]['duration']),
                        style={'font-weight': 'bold', 'color': 'red', 'border': '2px solid red', 'padding': '5px'}),
                html.H3('Rating: {}'.format(df_sorted_rates.iloc[0]['rating']),
                        style={'font-weight': 'bold', 'color': 'red', 'border': '2px solid red', 'padding': '5px'}),
            ]
        ),

        dbc.Row([
            dbc.Col([
                html.H2('Movies votes', style={'color': 'white'}),
                dcc.Graph(id='bar-plot', figure=bar_fig),
            ], width=8, style={'border': '2px solid blue'}),
            dbc.Col([
                html.H2('Movies types', style={'color': 'white'}),
                dcc.Graph(id='genre-pie-chart', figure=fig)
            ], width=4, style={'border': '2px solid blue'})
        ]),
        html.Hr(style={'background-color': 'blue'}),
        dbc.Row([
            dbc.Col([
                html.H2('Highest-rated movies', style={'color': 'white'}),
                dcc.Graph(id='ranking-fig', figure=ranking_fig)
            ], style={'border': '2px solid blue'}),
        ]),
        dbc.Row([
            dbc.Col([
                html.H2('Rates and Votes', style={'color': 'white'}),
                dcc.Graph(id='scatter-plot', figure=scatter_fig)
            ], style={'border': '2px solid blue'})
        ])
    ]
)

if __name__ == '__main__':
    app.run_server(debug=True)
