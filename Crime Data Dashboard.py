import requests
import os
import orjson
import plotly.express as px
from dash import Dash, html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go

#GeoJSON link
current_year = datetime.now()
five_year = current_year - timedelta(days=5*365)
date_string = five_year.strftime("%Y-%m-%d")

crimedatalink = f'https://phl.carto.com/api/v2/sql?q=SELECT+*+FROM+incidents_part1_part2 WHERE dispatch_date >= \'{date_string}\' &filename=incidents_part1_part2&format=geojson&skipfields=cartodb_id'

#establish response, normalize data into decodable json format
response = requests.get(crimedatalink, verify = True)
data = orjson.loads(response.content)

#convert to pandas dataframe
crimedf = pd.json_normalize([i['properties'] for i in data['features']])

#mapping of offenses commited in Philadlephia
offense_categories = {
    "Aggravated Assault Firearm": "Felony",
    "Aggravated Assault No Firearm": "Felony",
    "All Other Offenses": "Varies (Misdemeanor or Felony)",
    "Arson": "Felony",
    "Burglary Non-Residential": "Felony",
    "Burglary Residential": "Felony",
    "DRIVING UNDER THE INFLUENCE": "Misdemeanor (could be Felony)",
    "Disorderly Conduct": "Misdemeanor",
    "Embezzlement": "Felony",
    "Forgery and Counterfeiting": "Felony",
    "Fraud": "Felony",
    "Gambling Violations": "Misdemeanor",
    "Homicide - Criminal": "Felony",
    "Homicide - Justifiable": "Not a Crime (can vary)",
    "Liquor Law Violations": "Misdemeanor",
    "Motor Vehicle Theft": "Felony",
    "Narcotic / Drug Law Violations": "Felony",
    "Offenses Against Family and Children": "Felony",
    "Other Assaults": "Misdemeanor",
    "Other Sex Offenses (Not Commercialized)": "Varies (Misdemeanor or Felony)",
    "Prostitution and Commercialized Vice": "Misdemeanor",
    "Public Drunkenness": "Misdemeanor",
    "Rape": "Felony",
    "Receiving Stolen Property": "Felony",
    "Robbery Firearm": "Felony",
    "Robbery No Firearm": "Felony",
    "Theft from Vehicle": "Varies (Misdemeanor or Felony)",
    "Thefts": "Varies (Misdemeanor or Felony)",
    "Vagrancy/Loitering": "Misdemeanor",
    "Vandalism/Criminal Mischief": "Misdemeanor",
    "Weapon Violations": "Varies (Misdemeanor or Felony)",
    "Homicide - Gross Negligence": "Felony"
}

#data manipulation for addition of broad categorization - Felony vs Misdemeanor
cat_crimedf = crimedf
cat_crimedf['dispatch_date'] = pd.to_datetime(cat_crimedf['dispatch_date'])
cat_crimedf['year'] = cat_crimedf['dispatch_date'].dt.year
cat_crimedf['Category'] = cat_crimedf['text_general_code'].map(offense_categories)
cat_crimedf

cat_crimedf = crimedf.groupby(['year','Category']).size().reset_index(name='count')
cat_crimedf

category_fig = px.bar(cat_crimedf, x="year", y="count", color="Category",
            hover_data=['Category'], barmode = 'stack',
            labels={
                     "year": "Year",
                     "count": "Count",
                 },)
type_crimedf = crimedf.groupby(['year','text_general_code']).size().reset_index(name='count')
type_crimedf
#line_fig = px.line(type_crimedf, x="year", y="count", color='text_general_code')

line_fig = px.line(type_crimedf, x="year", y="count", color='text_general_code',
                   labels={
                     "year": "Year",
                     "count": "Count",
                     "text_general_code": 'General Codes'
                  },)
line_fig.show()


total_stats = crimedf.groupby(['year']).size().reset_index(name = 'count')
total_stats

totals_fig = px.bar(total_stats, x="year", y="count",
            hover_data=['count'],
            labels={
             "year": "Year",
             "count": "Count",
             },)
totals_fig.show()

six_months = datetime.now() - timedelta(days=180)
geo_data = crimedf[crimedf['dispatch_date'] >= six_months]

geo_data = geo_data[
    (geo_data['point_x'] >= -90) & (geo_data['point_x'] <= 90) &
    (geo_data['point_y'] >= -180) & (geo_data['point_y'] <= 180)
]
geo_data = geo_data[(geo_data['point_x'] != 0) & (geo_data['point_y'] != 0)]

geo_data = geo_data.dropna(subset=['point_x', 'point_y']) 
#geo_data = geo_data.groupby(['point_x','point_y']).size().reset_index(name = 'Count Per Block')
geo_data = geo_data.sort_values(by='dispatch_date')
geo_data

geo_data[['point_x', 'point_y']].describe()

geo_fig = px.scatter_map(geo_data,
                     lat='point_y',
                     lon='point_x',
                     hover_name='location_block',
                     zoom = 10,
                     color = 'text_general_code',
                     labels={
                     "text_general_code": "Crime Code",
                      },)  # Adjust size of points
