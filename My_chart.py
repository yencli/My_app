import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import wget
import geopandas as gpd
from shapely import wkt
from bokeh.io import output_notebook, show, output_file
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, ColumnDataSource, Grid, LinearAxis, Patches, Plot
import json
from bokeh.models import HoverTool
import streamlit as st
import altair as alt


site_url = 'https://raw.githubusercontent.com/maelfabien/COVID-19-Senegal/master/COVID_Senegal.csv'
file_name = wget.download(site_url)
covid_df= pd.read_csv(file_name,sep= ';',na_values="?")
covid_df = covid_df.astype({'Age': 'Int64', 'Homme': 'Int64', 'Femme': 'Int64', 'Décédé': 'Int64', 'Guéri': 'Int64','Temps Hospitalisation (j)': 'Int64'})
covid_df = covid_df.astype({'Positif': 'boolean','Negatif': 'boolean','Age': 'boolean', 'Homme': 'boolean', 'Femme': 'boolean', 'Décédé': 'boolean', 'Guéri': 'boolean','Temps Hospitalisation (j)': 'Int64'})
covid_df['Date'] = pd.to_datetime(covid_df['Date'], errors='coerce')
lat_df = pd.read_csv('input/city_coordinates.csv',sep= ',',na_values="?")
lat_df = lat_df.drop(lat_df.columns[[0]],axis = 1)

st.title("COVID Data Visualization in Senegal")
#Chart Senegal
brush = alt.selection(type='interval')

activ_df=covid_df.groupby('Date')[['Date','Positif','Guéri']].sum().cumsum().reset_index()
activ_df['Active'] = activ_df['Positif']-activ_df['Guéri']

chart1 = alt.Chart(activ_df).transform_fold(
    ['Positif', 'Active'],
).mark_line().encode(
    x='Date:T',
    y='value:Q',
    color='key:N'
)

fact_df = covid_df.pivot_table(values='Positif',index='Date',columns='Facteur',aggfunc='count').reset_index()
fact_df[['Communauté','Contact','Importé']]= fact_df[['Communauté','Contact','Importé']].apply(np.nancumsum)

chart2 = alt.Chart(fact_df).transform_fold(
    ['Communauté', 'Contact','Importé'],
).mark_line().encode(
    x='Date:T',
    y='value:Q',
    color='key:N'
)

st.altair_chart(chart1 & chart2)


# Map Senegal
city_df = covid_df[covid_df.Positif == True]
city_df = covid_df.groupby('Ville')[['Ville','Positif']].sum().reset_index()
df_cl = pd.merge(city_df, lat_df, how='left', on = 'Ville')
shapefile = 'input/ne_110m_admin_0_countries.shp'
gdf = gpd.read_file(shapefile)[['ADMIN', 'ADM0_A3', 'geometry']]
gdf.columns = ['country', 'country_code', 'geometry']
gdf = gdf[gdf['country'] == "Senegal" ]
grid_crs=gdf.crs
gdf_json = json.loads(gdf.to_json())
grid = json.dumps(gdf_json)
geosource = GeoJSONDataSource(geojson = grid)

# Create figure object.
p = figure(title = 'COVID case per City in Senegal',
           plot_height = 600 ,
           plot_width = 950,
           toolbar_location = 'below',
           tools = "pan, wheel_zoom, box_zoom, reset")
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None
p.xaxis.visible = False
p.yaxis.visible = False
p.outline_line_color = None
# Add patch renderer to figure.
states = p.patches('xs','ys', source = geosource,
                   fill_color = None,
                   line_color = 'gray',
                   line_width = 1,
                   fill_alpha = 1)

communes = ColumnDataSource(data=dict(xc=df_cl.Longitude, yc=df_cl.Latitude,
                                      ville=df_cl['Ville'],
                                      positif=df_cl['Positif'],
                                      size = df_cl['Positif']+10 ))

ville = p.scatter(x="xc", y="yc", fill_color="blue", line_color="blue", size="size",source=communes)
# Create hover tool
p.add_tools(HoverTool(renderers = [ville],
                      tooltips = [('City','@ville'),
                                ('Case','@positif')]))
st.bokeh_chart(p)
