import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import datetime
import base64
import io
import copy
import json
import os
from dash.dependencies import Input, Output, State
from .server import app

location = "app_folder"
cwd = os.getcwd()

df_total = pd.read_parquet(os.path.join(cwd, location, "df_total.parquet.gzip"))
df = pd.read_parquet(os.path.join(cwd, location, "df_by_well.parquet.gzip"))

# Get Confidential Well List Live! If not available, trigger to use last 15 just by date
try:
    data = pd.read_fwf(
        "https://www.aer.ca/data/conwell/ConWell.txt",
        colspecs=[(0, 19), (21, 30), (31, 66), (67, 84), (86, 103), (105, 123)],
        header=17,
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

# get shape files traces data:
with open(os.path.join(cwd, location, "shape_traces_storage.json")) as in_file:
    shape_traces = json.load(in_file)
    shape_traces["None"] = {"None": "None"}

# Columns to display in tables
cols_displayed_well = [
    "Well Licence Number",
    "Licensee",
    "UWI",
    "Number of Stages",
    "Production Fluid Type",
    "Terminating Formation",
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


# dummy point for map so there is at least one point plotted. If no data on map - the box selection tool disappears
dummy = go.Scattergeo(
    lon=[-130],
    lat=[60],
    mode="markers",
    hoverinfo="none",
    opacity=0.5,
    marker={"size": 1, "line": {"width": 0.5, "color": "white"}},
    name="",
    showlegend=False,
)
# define initial layout for map
initial_layout = {
    "autosize": True,
    "bordercolor": "#00000",
    "paper_bgcolor": "#FFFFFF",
    "legend": {
        "x": 0.2,
        "y": -0.01,
        "xanchor": "left",
        "yanchor": "top",
        "bgcolor": "#E2E2E2",
        "bordercolor": "#FFFFFF",
        "orientation": "h",
    },
    "font": {"size": 10},
    "geo": {
        "scope": "north america",
        "projection": {"type": "natural earth"},
        "resolution": 50,
        "lonaxis": {"range": [-126, -105]},
        "lataxis": {"range": [48, 61]},
        "showland": "true",
        "landcolor": "#EAEAAE",
        "countrycolor": "#d3d3d3",
        "countrywidth": 1.5,
    },
    "margin": {"l": 0, "r": 0, "b": 0, "t": 0},
}


def filter_df_operator_year_fm(df, selected_year, selected_operator, formation_list):
    filtered_df = df
    filtered_df = filtered_df[
        (filtered_df["year"] >= np.min(selected_year))
        & (filtered_df["year"] <= np.max(selected_year))
    ]  # year range
    filtered_df = filtered_df[filtered_df["Licensee"].isin(selected_operator)]
    filtered_df = filtered_df[filtered_df["Terminating Formation"].isin(formation_list)]
    return filtered_df


# Function to call with all the selectors as input
def filter_df(
    df_in,
    selected_year,
    selected_operator,
    selected_area,
    selection_mode,
    file_content,
    file_name,
    recency,
    conf_switch,
    formation_list,
):
    filtered_df = df

    if selection_mode == "file":  # if a file is uploaded...
        if (
            file_content == None
        ):  # if no file actually in upload box, return normal operator year selections
            # filter to operators year formation
            filtered_df = filter_df_operator_year_fm(
                filtered_df, selected_year, selected_operator, formation_list
            )
        else:
            upload_uwi = parse_contents(file_content, file_name)
            if filtered_df.size != 0:
                filtered_df = filtered_df[
                    filtered_df["UWI"].isin(upload_uwi.iloc[:, 0].values)
                ]
            elif (
                filtered_df.size == 0
            ):  # No proper wells could be selected, return normal operator year selections
                # filter to operators year formation
                filtered_df = filter_df_operator_year_fm(
                    filtered_df, selected_year, selected_operator, formation_list
                )
    elif (
        selection_mode == "operator_year"
    ):  # Strip data frame down to just selected operators and years
        if len(conf_switch) != 0:
            filtered_df = filtered_df[filtered_df["UWI"].isin(conf_well_list)]

        # filter to operators year formation
        filtered_df = filter_df_operator_year_fm(
            filtered_df, selected_year, selected_operator, formation_list
        )

    elif selection_mode == "recent":
        if len(conf_switch) != 0:
            filtered_df = filtered_df[filtered_df["UWI"].isin(conf_well_list)]

        if recency == "2_week":
            filtered_df = filtered_df[
                (
                    pd.to_datetime(filtered_df["Last Fracture Date"].values).date
                    > (datetime.date.today() - pd.to_timedelta(14, unit="d"))
                )
            ]
        elif recency == "4_week":
            filtered_df = filtered_df[
                (
                    pd.to_datetime(filtered_df["Last Fracture Date"].values).date
                    > (datetime.date.today() - pd.to_timedelta(30, unit="d"))
                )
            ]
        elif recency == "3_month":
            filtered_df = filtered_df[
                (
                    pd.to_datetime(filtered_df["Last Fracture Date"].values).date
                    > (datetime.date.today() - pd.to_timedelta(90, unit="d"))
                )
            ]
        elif recency == "6_month":
            filtered_df = filtered_df[
                (
                    pd.to_datetime(filtered_df["Last Fracture Date"].values).date
                    > (datetime.date.today() - pd.to_timedelta(180, unit="d"))
                )
            ]
    elif (
        selection_mode == "map"
    ):  # check lats and longs passed from selected data values. Strip down to wells within that area, irrespective of year and operator.
        if len(conf_switch) != 0:
            filtered_df = filtered_df[filtered_df["UWI"].isin(conf_well_list)]

        if selected_area != None:
            if "range" in selected_area.keys():
                filtered_df = filtered_df[
                    (  # Note - selectedData box goes from top left to bottom right for point 0, point 1. Negative Longitude!
                        (
                            filtered_df["Bottom Hole Latitude"]
                            >= selected_area["range"]["geo"][1][1]
                        )
                        & (
                            filtered_df["Bottom Hole Latitude"]
                            <= selected_area["range"]["geo"][0][1]
                        )
                        & (
                            filtered_df["Bottom Hole Longitude"]
                            <= selected_area["range"]["geo"][1][0]
                        )
                        & (
                            filtered_df["Bottom Hole Longitude"]
                            >= selected_area["range"]["geo"][0][0]
                        )
                    )
                ]
        else:
            # filter to operators year formation
            filtered_df = filter_df_operator_year_fm(
                filtered_df, selected_year, selected_operator, formation_list
            )
            # check if any wells returned

    return filtered_df


# Function to parse uploaded files to UWI dataframe
def parse_contents(contents, filename):
    blank_df = pd.DataFrame(data=None, columns=None)
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV file
            df_upload = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        # elif 'xls' in filename or 'xlsx' in filename:
        #     # Assume that the user uploaded an excel file
        #     df_upload = pd.read_excel(io.StringIO(decoded), usecols=1)
        if df_upload.size == 0:
            return blank_df
        else:
            return df_upload
    except:
        return blank_df


# ********************************************************page layout *************************************************************************
layout = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [  # Selection Mode
                                                html.Label("Selection Mode:"),
                                                dcc.RadioItems(
                                                    id="selection_mode",
                                                    options=[
                                                        {
                                                            "label": "By Operator,Year,Formation",
                                                            "value": "operator_year",
                                                        },
                                                        {
                                                            "label": "Select From Map",
                                                            "value": "map",
                                                        },
                                                        {
                                                            "label": "UWI List Upload",
                                                            "value": "file",
                                                        },
                                                        {
                                                            "label": "Recency",
                                                            "value": "recent",
                                                        },
                                                    ],
                                                    value="operator_year",
                                                    labelStyle={
                                                        "display": "inline-block",
                                                        "margin": "3px",
                                                    },
                                                ),
                                            ],
                                            className="six columns",
                                            style={
                                                "marginTop": "5px",
                                                "marginBottom": "15px",
                                            },
                                        ),
                                        html.Div(
                                            id="recency_div",
                                            children=[  # Recency Mode
                                                html.Label("Recency:"),
                                                dcc.Dropdown(
                                                    id="recent_drop",
                                                    options=[
                                                        {
                                                            "label": "Last 2 Weeks",
                                                            "value": "2_week",
                                                        },
                                                        {
                                                            "label": "Last 4 Weeks",
                                                            "value": "4_week",
                                                        },
                                                        {
                                                            "label": "Last 3 Months",
                                                            "value": "3_month",
                                                        },
                                                        {
                                                            "label": "Last 6 Months",
                                                            "value": "6_month",
                                                        },
                                                    ],
                                                    value="2_week",
                                                ),
                                            ],
                                            className="six columns",
                                            style={
                                                "visibility": "hidden",
                                                "marginBottom": 15,
                                            },
                                        ),
                                    ],
                                    className="row",
                                ),
                                html.Div(
                                    [  # Div to contain the year slider and component selector, set width = 100% to ensure wraps without needing a row
                                        html.Div(
                                            [
                                                html.Label("Select Date Range"),
                                                html.Div(
                                                    [
                                                        dcc.RangeSlider(
                                                            id="year-slider",
                                                            min=df["year"].min(),
                                                            max=df["year"].max(),
                                                            value=[
                                                                df["year"].max() - 1,
                                                                df["year"].max(),
                                                            ],
                                                            step=None,
                                                            marks={
                                                                str(year): str(year)
                                                                for year in df[
                                                                    "year"
                                                                ].unique()
                                                            },
                                                        ),
                                                    ],
                                                    style={
                                                        "height": "50px",
                                                        "margin": "10px",
                                                    },
                                                ),
                                            ],
                                            className="six columns",
                                        ),
                                        html.Div(
                                            [
                                                html.Label(
                                                    [
                                                        "Select Component Desired",
                                                        dcc.Dropdown(
                                                            id="component_dropdown",
                                                            multi=True,
                                                            value=["Select"],
                                                        ),
                                                    ]
                                                ),
                                            ],
                                            className="six columns",
                                        ),
                                    ],
                                    className="row",
                                ),
                                html.Div(
                                    [
                                        html.Label(
                                            [
                                                "Select Operators Desired",
                                                dcc.Dropdown(
                                                    id="operator_dropdown",
                                                    options=[
                                                        {"label": i, "value": i}
                                                        for i in df["Licensee"]
                                                        .dropna()
                                                        .sort_values()
                                                        .unique()
                                                    ],
                                                    multi=True,
                                                    value=["Tourmaline Oil Corp."],
                                                ),
                                            ]
                                        ),
                                        html.Label(
                                            [
                                                "Select Formations Desired",
                                                dcc.Dropdown(
                                                    id="formation_dropdown",
                                                    options=[
                                                        {"label": i, "value": i}
                                                        for i in df[
                                                            "Terminating Formation"
                                                        ]
                                                        .dropna()
                                                        .sort_values()
                                                        .unique()
                                                    ],
                                                    multi=True,
                                                    value=["SPIRIT RIVER FM"],
                                                ),
                                            ]
                                        ),
                                        html.Div(
                                            id="upload_data_div",
                                            children=[
                                                dcc.Upload(
                                                    id="upload_data",
                                                    children=html.Div(
                                                        [
                                                            "Drag and Drop UWI (XX/XX-XX-XXX-XXWX/X) List or ",
                                                            html.A(
                                                                "Select UWI List (.csv)"
                                                            ),
                                                        ]
                                                    ),
                                                    style={
                                                        "height": "60px",
                                                        "lineHeight": "60px",
                                                        "borderWidth": "1px",
                                                        "borderStyle": "dashed",
                                                        "borderRadius": "10px",
                                                        "textAlign": "center",
                                                        "margin": "10px",
                                                    },
                                                    # Allow multiple files to be uploaded
                                                    multiple=False,
                                                )
                                            ],
                                            style={"display": "none"},
                                        ),
                                        dcc.Checklist(
                                            id="conf_switch",
                                            options=[
                                                {
                                                    "label": "Confidential Wells Only?",
                                                    "value": "1",
                                                }
                                            ],
                                            value=[],
                                            labelStyle={"display": "inline-block"},
                                            style={
                                                "marginTop": "15px",
                                                "marginBottom": "15px",
                                            },
                                        ),
                                        # html.Pre(id='test_box'),
                                        html.Div(
                                            id="error_box",
                                            children=[""],
                                            style={
                                                "font-size": "15px",
                                                "font-color": "grey",
                                            },
                                        ),
                                    ],
                                    style={"margin": "0px"},
                                ),
                            ],
                            style={
                                "backgroundColor": "#FFFFFF",
                                "marginTop": 20,
                                "paddingLeft": 10,
                                "paddingRight": 30,
                                "paddingBottom": 30,
                                "borderRadius": "6px",
                            },
                        )
                    ],
                    className="six columns",
                ),
                html.Div(
                    id="graph-div",
                    children=[  # Other Div for 6 columns to hold map!
                        html.Div(
                            id="graph-container",
                            children=[
                                html.Div(
                                    children=[
                                        html.Div(
                                            id="color_by_div",
                                            children=[  # drop down box to control how points are colored
                                                html.Label("Color Points By:"),
                                                dcc.Dropdown(
                                                    id="color_by",
                                                    options=[
                                                        {
                                                            "label": "Licensee",
                                                            "value": "Licensee",
                                                        },
                                                        {
                                                            "label": "Fracture Date: Year & Month",
                                                            "value": "year_month",
                                                        },
                                                        {
                                                            "label": "Formation",
                                                            "value": "Terminating Formation",
                                                        },
                                                    ],
                                                    multi=False,
                                                    value="Licensee",
                                                ),
                                            ],
                                            className="six columns",
                                            style={"marginBottom": 5},
                                        ),
                                        html.Div(
                                            children=[
                                                html.Label("Background Geometry:"),
                                                dcc.Dropdown(
                                                    id="shape_drawn",
                                                    options=[
                                                        {"label": key, "value": key}
                                                        for key in shape_traces.keys()
                                                    ],
                                                    multi=False,
                                                    value="None",
                                                ),
                                            ],
                                            className="six columns",
                                            style={"marginBottom": 5},
                                        ),
                                    ],
                                    className="row",
                                ),
                                dcc.Graph(
                                    id="graph-with-slider",
                                    figure={"data": [dummy], "layout": initial_layout},
                                    config={
                                        "editable": False,
                                        "modeBarButtonsToRemove": ["sendDataToCloud"],
                                    },
                                ),  # style={'display': 'none'}
                            ],
                            style={
                                "marginTop": 10,
                                "marginRight": 0,
                                "marginLeft": 0,
                                "marginBottom": 20,
                                "borderRadius": "6px",
                            },
                        )
                    ],
                    className="six columns",
                ),  # Setting equal to hidden at first allows no error when loadingNo edit in cloud!
            ],
            className="row",  # , style={'height':'100%'}
        ),
        html.Div(
            [  # Second row of figures
                html.Div(
                    [  # half page graphs again require a Div each
                        dcc.Graph(
                            id="stages",
                            figure={"data": []},
                            config={
                                "editable": False,
                                "modeBarButtonsToRemove": [
                                    "sendDataToCloud",
                                    "pan2d",
                                    "lasso2d",
                                    "resetScale2d",
                                    "hoverCompareCartesian",
                                    "toggleSpikelines",
                                ],
                            },
                        )  # No edit in cloud!
                    ],
                    className="six columns",
                ),
                html.Div(
                    [
                        dcc.Graph(
                            id="tons_proppant_stage",
                            figure={"data": []},
                            config={
                                "editable": False,
                                "modeBarButtonsToRemove": [
                                    "sendDataToCloud",
                                    "pan2d",
                                    "lasso2d",
                                    "resetScale2d",
                                    "hoverCompareCartesian",
                                    "toggleSpikelines",
                                ],
                            },
                        )  # No edit in cloud!
                    ],
                    className="six columns",
                ),
            ],
            className="row",
        ),
        html.Div(
            [
                html.H2(children="Selected Well Data From Map"),
                dt.DataTable(
                    id="selected_well",
                    columns=[{"name": i, "id": i} for i in cols_displayed_well],
                    data=[{}],  # initialise the rows
                    # sorting_type="single",
                    # style_table={'overflowX': 'scroll'},
                    style_header={"fontWeight": "bold"},
                    style_cell={"textAlign": "left", "fontFamily": "Arial"},
                ),
                html.Div([html.Hr()], style={"margin": {"t": 10, "b": 10}}),
                dt.DataTable(
                    id="selected_well_comp",
                    columns=[{"name": i, "id": i} for i in cols_displayed_comp],
                    data=[{}],  # initialise the rows
                    style_header={"fontWeight": "bold"},
                    style_cell={"textAlign": "left", "fontFamily": "Arial"},
                ),
            ],
            className="row",
        ),
    ],
    className="row",
)


