import requests
import orjson
import plotly.express as px
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
import pandas as pd
from datetime import datetime, timedelta


# In[11]:


#GeoJSON link
current_year = datetime.now()
five_year = current_year - timedelta(days=5*365)
date_string = five_year.strftime("%Y-%m-%d")

crimedatalink = f'https://phl.carto.com/api/v2/sql?q=SELECT+*+FROM+incidents_part1_part2 WHERE dispatch_date >= \'{date_string}\' &filename=incidents_part1_part2&format=geojson&skipfields=cartodb_id'


# In[12]:


#establish response, normalize data into decodable json format
response = requests.get(crimedatalink, verify = True)
data = orjson.loads(response.content)


# In[13]:


#convert to pandas dataframe
crimedf = pd.json_normalize([i['properties'] for i in data['features']])


# In[15]:


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


# In[16]:


#data manipulation for addition of broad categorization - Felony vs Misdemeanor
cat_crimedf = crimedf
cat_crimedf['dispatch_date'] = pd.to_datetime(cat_crimedf['dispatch_date'])
cat_crimedf['year'] = cat_crimedf['dispatch_date'].dt.year
cat_crimedf['Category'] = cat_crimedf['text_general_code'].map(offense_categories)
cat_crimedf


# In[17]:


cat_crimedf = crimedf.groupby(['year','Category']).size().reset_index(name='count')
cat_crimedf


# In[18]:


category_fig = px.bar(cat_crimedf, x="year", y="count", color="Category",
            hover_data=['Category'], barmode = 'stack',
            labels={
                     "year": "Year",
                     "count": "Count",
                 },
            title="Crimes By Category Over Time")


# In[19]:


type_crimedf = crimedf.groupby(['year','text_general_code']).size().reset_index(name='count')
type_crimedf
#line_fig = px.line(type_crimedf, x="year", y="count", color='text_general_code')


# In[20]:


line_fig = px.line(type_crimedf, x="year", y="count", color='text_general_code',
                   labels={
                     "year": "Year",
                     "count": "Count",
                     "text_general_code": 'General Codes'
                  },
                  title="Crimes By General Type Overtime")
line_fig.show()


# In[76]:


total_stats = crimedf.groupby(['year']).size().reset_index(name = 'count')
total_stats


# In[77]:


totals_fig = px.bar(total_stats, x="year", y="count",
            hover_data=['count'],
            title="Total Crimes Per Year",
                    labels={
                     "year": "Year",
                     "count": "Count",
                     },)
totals_fig.show()


# In[63]:


past_month = datetime.now() - pd.DateOffset(months=1)
geo_data = crimedf[crimedf['dispatch_date'] >= past_month]

geo_data = geo_data[
    (geo_data['point_x'] >= -90) & (geo_data['point_x'] <= 90) &
    (geo_data['point_y'] >= -180) & (geo_data['point_y'] <= 180)
]
geo_data = geo_data[(geo_data['point_x'] != 0) & (geo_data['point_y'] != 0)]

geo_data = geo_data.dropna(subset=['point_x', 'point_y']) 
#geo_data = geo_data.groupby(['point_x','point_y']).size().reset_index(name = 'Count Per Block')
geo_data


# In[64]:


geo_data[['point_x', 'point_y']].describe()


# In[82]:


geo_fig = px.scatter_map(geo_data,
                     lat='point_y',
                     lon='point_x',
                     hover_name='location_block',
                     zoom = 10,
                     color = 'text_general_code',# Display the address on hover
                     title="Mapping of Crime")  # Adjust size of points

geo_fig.show()


# In[85]:


# Create the Dash app using a Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(children=[
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

    # Geographic Mapping Section
    dbc.Row(
        dbc.Col(html.H1('Geographic Mapping of Crimes', className='text-center mb-4'), width=12)
    ),

    dbc.Row(
        dbc.Col(html.P('Geographic mapping of crimes by location block.', className='text-center mb-4'), width=12)
    ),

    # Optional: Add a map or any other graph component below
    dbc.Row(
        dbc.Col(
            dcc.Graph(
                id='location-graph',  # Replace with your map figure
                figure=geo_fig,  # Add the geographic map figure here
                style={'height': '500px'}
            ),
            width=12,
        ),
        className="mb-5"
    ),
])

if __name__ == '__main__':
    app.run(debug=True)

