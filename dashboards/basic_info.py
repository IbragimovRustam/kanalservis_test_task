import os
import re
import pandas as pd
import numpy as np
import datetime
import gspread

from sqlalchemy import create_engine
import io

import plotly.graph_objects as go

from dash import Dash, dash_table, html, dcc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from .dash_fun import apply_layout_without_auth

import requests
import xmltodict, json

from flask import current_app
from config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)

url_base = '/dash/app1/'

layout = dict(
            bargap=0.1, # gap between bars of adjacent location coordinates.
            bargroupgap=0.25, # gap between bars of the same location coordinate.
            title={
                    # 'text': '<b>Расчет KPI по специальностям</b><br>',
                    'font_size': 15,
                    'x':0.5, 'y':0.97,
                    'xanchor': 'center'},
            yaxis=dict(
                mirror=True,
                showline=True, 
                linewidth=1, 
                linecolor='black',
                showticklabels=True,
                # rangemode = 'tozero',
                gridcolor = '#D5D5D5',
                tickfont=dict(
                    family='Arial',
                    size=13,
                    color='rgb(40, 40, 40)',
                ),
                domain=[0, 0.95],
            ),
            xaxis=dict(
                mirror=True,
                showline=True, 
                linewidth=1,
                linecolor='black',
                zeroline=False,
                showticklabels=True,
                gridcolor = '#D5D5D5',
                ticks='outside',
                tickfont=dict(
                    family='Arial',
                    size=12,
                    color='rgb(82, 82, 82)',
                ),
                showgrid=True,
                # domain=[0.7, 1.0],
                # range=[0, 110],
            ),
            showlegend=True,
            legend=dict(x=1.1, y=0.96, font_size=12, orientation='v', bordercolor='Black', borderwidth=1),
            margin=dict(l=5, r=5, t=50, b=10),
            # paper_bgcolor='rgb(248, 248, 255)',
            # plot_bgcolor='rgb(248, 248, 255)',
            paper_bgcolor='#FFFFFF',
            plot_bgcolor='#FFFFFF',
        )

def graph_config(filename='new_plot'):
    config = {"scrollZoom": False, "displayModeBar": 'hover', "showSendToCloud": False, "displaylogo":False, "responsive": True,
                'toImageButtonOptions': {
                    'format': 'jpeg', # one of png, svg, jpeg, webp
                    'filename': filename,
                    'height': None, 'width': None,
                    'scale': 1 # Multiply title/legend/axis/canvas sizes by this factor
                    },
                'modeBarButtonsToRemove': ['zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian', 'toggleSpikelines']
    }
    return config


def add_table(df, table_name, method='replace'): # method='replace', 'append'
    df.head(0).to_sql(table_name, engine, if_exists=method, index=False) #truncates the table
    conn = engine.raw_connection()
    cur = conn.cursor()
    output = io.StringIO()
    df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    contents = output.getvalue()
    cur.copy_from(output, table_name, null="") # null values become ''
    conn.commit()


def put_data_to_db(df):
    if engine.url.drivername == 'sqlite':
        df.to_sql('orders', engine, if_exists='replace', index=False)
    else:
        add_table(df, 'orders')


def get_usd_rub_curs():
    """
        Функция для получения текущего курса рубля по отношению к доллару
    """
    current_data = datetime.datetime.now().strftime('%d/%m/%Y')
    url = f"http://www.cbr.ru/scripts/XML_daily.asp?date_req={current_data}"
    try:
        response = requests.request("GET", url)
    except Exception as e:
        usd_rub_value = None
    response_xml_dict = xmltodict.parse(response.text)
    usd_rub = next((item for item in response_xml_dict['ValCurs']['Valute'] if item["Name"] == "Доллар США"), None)
    usd_rub_value = float(usd_rub.get('Value').replace(',', '.'))
    
    return usd_rub_value


def create_df():
    mult = get_usd_rub_curs()
    sa = gspread.service_account(filename='service_accounts.json')
    sh = sa.open("test")
    wks = sh.worksheet('data')
    data = wks.get_all_values()
    headers = data.pop(0)
    df = pd.DataFrame(data, columns=headers)
    df[['заказ №', 'стоимость,$']] = df[['заказ №', 'стоимость,$']].astype('int')
    df['стоимость в руб.'] = df['стоимость,$']*mult
    df['срок поставки'] = pd.to_datetime(df['срок поставки'], format='%d.%m.%Y')
    df.sort_values(by='срок поставки', inplace=True)
    df = df.reindex(columns = ['№','заказ №','стоимость,$', 'стоимость в руб.', 'срок поставки'])
    df.columns = ['num', 'order_num', 'cost_usd', 'cost_rub', 'deliver_date']

    df['id'] = df.index+1
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    df = df[cols]

    put_data_to_db(df)

    return df



def create_graph(df):
    fig = go.Figure(layout=layout)
    fig.add_trace(go.Scatter(
        y = df['cost_usd'],
        x = df['deliver_date'],
        mode='lines+markers',
        name='',
        marker=dict(
            opacity = 0.85,
            # showscale=True,
            line=dict(color='blue', width=1.5)
        ),

    ))

    fig.update_layout(
        showlegend=False,
        title={'text': 'Изменение стоимости заказов по времени',
    #     title={'text': '<b>Covid-19 Казахстан на дату 30 апреля 2020 г.</b><br>'+subtitle,
                'font_size': 15,
                'x':0.5, 'y':0.97,
                'xanchor': 'center'},
        height=500,
        yaxis=dict(
            title={'text': 'Стоимость заказа, $'},
            # showline=False,
            # domain=[0, 1.0],
        ),
        xaxis=dict(

        ),
        margin=dict(l=20, r=20, t=40, b=20),
    )

    return fig