# # On Zoom or Pan of Map, check zoom level, if zoomed in toggle box to draw grid
# @app.callback(Output('test_box', 'children'),[Input('conf_switch', 'values')])
# def test_box(layout_data):
#     return layout_data

# Callback for Recency dropdown visiblity
@app.callback(Output("recency_div", "style"), [Input("selection_mode", "value")])
def make_visible_recency(selection):
    if selection == "recent":
        return {"visibility": "visible"}
    else:
        return {"visibility": "hidden"}


# Callback for Upload button visiblity
@app.callback(Output("upload_data_div", "style"), [Input("selection_mode", "value")])
def make_visible_upload(selection):
    if selection == "file":
        return {"display": "block"}
    else:
        return {"display": "none"}


# Callback for Component Dropdown box - only components in wells currently drawn on map!
@app.callback(
    Output("component_dropdown", "options"),
    [
        Input("year-slider", "value"),
        Input("operator_dropdown", "value"),
        Input("selection_mode", "value"),
        Input("upload_data", "contents"),
        Input("recent_drop", "value"),
        Input("conf_switch", "value"),
        Input("formation_dropdown", "value"),
    ],
    [State("upload_data", "filename")],
)
def update_component_options(
    selected_year,
    selected_operator,
    selection_mode,
    file_content,
    recency,
    conf_switch,
    formation_list,
    file_name,
):
    filtered_df = filter_df(
        df,
        selected_year,
        selected_operator,
        None,
        selection_mode,
        file_content,
        file_name,
        recency,
        conf_switch,
        formation_list,
    )
    if filtered_df.size == 0:
        return [{"label": "", "value": ""}]
    else:
        options = [
            {"label": i, "value": i}
            for i in df_total.loc[
                df_total["UWI"].isin(filtered_df["UWI"]), "Component Trade Name"
            ]
            .dropna()
            .sort_values()
            .unique()
        ]
        return options