geo_fig.update_layout('')
geo_fig.show()

print(os.listdir('assets'))

#homicide data cleaning
homicide_data = crimedf[crimedf['text_general_code'].str.contains('Homicide')]
homicide_data['dispatch_date'] = pd.to_datetime(homicide_data['dispatch_date'])
homicide_data['year'] = homicide_data['dispatch_date'].dt.year
homicide_data = homicide_data[['year','text_general_code']]

#homicide dataframe creation
homicide_data = homicide_data.groupby(['year']).size().reset_index(name='count')
homicide_data = homicide_data.rename(columns={'year':'Year',
                                               'count': 'Homicide Count'})
#homicide table creation and variable
homicide_fig = go.Figure(data=[go.Table(
    header=dict(
        values=homicide_data.columns.tolist(),
        fill_color="#2176d2",
        align="center",
        height=25,
        font_size=12,
        font_color="white",
        font_family='Montserrat',
    ),
    cells=dict(
        values=[homicide_data['Year'].tolist(), homicide_data['Homicide Count'].tolist()],
        fill_color='lavender',
        align='left',
    )
)])

homicide_fig.update_layout(
        width=800,
        height=800,
        autosize=False,
        margin=dict(l=20, r=20, t=20, b=20),
    )

homicide_fig.show()


# Create the Dash app using a Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(children=[
    dbc.Row(
    html.Div([
    html.Img(src='/assets/Logo.png', style={'height': '50px', 'float': 'left', 'margin-right': '20px', 'margin-bottom': '20px'})
    ])),
               
     # Header Section
    dbc.Row(
        dbc.Col(html.H1('Geographic Mapping of Crimes', className='text-center mb-4'), width=12)
    ),

    # Time period selection instruction
    html.Div("Select a time period to filter the crime data points displayed on the map.", className="text-center mb-4"),

    # Time range filter using dropdown buttons
    html.Div([
        html.Label('Select Time Period:'),
        dcc.Dropdown(
            id='time-period-dropdown',
            options=[
                {'label': 'Last 1 Week', 'value': '1_week'},
                {'label': 'Last 1 Month', 'value': '1_month'},
                {'label': 'Last 6 Months', 'value': '6_months'},
            ],
            value='6_months',  # Default value
            style={'width': '80%', 'margin': 'auto'},
        ),
    ], className="mb-4", style={'width': '80%', 'margin': 'auto'}),

    # Map display section
    dcc.Graph(id='crime-map'),
    # Header Section
    dbc.Row(
        dbc.Col(html.H1("Crime Stats By Type", className='text-center mb-4'), width=12)
    ),

    # Description Section
    dbc.Row(
        dbc.Col(html.P('Breakdown of crime types over time, categorized as Felonies or Misdemeanors, '
                       'general codes and total per year.', className='text-center mb-5'),
                width=12)
    ),
    # Total Graph (Occupying full width)
    dbc.Row(
        dbc.Col(
            dcc.Graph(
                id='total-graph',
                figure=totals_fig,
                style={'height': '500px'}
            ),
            width=12,
        ),
        className="mb-5"
    ),


    # Graphs Section (Category Graph and Type Graph side by side)
    dbc.Row(
        [
            dbc.Col(
                dcc.Graph(
                    id='category-graph',
                    figure=category_fig,
                    style={'height': '400px'}
                ),
                width=6,  # This will take half the screen width
            ),
            dbc.Col(
                dcc.Graph(
                    id='type-graph',
                    figure=line_fig,
                    style={'height': '400px'}
                ),
                width=6,  # This will take the other half of the screen width
            ),
        ],
        className="mb-5"
    ),

])

# Callback to update the map based on selected time period
@app.callback(
    Output('crime-map', 'figure'),
    [Input('time-period-dropdown', 'value')]
)
    
def update_map(selected_period):
    # Get the current date
    current_date = datetime.now()

    # Calculate the start date based on the selected period
    if selected_period == '1_week':
        start_date = current_date - timedelta(weeks=1)
    elif selected_period == '1_month':
        start_date = current_date - timedelta(days=30)  # Approximate one month
    elif selected_period == '6_months':
        start_date = current_date - timedelta(days=180)  # Approximate six months

    # Filter geo_data based on the calculated start date
    filtered_data = geo_data[geo_data['dispatch_date'] >= start_date]

    # Check if filtered data is empty
    if filtered_data.empty:
        return {
            'data': [],
            'layout': {
                'title': 'No data available for the selected period',
                'mapbox': {'style': "open-street-map"}
            }
        }

    # Create a new map figure with the filtered data
    geo_fig = px.scatter_mapbox(
        filtered_data,
        lat='point_y',
        lon='point_x',
        hover_name='location_block',
        zoom = 10,
        color = 'text_general_code',
        labels={
        "text_general_code": "Crime Code",
         },
    )
    
    # Set map style
    geo_fig.update_layout(mapbox_style="open-street-map")

    return geo_fig


if __name__ == '__main__':
    app.run(debug=True)