app_layout = html.Div(
    [       
        html.Div(
            [
                html.Div(
                    [
                        html.H2(['Каналсервис'],
                                style={'margin-top': '30px'}
                        ),
                    ],
                    id='title',
                    # className='one-half column',
                    className='twelve columns',
                )
            ],
        id='header',
        className='flex-display',
        style={'margin-bottom': '25px'},
        ),
        html.Br(),
        html.Div(
            [
                html.Button(['Обновить'], id='button_1', n_clicks=0, className='btn btn-outline-secondary btn-lg'),
                dcc.Loading(id='loading-1', type='default', children=html.Div(id='loading-output-1')),
            ]
        ),
        html.Br(),
        html.Hr(),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id='1_graph', config=graph_config(filename='Стоимсть заказа'), className='groove_border')
                    ],
                    className='six columns',
                ),
                html.Div(
                    [
                        html.Div(
                            [   
                                html.H1(id='total_cost'),
                            ],
                            className='row',
                            # style = {'justify-content': 'center'}
                        ),
                        html.Div(
                            [   
                                dash_table.DataTable(
                                    data=[], #df.to_dict('records'),
                                    columns=[],
                                    id='initial_table',
                                )
                            ],
                            className='row',
                            # style = {'justify-content': 'center'}
                        ),
                    ],
                    className='six columns',
                    style = {'text-align': 'center', 'margin-left': '100px'}
                ),
            ],
            className='flex-display',
        ),
        html.Br(),


        html.Div(id='intermediate-value_df_1', style={'display': 'none'}),    
    ],
    className='main-window'
)




def Add_Dash(server):
    app = Dash(server=server, url_base_pathname=url_base, assets_folder='static/dash_assets/IM_assets') # external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    apply_layout_without_auth(app, app_layout)


    @app.callback([Output('loading-output-1', 'children'),
                    Output('intermediate-value_df_1', 'children'),
                    ],
                    [Input('button_1', 'n_clicks'),])
    def update_create_df(n_clicks):
        print(n_clicks)
        if not n_clicks:
            raise PreventUpdate
        else:
            df = create_df()
            jsonified_data = df.to_json(date_format='iso', orient='split')

            return '', jsonified_data


    @app.callback([Output('1_graph', 'figure'), 
                    Output('total_cost', 'children'),
                    Output('initial_table', 'data'), Output('initial_table', 'columns')],

                [Input('intermediate-value_df_1', 'children'),
                ],
                )
    def update_create_first_bar(jsonified_data):
        if jsonified_data is None:
            raise PreventUpdate
        else:
            dff = pd.read_json(jsonified_data, orient='split')
            fig = create_graph(dff)
            
            total_cost = dff['cost_usd'].sum()
            total_cost_title = f'Total - {total_cost} $'

            # data = dff.iloc[:, 1:].to_dict('records')
            # columns = [{"name": i, "id": i} for i in ['№', 'заказ №', 'стоимость,$', 'стоимость в руб.', 'срок поставки']]

            dff.sort_values(by='num', inplace=True)
            dff['deliver_date'] = pd.to_datetime(dff['deliver_date'])
            dff['deliver_date'] = dff['deliver_date'].dt.strftime('%d-%m-%Y')
            dff = dff.iloc[:, 1:]
            dff.columns = ['№','заказ №','стоимость,$', 'стоимость в руб.', 'срок поставки']

            data = dff.to_dict('records')
            # columns = [{"name": i, "id": i} for i in dff.columns]
            columns=[{'name': i, 'id': i} if i != 'срок поставки' else {'name': 'срок поставки', 'id': 'срок поставки', 'type': 'datetime'} for i in dff.columns]

        return fig, total_cost_title, data, columns


    # @app.callback(Output('2_bar_graph', 'figure'),
    #             [Input('intermediate-value_df_1', 'children'),
    #              Input('1_bar_graph', 'clickData'),
    #              Input('axis_type_bar_2', 'value')
    #             ],
    #             )
    # def update_create_second_bar(jsonified_data, bar_click, axis_type):
    #     if jsonified_data is None:
    #         raise PreventUpdate
    #     else:
    #         dff = pd.read_json(jsonified_data, orient='split')
    #         if bar_click is None:
    #             company = dff.groupby('departament')['rashod'].agg(['sum']).reset_index().sort_values(by='sum').iloc[-1]['departament']
    #         else:
    #             company = bar_click['points'][0]['label']          
    #         df = dff[dff['departament'] == company].sort_values(by='rashod')
    #         for i, k in df[df['departament'] == company].groupby('mnem'):
    #             if len(k)>1:
    #                 sub_index = 1
    #                 for n, m in k.iterrows():
    #                     df.loc[n, 'mnem'] = df.loc[n, 'mnem']+'_'+str(sub_index)
    #                     sub_index = sub_index+1

    #         fig = create_second_bar(df, company, axis_type)

    #     return fig
    
    

    
    return app.server