# Selectors to Map
@app.callback(
    Output("graph-with-slider", "figure"),
    [
        Input("year-slider", "value"),
        Input("operator_dropdown", "value"),
        Input("component_dropdown", "value"),
        Input("stages", "selectedData"),
        Input("tons_proppant_stage", "selectedData"),
        Input("selection_mode", "value"),
        Input("graph-with-slider", "selectedData"),
        Input("upload_data", "contents"),
        Input("recent_drop", "value"),
        Input("color_by", "value"),
        Input("shape_drawn", "value"),
        Input("conf_switch", "value"),
        Input("formation_dropdown", "value"),
    ],
    [State("upload_data", "filename")],
)
def update_figure(
    selected_year,
    selected_operator,
    selected_component,
    selected_stages,
    selected_proppant,
    selection_mode,
    selected_area,
    file_content,
    recency,
    color_by,
    shape_drawn,
    conf_switch,
    formation_list,
    file_name,
):
    legend_on = True
    filtered_df = filter_df(
        df,
        selected_year,
        selected_operator,
        selected_area,
        selection_mode,
        file_content,
        file_name,
        recency,
        conf_switch,
        formation_list,
    )

    if selection_mode == "map" or selection_mode == "recent":
        legend_on = False

    # Get the UWI's of passed in selections
    highlight_UWI_comp = df_total["UWI"][
        df_total["Component Trade Name"].isin(selected_component)
    ].unique()

    # If data got updated, default the uirevision flag
    ui_update = "True"
    highlight_UWI_stages = []
    highlight_UWI_proppant = []
    traces = []

    # ***********************************INITIAL DATA**************************************************************
    for i in (
        filtered_df[str(color_by)].sort_values().unique()
    ):  # Allow for different coloring options when looping through points
        df_by_licensee = filtered_df[filtered_df[str(color_by)] == i]
        traces.append(
            go.Scattergeo(
                lon=df_by_licensee["Bottom Hole Longitude"],
                lat=df_by_licensee["Bottom Hole Latitude"],
                text=df_by_licensee["UWI"] + ":" + df_by_licensee[str(color_by)],
                customdata=df_by_licensee["UWI"],
                mode="markers",
                hoverinfo="text",
                opacity=0.5,
                showlegend=legend_on,
                marker={"size": 10, "line": {"width": 0.5, "color": "white"}},
                name=i,
            )
        )
    # ***********************************SELECTED COMPONENT DATA***********************************************************
    # NOTE: Because the UWI's are coming from a dropdown box lookup, no need to look any input selectedData
    if selected_component != None:
        traces.append(
            go.Scattergeo(
                lon=filtered_df["Bottom Hole Longitude"][
                    filtered_df["UWI"].isin(highlight_UWI_comp)
                ],
                lat=filtered_df["Bottom Hole Latitude"][
                    filtered_df["UWI"].isin(highlight_UWI_comp)
                ],
                text=filtered_df["UWI"][filtered_df["UWI"].isin(highlight_UWI_comp)]
                + ":"
                + "COMPONENT",
                customdata=filtered_df["UWI"][
                    filtered_df["UWI"].isin(highlight_UWI_comp)
                ],
                mode="markers",
                hoverinfo="text",
                marker={
                    "color": "rgba(0,0,0,0)",
                    "size": 9,
                    "line": {"width": 0.75, "color": "rgba(0,0,255,1)"},
                },
                name="Selected Components",
            )
        )

    # ***********************************SELECTED STAGES DATA**************************************************************

    if selected_stages != None:
        highlight_UWI_stages = filtered_df["UWI"][
            (filtered_df["Number of Stages"] >= np.min(selected_stages["range"]["x"]))
            & (filtered_df["Number of Stages"] <= np.max(selected_stages["range"]["x"]))
        ]
        traces.append(
            go.Scattergeo(
                lon=filtered_df["Bottom Hole Longitude"][
                    filtered_df["UWI"].isin(highlight_UWI_stages)
                ],
                lat=filtered_df["Bottom Hole Latitude"][
                    filtered_df["UWI"].isin(highlight_UWI_stages)
                ],
                text=filtered_df["UWI"][filtered_df["UWI"].isin(highlight_UWI_stages)]
                + ":"
                + "Stages selected",
                customdata=filtered_df["UWI"][
                    filtered_df["UWI"].isin(highlight_UWI_stages)
                ],
                mode="markers",
                hoverinfo="text",
                marker={
                    "color": "rgba(0,0,0,0)",
                    "size": 10,
                    "line": {"width": 0.75, "color": "rgba(0,255,0,1)"},
                },
                name="Selected Stages",
            )
        )
    # ***********************************SELECTED PROPPANT DATA***********************************************************

    if selected_proppant != None:
        highlight_UWI_proppant = filtered_df["UWI"][
            (
                filtered_df["Total Proppant (tonnes)/Stage"]
                >= np.min(selected_proppant["range"]["x"])
            )
            & (
                filtered_df["Total Proppant (tonnes)/Stage"]
                <= np.max(selected_proppant["range"]["x"])
            )
        ]

        traces.append(
            go.Scattergeo(
                lon=filtered_df["Bottom Hole Longitude"][
                    filtered_df["UWI"].isin(highlight_UWI_proppant)
                ],
                lat=filtered_df["Bottom Hole Latitude"][
                    filtered_df["UWI"].isin(highlight_UWI_proppant)
                ],
                text=filtered_df["UWI"][filtered_df["UWI"].isin(highlight_UWI_proppant)]
                + ":"
                + "Proppant selected",
                customdata=filtered_df["UWI"][
                    filtered_df["UWI"].isin(highlight_UWI_proppant)
                ],
                mode="markers",
                hoverinfo="text",
                marker={
                    "color": "rgba(0,0,0,0)",
                    "size": 11,
                    "line": {"width": 0.75, "color": "rgba(255,0,0,1)"},
                },
                name="Selected Proppant Amt",
            )
        )
    # *********************************BUILD SERIES TO HIGHLIGHT SELECTION BOX************************************************
    # Point ['geo'][0] is top left, ['geo'][1] is bottom right.......work left top left clockwise around building lat,lon lists for rectangle
    if selected_area != None and "range" in selected_area:
        lons = [
            selected_area["range"]["geo"][0][0],
            selected_area["range"]["geo"][1][0],
            selected_area["range"]["geo"][1][0],
            selected_area["range"]["geo"][0][0],
            selected_area["range"]["geo"][0][0],
        ]
        lats = [
            selected_area["range"]["geo"][0][1],
            selected_area["range"]["geo"][0][1],
            selected_area["range"]["geo"][1][1],
            selected_area["range"]["geo"][1][1],
            selected_area["range"]["geo"][0][1],
        ]

        for i in range(len(lons) - 1):
            traces.append(
                go.Scattergeo(
                    lon=[lons[i], lons[i + 1]],
                    lat=[lats[i], lats[i + 1]],
                    name="",
                    hoverinfo="text",
                    text="Selected Region",
                    mode="lines",
                    line={"width": 1, "color": "red"},
                    showlegend=False,
                )
            )

        # Tack on Shape files if selected in check box
    if shape_drawn != "None":
        traces.extend(shape_traces[shape_drawn])
        # ui_update = 'True'

    # IF no data selected - return a dummy point so data selection box tool stays on graph....bit of a workaround
    if filtered_df.size == 0:
        traces.append(dummy)

    # #Check current location shown. Reset zoom to current level if relayoutData was triggered due to zooming in, not data changing
    graph_layout = copy.deepcopy(initial_layout)
    # graph_layout['uirevision'] = ui_update

    return {"data": traces, "layout": graph_layout}


