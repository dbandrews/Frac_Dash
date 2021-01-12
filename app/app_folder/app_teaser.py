import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import base64
import io
import os
import json
from dash.dependencies import Input, Output, State
from .server import app

location = "app_folder"
cwd = os.getcwd()

df_total = pd.read_csv(os.path.join(cwd, location, "df_total.csv"), index_col=0)
df = pd.read_csv(os.path.join(cwd, location, "df_by_well.csv"), index_col=0)


# Get Confidential Well List Live! If not available, trigger to use last 15 just by date
try:
    data = pd.read_fwf(
        "https://www.aer.ca/data/conwell/ConWell.txt",
        colspecs=[(0, 19), (21, 30), (31, 66), (67, 84), (86, 103), (105, 123)],
        header=7,
    )
    data = data.drop(data.index[0])

    data_conf = data.loc[data["Conf. Release Date"] != "no date avail", :]
    data_conf.loc[:, "Well Location"] = data_conf.loc[:, "Well Location"].astype("str")
    data_conf.loc[:, "Well Location"] = data_conf.loc[:, "Well Location"].str.replace(
        "w", "W"
    )
    conf_well_list = data_conf["Well Location"].values  # Stores UWI's......
    conf_list_down = False
except:
    conf_list_down = True
    df.sort_values(by="Last Fracture Date", inplace=True, ascending=False)
    conf_well_list = df["UWI"].head(15)

# Top 10 on well count of all fracs...
counts = df["Licensee"].value_counts()

# #Filter Df's down to interesting wells....
df = df.loc[df["UWI"].isin(conf_well_list), :]  # only confidential wells!
df_total = df_total.loc[df_total["UWI"].isin(conf_well_list), :]

# Get 20 last Confidential Fracs for consistency of design of teaser page
df.sort_values(by="Last Fracture Date", inplace=True, ascending=False)
last_15 = df["UWI"].head(15)

df = df.loc[df["UWI"].isin(last_15), :]
df_total = df_total.loc[df_total["UWI"].isin(last_15), :]

# Columns for lower tables
cols_displayed_well = [
    "Well Licence Number",
    "Licensee",
    "UWI",
    "Number of Stages",
    "Production Fluid Type",
    "Start Date",
    "End Date",
    "Total Water Volume",
    "Total Proppant %",
    "Total Frac Mass",
    "Total Proppant (tonnes)/Stage",
]

cols_displayed_comp = [
    "Component Type",
    "Component Trade Name",
    "Component Supplier Name",
    "Additive Purpose",
    "Ingredient Name",
    "CAS # HMIRC #",
    "Concentration Component",
    "Concentration HFF",
]

# if confidential well list not available, return 15 most recent instead
if conf_list_down == True:
    title_text = "Last 15 Fracs in Alberta"
else:
    title_text = "Last 15 Confidential Fracs in Alberta"


layout = html.Div(
    [
        html.Div(  # FIRST ROW
            [
                html.H2(
                    children=title_text,
                    # className='four columns'
                )
            ],
            className="row",
            style={
                #                 'background':'rgba(0,0,220,100)',
                #'color':'rgba(0,0,220,100)'
            },
        ),
        html.Div(
            [  # SECOND ROW
                html.Div(
                    [
                        dt.DataTable(
                            id="summary_table",
                            columns=[
                                {"name": i, "id": i}
                                for i in [
                                    "UWI",
                                    "Well Licence Number",
                                    "Licensee",
                                    "Number of Stages",
                                    "End Date",
                                    "Total Proppant (tonnes)/Stage",
                                ]
                            ],
                            data=df.loc[
                                :,
                                [
                                    "UWI",
                                    "Well Licence Number",
                                    "Licensee",
                                    "Number of Stages",
                                    "End Date",
                                    "Total Proppant (tonnes)/Stage",
                                ],
                            ]
                            .sort_values(by="End Date", ascending=False)
                            .to_dict("records"),  # initialise the rows
                            row_selectable="single",
                            selected_rows=[],
                            # sorting_type="single",
                            derived_virtual_data=df.to_dict("records"),
                            # style_table={'overflowX': 'scroll'},
                            style_header={"fontWeight": "bold"},
                            style_cell={"textAlign": "left", "fontFamily": "Arial"},
                        )
                    ],
                    className="seven columns",
                ),
                html.Div(),  # NOT SURE WHY BUT THIS DIV MAKES HIGHLIGHT PROPPANT WELLS CALLBACK ON OTHER TAB WORK!!!
                html.Div(
                    [
                        dcc.Graph(
                            id="teaser_graph_with_slider",
                            config={
                                "editable": True,
                                "modeBarButtonsToRemove": ["sendDataToCloud"],
                            },
                        )
                    ],
                    className="five columns",
                ),  # No edit in cloud!
            ],
            className="row",
        ),
        html.Div(
            [  # THIRD ROW
                html.H2(children="Selected Well Data From Map"),
                dt.DataTable(
                    data=[{}],  # initialise the rows
                    columns=[{"name": i, "id": i} for i in cols_displayed_well],
                    editable=False,
                    derived_virtual_data=[{}],
                    # style_table={'overflowX': 'scroll'},
                    style_header={"fontWeight": "bold"},
                    style_cell={"textAlign": "left", "fontFamily": "Arial"},
                    # selected_row_indices=[],
                    id="teaser_selected_well",
                ),
                html.Div([html.Hr()], style={"margin": {"t": 10, "b": 10}}),
                dt.DataTable(
                    data=[{}],
                    columns=[{"name": i, "id": i} for i in cols_displayed_comp],
                    editable=False,
                    derived_virtual_data=[{}],
                    # style_table={'overflowX': 'scroll'},
                    style_header={"fontWeight": "bold"},
                    style_cell={"textAlign": "left", "fontFamily": "Arial"},
                    # selected_row_indices=[],
                    id="teaser_selected_well_comp",
                ),
            ],
            className="row",
        ),
    ],
    className="row",
)


