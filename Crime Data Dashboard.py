#!/usr/bin/env python
#!/usr/bin/env python
# coding: utf-8

# In[30]:


import requests
import orjson
import plotly.express as px
from dash import Dash, html, dcc
import pandas as pd


# In[2]:


#GeoJSON link
current_year = datetime.now()
five_year = current_year - timedelta(days=5*365)
date_string = five_year.strftime("%Y-%m-%d")

print(date_string)

crimedatalink = f'https://phl.carto.com/api/v2/sql?q=SELECT+*+FROM+incidents_part1_part2 WHERE dispatch_date >= \'{date_string}\' &filename=incidents_part1_part2&format=geojson&skipfields=cartodb_id'
# In[3]:


#establish response, normalize data into decodable json format
response = requests.get(crimedatalink, verify = True)
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


cat_crimedf = crimedf.groupby(['year','Category']).size().reset_index(name='count')
cat_crimedf


# In[57]:


category_fig = px.bar(cat_crimedf, x="year", y="count", color="Category",
            hover_data=['Category'], barmode = 'stack',
            labels={
                     "year": "Year",
                     "count": "Count",
                 },
            title="Crimes By Category Over Time")


# In[36]:


type_crimedf = crimedf.groupby(['year','text_general_code']).size().reset_index(name='count')
type_crimedf
#line_fig = px.line(type_crimedf, x="year", y="count", color='text_general_code')


# In[59]:


line_fig = px.line(type_crimedf, x="year", y="count", color='text_general_code',
                   labels={
                     "year": "Year",
                     "count": "Count",
                     "text_general_code": 'General Codes'
                  },
                  title="Crimes By General Type Overtime")
line_fig.show()


# In[47]:


total_stats = crimedf.groupby(['year']).size().reset_index(name = 'count')
total_stats


# In[60]:


totals_fig = px.bar(total_stats, x="year", y="count",
            hover_data=['count'],
            title="Total Crimes Per Year",
                    labels={
                     "year": "Year",
                     "count": "Count",
                     },)
totals_fig.show()


# In[75]:


app = Dash(__name__)

app.layout = html.Div(children=[
    html.H1(children='Crime Stats By Type'),

    html.Div(children='''
        Breakdown of crime types overtime, categorized as Felonies or Misdemeanors, general codes and total per year.
    '''),
    dcc.Graph(
        id='category-graph',
        figure=category_fig,
        style={'display': 'inline-block','width': 'auto'}
    ),
    dcc.Graph(
        id = 'type-graph',
        figure = line_fig,
        style={'display': 'inline-block', 'width': 'auto'}
    ),
    dcc.Graph(
        id = 'total-graph',
        figure = totals_fig,
    ),
])

if __name__ == '__main__':
    app.run(debug=True)