# Callback for the Number of Stages histogram graph
@app.callback(
    Output("stages", "figure"),
    [
        Input("year-slider", "value"),
        Input("operator_dropdown", "value"),
        Input("graph-with-slider", "selectedData"),
        Input("selection_mode", "value"),
        Input("upload_data", "contents"),
        Input("recent_drop", "value"),
        Input("color_by", "value"),
        Input("conf_switch", "value"),
        Input("formation_dropdown", "value"),
    ],
    [State("upload_data", "filename")],
)
def update_stages_figure(
    selected_year,
    selected_operator,
    selected_area,
    selection_mode,
    file_content,
    recency,
    color_by,
    conf_switch,
    formation_list,
    file_name,
):

    filtered_df = filter_df(
        df,
        selected_year,
        selected_operator,
        selected_area,
        selection_mode,
        file_content,
        file_name,
        recency,
        conf_switch,
        formation_list,
    )

    # #Strip out based on UWI's selected on Map. To keep coloring consistent keep total list of wells in filtered_df, filtered_df_selected are only ones drawn
    if (selected_area != None) and (selection_mode != "map"):
        selected_uwi = [point["customdata"] for point in selected_area["points"]]
        filtered_df_selected = filtered_df[filtered_df["UWI"].isin(selected_uwi)]
    else:
        filtered_df_selected = filtered_df

    traces = []
    for i in (
        filtered_df[str(color_by)].sort_values().unique()
    ):  # Allow for different coloring options when looping through points
        df_by_licensee = filtered_df_selected[filtered_df_selected[str(color_by)] == i]
        traces.append(
            go.Histogram(
                x=df_by_licensee["Number of Stages"],
                hoverinfo="text",
                text=df_by_licensee[str(color_by)],
                customdata=df_by_licensee["UWI"],
                opacity=0.5,
                name=i,
            )
        )

    return {
        "data": traces,
        "layout": {
            "title": "Stage Count Histogram",
            "border": "#000000",
            "plot_bgcolor": "#FFFFFF",
            "selectdirection": "h",
            "xaxis": {"title": "# of Stages", "ticks": "inside"},
            "yaxis": {"title": "Count of Wells", "mirror": True},
            "barmode": "stacked",
            "showlegend": False,
            "font": {"size": 12},
            "margin": {"l": 50, "r": 50, "b": 50, "t": 50},
        },
    }


