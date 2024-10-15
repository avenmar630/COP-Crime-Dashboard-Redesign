#!/usr/bin/env python
# coding: utf-8

# In[30]:


import requests
iimport requests
import orjson
import plotly.express as px
from dash import Dash, html, dcc
import pandas as pd


# In[2]:


#GeoJSON link
crimedatalink = 'https://phl.carto.com/api/v2/sql?q=SELECT+*+FROM+incidents_part1_part2&filename=incidents_part1_part2&format=geojson&skipfields=cartodb_id'


# In[3]:


#establish response, normalize data into decodable json format
response = requests.get(crimedatalink)
data = orjson.loads(response.content)


# In[4]:


#convert to pandas dataframe
crimedf = pd.json_normalize([i['properties'] for i in data['features']])


# In[16]:


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


# In[18]:


#data manipulation for addition of broad categorization - Felony vs Misdemeanor
cat_crimedf = crimedf
cat_crimedf['dispatch_date'] = pd.to_datetime(cat_crimedf['dispatch_date'])
cat_crimedf['year'] = cat_crimedf['dispatch_date'].dt.year
cat_crimedf['Category'] = cat_crimedf['text_general_code'].map(offense_categories)
cat_crimedf


# In[27]:


cat_crimedf = cat_crimedf.groupby(['year','Category']).size().reset_index(name='count')
cat_crimedf


# In[28]:


category_fig = px.bar(tr, x="year", y="count", color="Category",
            hover_data=['Category'], barmode = 'stack')


# In[34]:


app = Dash(__name__)

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options

category_fig = category_fig

app.layout = html.Div(children=[
    html.H1(children='Stacked Bar Graph'),

    html.Div(children='''
        Breakdown of crime types overtime, categorized as Felonies or Misdemeanors.
    '''),

    dcc.Graph(
        id='category-graph',
        figure=category_fig
    )
])

if __name__ == '__main__':
    app.run(debug=True)