# @app.callback(
#     Output('datatable-interactivity-container', "children"),
#     [Input('summary_table', "derived_virtual_data"),
#      Input('summary_table', "derived_virtual_selected_rows")])
# def update_graph(rows, derived_virtual_selected_rows):
#     return html.Div(children=[])


# Selectors to Map
@app.callback(
    Output("teaser_graph_with_slider", "figure"),
    [
        Input("summary_table", "derived_virtual_data"),
        Input("summary_table", "derived_virtual_selected_rows"),
    ],
)
def update_teaser_figure(rows_total, selected_row_indices):

    # If no rows selected, just work with original data frame. otherwise, indices of selected rows returned with respect to derived_virtual_data (i.e index of rows)
    # if selected_row_indices is None:
    #     filtered_df = df.copy()
    # else:
    #     filtered_df = pd.DataFrame(rows_total)
    filtered_df = df
    table_df = pd.DataFrame(
        rows_total
    )  # Will use this for indexing selected rows into...

    traces = []

    # ***********************************INITIAL DATA**************************************************************
    for i in filtered_df["Licensee"].unique():
        df_by_licensee = filtered_df[filtered_df["Licensee"] == i]
        traces.append(
            go.Scattergeo(
                # locationmode='CANADA',
                lon=df_by_licensee["Bottom Hole Longitude"],
                lat=df_by_licensee["Bottom Hole Latitude"],
                text=df_by_licensee["UWI"] + ":" + df_by_licensee["Licensee"],
                customdata=df_by_licensee["UWI"],
                mode="markers",
                hoverinfo="text",
                opacity=0.5,
                marker={"size": 10, "line": {"width": 0.5, "color": "white"}},
                name=i,
            )
        )
    # ***********************************SELECTED WELLS FROM TABLE DATA***********************************************************
    highlight_UWI_table = []
    if selected_row_indices != None:
        highlight_UWI_table = table_df["UWI"][selected_row_indices].tolist()

        traces.append(
            go.Scattergeo(
                # locationmode='CANADA',
                lon=filtered_df["Bottom Hole Longitude"][
                    filtered_df["UWI"].isin(highlight_UWI_table)
                ],
                lat=filtered_df["Bottom Hole Latitude"][
                    filtered_df["UWI"].isin(highlight_UWI_table)
                ],
                text=filtered_df["UWI"][filtered_df["UWI"].isin(highlight_UWI_table)]
                + ":"
                + "Well selected",
                customdata=filtered_df["UWI"][
                    filtered_df["UWI"].isin(highlight_UWI_table)
                ],
                mode="markers",
                hoverinfo="text",
                marker={
                    "color": "rgba(0,0,0,0)",
                    "size": 11,
                    "line": {"width": 1.5, "color": "rgba(255,0,0,1)"},
                },
                name="Selected Well",
            )
        )

    return {
        "data": traces,
        "layout": {
            "paper_bgcolor": "#FFFFFF",
            "title": "",
            "autosize": False,
            "showlegend": True,
            "legend": {
                "x": 0.2,
                "y": -0.01,
                "xanchor": "left",
                "yanchor": "top",
                "bgcolor": "#E2E2E2",
                "bordercolor": "#FFFFFF",
                "orientation": "h",
            },
            "height": "100%",
            "font": {"size": 10},
            "geo": {
                "scope": "north america",
                "projection": {"type": "natural earth"},
                "resolution": 50,
                "lonaxis": {"range": [-122, -109], "showgrid": True},
                "lataxis": {"range": [49, 62], "showgrid": True},
                "showland": "true",
                "landcolor": "#EAEAAE",
                "countrycolor": "#d3d3d3",
                "countrywidth": 1.5,
            },
            "margin": {"l": 0, "r": 0, "b": 0, "t": 0},
        },
    }


@app.callback(
    Output("teaser_selected_well_comp", "data"),
    [
        Input("summary_table", "derived_virtual_data"),
        Input("summary_table", "derived_virtual_selected_rows"),
    ],
)
def teaser_update_selected_well_components(rows_total, selected_row_indices):
    table_df = pd.DataFrame(rows_total)
    if selected_row_indices != None:
        highlight_UWI_table = table_df["UWI"][selected_row_indices].tolist()
        return_df = df_total.loc[
            df_total["UWI"].isin(highlight_UWI_table), cols_displayed_comp
        ]

        return return_df.to_dict("records")
    else:
        return [{}]


# # #Callback to populate well table with selected well
@app.callback(
    Output("teaser_selected_well", "data"),
    [
        Input("summary_table", "derived_virtual_data"),
        Input("summary_table", "derived_virtual_selected_rows"),
    ],
)
def teaser_update_selected_well_table(rows_total, selected_row_indices):
    table_df = pd.DataFrame(rows_total)
    if selected_row_indices != None:
        highlight_UWI_table = table_df["UWI"][selected_row_indices].tolist()
        return_df = df.loc[df["UWI"].isin(highlight_UWI_table), cols_displayed_well]

        return return_df.to_dict("records")
    return [{}]