# Callback for the Tonnes Proppant histogram graph
@app.callback(
    Output("tons_proppant_stage", "figure"),
    [
        Input("year-slider", "value"),
        Input("operator_dropdown", "value"),
        Input("graph-with-slider", "selectedData"),
        Input("selection_mode", "value"),
        Input("upload_data", "contents"),
        Input("recent_drop", "value"),
        Input("color_by", "value"),
        Input("conf_switch", "value"),
        Input("formation_dropdown", "value"),
    ],
    [State("upload_data", "filename")],
)
def update_proppant_figure(
    selected_year,
    selected_operator,
    selected_area,
    selection_mode,
    file_content,
    recency,
    color_by,
    conf_switch,
    formation_list,
    file_name,
):

    filtered_df = filter_df(
        df,
        selected_year,
        selected_operator,
        selected_area,
        selection_mode,
        file_content,
        file_name,
        recency,
        conf_switch,
        formation_list,
    )
    # remove wells with Proppant values greater than 500/stage...

    filtered_df.loc[
        filtered_df["Total Proppant (tonnes)/Stage"] >= 500,
        "Total Proppant (tonnes)/Stage",
    ] = ""

    # #Strip out based on UWI's selected on Map. To keep coloring consistent keep total list of wells in filtered_df, filtered_df_selected are only ones drawn
    if (selected_area != None) and (selection_mode != "map"):
        selected_uwi = [point["customdata"] for point in selected_area["points"]]
        filtered_df_selected = filtered_df[filtered_df["UWI"].isin(selected_uwi)]
    else:
        filtered_df_selected = filtered_df

    traces = []
    for i in filtered_df[str(color_by)].sort_values().unique():
        df_by_licensee = filtered_df_selected[filtered_df_selected[str(color_by)] == i]
        traces.append(
            go.Histogram(
                x=df_by_licensee["Total Proppant (tonnes)/Stage"],
                customdata=df_by_licensee["UWI"],
                text=df_by_licensee[str(color_by)],
                hoverinfo="text",
                opacity=0.5,
                name=i,
            )
        )

    return {
        "data": traces,
        "layout": {
            "border": "#000000",
            "plot_bgcolor": "#FFFFFF",
            "selectdirection": "h",
            "title": "Proppant Per Stage Histogram",
            "xaxis": {
                "title": "Total Proppant (tonnes)/Stage",
                "ticks": "inside"
                #'range':[0,600]
            },
            "yaxis": {"title": "Count of Wells", "mirror": True},
            #'barmode':'overlay',
            "showlegend": False,
            "font": {"size": 12},
            "margin": {"l": 50, "r": 50, "b": 50, "t": 50},
        },
    }


# #Callback to populate component table with selected well
@app.callback(
    Output("selected_well_comp", "data"), [Input("graph-with-slider", "clickData")]
)
def update_selected_well_components(clicked_well):
    if clicked_well != None:
        if clicked_well["points"][0]["customdata"] != None:
            selected_uwi = [point["customdata"] for point in clicked_well["points"]]
            return_df = df_total.loc[
                df_total["UWI"].isin(selected_uwi), cols_displayed_comp
            ]
            # return_df.fillna('BLANK',inplace=True)
            return return_df.to_dict("records")
    else:
        return [{}]


# # #Callback to populate well table with selected well
@app.callback(
    Output("selected_well", "data"), [Input("graph-with-slider", "clickData")]
)
def update_selected_well_table(clicked_well):
    if clicked_well != None:
        if (
            clicked_well["points"][0]["customdata"] != None
        ):  # if a trace object that doesn't have custom data is clicked, skip returning data
            selected_uwi = [point["customdata"] for point in clicked_well["points"]]
            return_df = df.loc[df["UWI"].isin(selected_uwi), cols_displayed_well]

            # Fill proppant values that are errors, > 500 tonnes per stage
            return_df.loc[
                return_df["Total Proppant (tonnes)/Stage"] >= 500,
                "Total Proppant (tonnes)/Stage",
            ] = "ERROR"
            # return_df.fillna('BLANK',inplace=True)
            return return_df.to_dict("records")
    else:
        return [{}]


# Callback for the Div that contains error messages
@app.callback(
    Output("error_box", "children"),
    [
        Input("year-slider", "value"),
        Input("operator_dropdown", "value"),
        Input("graph-with-slider", "selectedData"),
        Input("selection_mode", "value"),
        Input("upload_data", "contents"),
        Input("recent_drop", "value"),
        Input("conf_switch", "value"),
        Input("formation_dropdown", "value"),
    ],
    [State("upload_data", "filename")],
)
def update_error_box(
    selected_year,
    selected_operator,
    selected_area,
    selection_mode,
    file_content,
    recency,
    conf_switch,
    formation_list,
    file_name,
):

    filtered_df = filter_df(
        df,
        selected_year,
        selected_operator,
        selected_area,
        selection_mode,
        file_content,
        file_name,
        recency,
        conf_switch,
        formation_list,
    )
    selected_uwi = []

    if selection_mode == "map" and selected_area == None:
        return "Please use box selection on map to select a region"
    elif filtered_df.size == 0 and selection_mode == "map":
        return "No wells found in selected area"
    elif selection_mode == "operator_year":
        if selected_area != None:
            selected_uwi = [point["customdata"] for point in selected_area["points"]]
            filtered_df = filtered_df[filtered_df["UWI"].isin(selected_uwi)]
        if filtered_df.size == 0:
            return "No wells in map within the selected area"
    elif selection_mode == "recent" and filtered_df.size == 0:
        return "No wells within recent period"
    elif selection_mode == "file" and file_name == None:
        return "Please upload a CSV file"
    else:
        return ""


# Callback for upload component to display file name info and wells selected
@app.callback(
    Output("upload_data", "children"),
    [Input("upload_data", "contents")],
    [State("upload_data", "filename")],
)
def update_upload_component(file_content, file_name):
    if file_name == None:
        return html.Div(
            [
                "Drag and Drop UWI (XX/XX-XX-XXX-XXWX/X) List or ",
                html.A("Select UWI List (.csv)"),
            ]
        )
    else:
        return html.Div(
            [
                "File Selected: " + str(file_name) + ".....",
                html.A("Select new UWI (XX/XX-XX-XXX-XXWX/X) List (.csv)"),
            ]
        )


# Callback for the Formations drop down to make it more user friendly - populate with all Formations for selected operators within selected years
@app.callback(
    Output("formation_dropdown", "value"),
    [Input("operator_dropdown", "value"), Input("year-slider", "value")],
)
def populate_formations(operators, selected_year):
    return (
        df.loc[
            (
                df["Licensee"].isin(operators)
                & (df["year"] >= np.min(selected_year))
                & (df["year"] <= np.max(selected_year))
            ),
            "Terminating Formation",
        ]
        .unique()
        .tolist()
    )


# FOR EXTERNAL CSS base style sheet USE THE FOLLOWING
# app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
# FOR

# FOR OFFLINE USE THE FOLLOWING
# app.css.config.serve_locally = True
# app.scripts.config.serve_locally = True
