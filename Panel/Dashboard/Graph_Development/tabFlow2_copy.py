from matplotlib.pyplot import title
import pandas as pd
import panel as pn
import os, tornado
import itertools
import plotly.graph_objs as go
import datetime as dt
import numpy as np

import constants as c
import dashboard_constants as dc

currentDir = os.path.join(os.getcwd(),'data')
dateColumn = 'Date'

def mainFun():
    # Get all the dataset from csv file
    uname = tornado.escape.json_decode(pn.state.cookies['user'])
    try:
        df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
    except: 
        df_flow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

    # convert string to datetime format
    df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

    df_flow = df_flow.fillna(0)  
    df_flow = df_flow.round(2) 

    #Dynamically get all the fields according to its types
    flowType = []
    for i in df_flow.columns:
        if df_flow[i].dtype == 'int64':
            flowType.append(i)
        if df_flow[i].dtype == 'float64':
            flowType.append(i)

    allPackage = ['Select All']
    for i in list(df_flow['subscr_type'].unique()):
        allPackage.append(i)

    renameGraph = {
        'newcheck': 'Inflow',
        'churncheck': 'Outflow',
        'currentcheck': 'Active Subscribers',
        'inflow_transformers': 'Transformers Inflow',
        'inflow_switchers': 'Switchers Inflow',
        'trans_outflow': 'Transformers Outflow',
        'switcher_outflow': 'Switchers Outflow',
        'switcher_winback': ' Switchers Winback'
    }

    # create a new column for selectIntegrityDate date-slider
    mon_year = df_flow[dateColumn].dt.strftime('%b-%Y')
    df_flow.insert(1, 'mon_year', mon_year)
    df_flow = df_flow.sort_values(by=dateColumn)

    # Drop-downs for different variables for flow tab
    selectBrandFlow = pn.widgets.Select(name='Brand', options=list(df_flow['brand'].unique()), value='DS')
    #selectPrintFlow = pn.widgets.Select(name='Print', options=list(df_flow['print'].unique()), value=df_flow['print'][0])
    selectSubscr_TypeFlow = pn.widgets.MultiChoice(name='Package Type', options=allPackage, value=['ZADI'], solid=False)
    selectFlowType = pn.widgets.MultiChoice(name='Flow Type', options=flowType, value=[flowType[0]], solid=False)
    selectDateRange = pn.widgets.DateRangeSlider(name='Date Range', start=dt.datetime(2017, 1, 1), end=dt.datetime(2019, 1, 1), value=(dt.datetime(2016, 1, 1), dt.datetime(2020, 7, 1)))
    selectEndDate = pn.widgets.DiscreteSlider(name='Select End Date', options=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique()), value=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique())[-1])
    selectStartDate = pn.widgets.DiscreteSlider(name='Select Start Date', options=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique()), value=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique())[0])

    # Buttons
    downloadButton = pn.widgets.Button(name='Download as CSV', button_type='primary', width=250)

    from .main_dev import dummySlider

    # interaction function newcheck
    @pn.depends(selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotRegularInflowGraph(selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
        print("Seventh ----------------------------", dSlider)
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        traces = []
        try:
            df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_flow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

        # convert string to datetime format
        df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

        df_flow = df_flow.fillna(0)  
        df_flow = df_flow.round(2) 
        # create a new column for selectIntegrityDate date-slider
        mon_year = df_flow[dateColumn].dt.strftime('%b-%Y')
        df_flow.insert(1, 'mon_year', mon_year)
        df_flow = df_flow.sort_values(by=dateColumn)

        layout=go.Layout()

        df_flow['newcheck'] = df_flow['newcheck'].astype(int)
        traces = []
        listOfSelections = []
        listOfName = []
    
        listOfSelections.append([selectedBrand])
        listOfName.append('brand')
        if 'Select All' in selectedSubscr_Type or selectedSubscr_Type == []:
            listOfSelections.append(list(df_flow['subscr_type'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedSubscr_Type)
            listOfName.append('subscr_type')
        #listOfSelections.append([selectedPrint])
        #listOfName.append('print')
        listOfSelections.append(['newcheck'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0]) 
                        & (df_flow['subscr_type'] == combs[1])]
                        #& (df_flow['print'] ==  combs[2])]
                        
            df_graph = df_graph.groupby([dateColumn,'forecast'])[combs[2]].sum().reset_index()

            rename = combs[2]
            if combs[2] in renameGraph:
                rename = renameGraph[combs[2]]
            
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 0][dateColumn], y=df_graph[df_graph['forecast'] == 0][combs[2]], text=list(df_graph[combs[2]]), textposition='auto', name=combs[1]+' Actual'))
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[2]], text=list(df_graph[df_graph['forecast'] == 1][combs[2]]), textposition='auto', name=combs[1]+' forecast'))
            
            # Create layout for graph
            layout = go.Layout(
                title="Regular Inflow",
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=1400, 
                height=500,
                barmode='stack',
                autosize=False,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Regular Inflow')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotRegularOutflowGraph(selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        traces = []
        try:
            df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_flow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

        # convert string to datetime format
        df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

        df_flow = df_flow.fillna(0)  
        df_flow = df_flow.round(2) 
        # create a new column for selectIntegrityDate date-slider
        mon_year = df_flow[dateColumn].dt.strftime('%b-%Y')
        df_flow.insert(1, 'mon_year', mon_year)
        df_flow = df_flow.sort_values(by=dateColumn)

        df_flow['churncheck'] = df_flow['churncheck'].astype(int)
        traces = []
        layout=go.Layout()
                
        traces = []
        listOfSelections = []
        listOfName = []

        listOfSelections.append([selectedBrand])
        listOfName.append('brand')
        if 'Select All' in selectedSubscr_Type or selectedSubscr_Type == []:
            listOfSelections.append(list(df_flow['subscr_type'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedSubscr_Type)
            listOfName.append('subscr_type')
        #listOfSelections.append([selectedPrint])
        #listOfName.append('print')
        listOfSelections.append(['churncheck'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0]) 
                        & (df_flow['subscr_type'] == combs[1])]
                        #& (df_flow['print'] ==  combs[2])]

            df_graph = df_graph.groupby([dateColumn,'forecast'])[combs[2]].sum().reset_index()

            rename = combs[2]
            if combs[2] in renameGraph:
                rename = renameGraph[combs[2]]

                                
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 0][dateColumn], y=df_graph[df_graph['forecast'] == 0][combs[2]], text=list(df_graph[combs[2]]), textposition='auto', name=combs[1]+' Actual'))
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[2]], text=list(df_graph[df_graph['forecast'] == 1][combs[2]]), textposition='auto', name=combs[1]+' forecast'))
            
            # Create layout for graph
            layout = go.Layout(
                title="Regular Outflow",
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=1400, 
                height=500,
                barmode='stack',
                autosize=False,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Regular Outflow')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate)
    def plotSubscribersGraph(selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        traces = []
        try:
            df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_flow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

        # convert string to datetime format
        df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

        df_flow = df_flow.fillna(0)  
        df_flow = df_flow.round(2) 
        # create a new column for selectIntegrityDate date-slider
        mon_year = df_flow[dateColumn].dt.strftime('%b-%Y')
        df_flow.insert(1, 'mon_year', mon_year)
        df_flow = df_flow.sort_values(by=dateColumn)
        
        layout=go.Layout()
        df_flow['currentcheck'] = df_flow['currentcheck'].astype(int)
        traces = []
        listOfSelections = []
        listOfName = []

        listOfSelections.append([selectedBrand])
        listOfName.append('brand')
        if 'Select All' in selectedSubscr_Type or selectedSubscr_Type == []:
            listOfSelections.append(list(df_flow['subscr_type'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedSubscr_Type)
            listOfName.append('subscr_type')
        #listOfSelections.append([selectedPrint])
        #listOfName.append('print')
        listOfSelections.append(['currentcheck'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0]) 
                        & (df_flow['subscr_type'] == combs[1])]
                        #& (df_flow['print'] ==  combs[2])]

            df_graph = df_graph.groupby([dateColumn,'forecast'])[combs[2]].sum().reset_index()

            rename = combs[2]
            if combs[2] in renameGraph:
                rename = renameGraph[combs[2]]

                                    
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 0][dateColumn], y=df_graph[df_graph['forecast'] == 0][combs[2]], text=list(df_graph[combs[2]]), textposition='auto', name=combs[1]+' Actual'))
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[2]], text=list(df_graph[df_graph['forecast'] == 1][combs[2]]), textposition='auto', name=combs[1]+' forecast'))
            
            # Create layout for graph
            layout = go.Layout(
                title="Active Subscribers",
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=1400, 
                height=500,
                barmode='stack',
                autosize=False,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Subscribers')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotTransformersGraph(selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        try:
            df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_flow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

        # convert string to datetime format
        df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

        df_flow = df_flow.fillna(0)  
        df_flow = df_flow.round(2) 
        # create a new column for selectIntegrityDate date-slider
        mon_year = df_flow[dateColumn].dt.strftime('%b-%Y')
        df_flow.insert(1, 'mon_year', mon_year)
        df_flow = df_flow.sort_values(by=dateColumn)

        traces = []
        layout=go.Layout()
        df_flow['inflow_transformers'] = df_flow['inflow_transformers'].astype(int)
        traces = []
        listOfSelections = []
        listOfName = []

        listOfSelections.append([selectedBrand])
        listOfName.append('brand')
        if 'Select All' in selectedSubscr_Type or selectedSubscr_Type == []:
            listOfSelections.append(list(df_flow['subscr_type'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedSubscr_Type)
            listOfName.append('subscr_type')
        #listOfSelections.append([selectedPrint])
        #listOfName.append('print')
        listOfSelections.append(['inflow_transformers'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0]) 
                        & (df_flow['subscr_type'] == combs[1])]
                        #& (df_flow['print'] ==  combs[2])]
            
            df_graph = df_graph.groupby([dateColumn, 'forecast'])[combs[2]].sum().reset_index()
            
            rename = combs[2]
            if combs[2] in renameGraph:
                rename = renameGraph[combs[2]]

                                        
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 0][dateColumn], y=df_graph[df_graph['forecast'] == 0][combs[2]], text=list(df_graph[df_graph['forecast'] == 0][combs[2]]), textposition='auto', name=combs[1]+' '+combs[2]+' Actual'))
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[2]], text=list(df_graph[df_graph['forecast'] == 1][combs[2]]), textposition='auto', name=combs[1]+' forecast'))
            
            # Create layout for graph
            layout = go.Layout(
                title="Transformers Inflow",
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=1400, 
                height=500,
                barmode='stack',
                autosize=False,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Transformers')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotSwitchersGraph(selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        traces = []
        try:
            df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_flow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

        # convert string to datetime format
        df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

        df_flow = df_flow.fillna(0)  
        df_flow = df_flow.round(2) 
        # create a new column for selectIntegrityDate date-slider
        mon_year = df_flow[dateColumn].dt.strftime('%b-%Y')
        df_flow.insert(1, 'mon_year', mon_year)
        df_flow = df_flow.sort_values(by=dateColumn)

        layout=go.Layout()
        df_flow['inflow_switchers'] = df_flow['inflow_switchers'].astype(int)
        traces = []
        listOfSelections = []
        listOfName = []

        listOfSelections.append([selectedBrand])
        listOfName.append('brand')
        if 'Select All' in selectedSubscr_Type or selectedSubscr_Type == []:
            listOfSelections.append(list(df_flow['subscr_type'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedSubscr_Type)
            listOfName.append('subscr_type')
        #listOfSelections.append([selectedPrint])
        #listOfName.append('print')
        listOfSelections.append(['inflow_switchers'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0]) 
                        & (df_flow['subscr_type'] == combs[1])]
                        #& (df_flow['print'] ==  combs[2])]
            
            df_graph = df_graph.groupby([dateColumn, 'forecast'])[combs[2]].sum().reset_index()
            # df_graph2 = df_graph.groupby(dateColumn)[combs[2]].sum().reset_index()

            rename = combs[2]
            if combs[2] in renameGraph:
                rename = renameGraph[combs[2]]

                                            
            # traces.append(go.Bar(x=df_graph[dateColumn], y=df_graph[combs[2]], text=list(df_graph[combs[2]]), textposition='auto', name=combs[1]+' Actual'))
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 0][dateColumn], y=df_graph[df_graph['forecast'] == 0][combs[2]], text=list(df_graph[df_graph['forecast'] == 0][combs[2]]), textposition='auto', name=combs[1]+' '+combs[2]+' Actual'))
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[2]], text=list(df_graph[df_graph['forecast'] == 1][combs[2]]), textposition='auto', name=combs[1]+' '+combs[2]+' Forecast'))
            
            # Create layout for graph
            layout = go.Layout(
                title=rename.capitalize(),
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=1400, 
                height=500,
                barmode='stack',
                autosize=True,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Switchers')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    # Transformers Outflow
    @pn.depends(selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotTransformersOutflowGraph(selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        traces = []
        try:
            df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_flow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

        # convert string to datetime format
        df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

        df_flow = df_flow.fillna(0)  
        df_flow = df_flow.round(2) 
        # create a new column for selectIntegrityDate date-slider
        mon_year = df_flow[dateColumn].dt.strftime('%b-%Y')
        df_flow.insert(1, 'mon_year', mon_year)
        df_flow = df_flow.sort_values(by=dateColumn)

        layout=go.Layout()
        df_flow['trans_outflow'] = df_flow['trans_outflow'].astype(int)
        traces = []
        listOfSelections = []
        listOfName = []

        listOfSelections.append([selectedBrand])
        listOfName.append('brand')
        if 'Select All' in selectedSubscr_Type or selectedSubscr_Type == []:
            listOfSelections.append(list(df_flow['subscr_type'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedSubscr_Type)
            listOfName.append('subscr_type')
        listOfSelections.append(['trans_outflow'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0]) 
                        & (df_flow['subscr_type'] == combs[1])]
            df_graph = df_graph.groupby([dateColumn, 'forecast'])[combs[2]].sum().reset_index()
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 0][dateColumn], y=df_graph[df_graph['forecast'] == 0][combs[2]], text=list(df_graph[df_graph['forecast'] == 0][combs[2]]), textposition='auto', marker_color='#34495e', name=combs[1]+' '+combs[2]+' Actual'))
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[2]], text=list(df_graph[df_graph['forecast'] == 1][combs[2]]), textposition='auto', marker_color='#4cd137', name=combs[1]+' '+combs[2]+' forecast'))

            # Create layout for graph
            layout = go.Layout(
                title="Transformers Outflow",
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=1400, 
                height=500,
                barmode='stack',
                autosize=False,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Transformers Outflow')
            ) 
        
        return go.Figure(data=traces, layout=layout)


    #Switchers Outflow
    @pn.depends(selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotSwitchersOutflowGraph(selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        traces = []
        try:
            df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_flow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

        # convert string to datetime format
        df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

        df_flow = df_flow.fillna(0)  
        df_flow = df_flow.round(2) 
        # create a new column for selectIntegrityDate date-slider
        mon_year = df_flow[dateColumn].dt.strftime('%b-%Y')
        df_flow.insert(1, 'mon_year', mon_year)
        df_flow = df_flow.sort_values(by=dateColumn)

        layout=go.Layout()
        df_flow['switcher_outflow'] = df_flow['switcher_outflow'].astype(int)
        traces = []
        listOfSelections = []
        listOfName = []

        listOfSelections.append([selectedBrand])
        listOfName.append('brand')
        if 'Select All' in selectedSubscr_Type or selectedSubscr_Type == []:
            listOfSelections.append(list(df_flow['subscr_type'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedSubscr_Type)
            listOfName.append('subscr_type')
        listOfSelections.append(['switcher_outflow'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0]) 
                        & (df_flow['subscr_type'] == combs[1])]
            
            df_graph = df_graph.groupby([dateColumn, 'forecast'])[combs[2]].sum().reset_index()
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 0][dateColumn], y=df_graph[df_graph['forecast'] == 0][combs[2]], text=list(df_graph[combs[2]]), textposition='auto', marker_color='#34495e', name=combs[1]+' '+combs[2]+' Actual'))
            traces.append(go.Bar(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[2]], text=list(df_graph[df_graph['forecast'] == 1][combs[2]]), textposition='auto', marker_color='#4cd137', name=combs[1]+'_'+combs[2]+' forecast'))
            
            # Create layout for graph
            layout = go.Layout(
                title="Switchers Outflow",
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=1400, 
                height=500,
                barmode='stack',
                autosize=True,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Switcher Outflow')
            ) 
        
        return go.Figure(data=traces, layout=layout)


    # function for click event to download file
    def downloadFile(event):
        pass
    '''    with open(tableFileName, 'w') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(table_df_flow.columns)
            csvwriter.writerows(table_df_flow.values)'''

    # function call for download csv
    downloadButton.on_click(downloadFile)

    #pn.config.sizing_mode = 'stretch_width'

    return pn.Column(
        pn.Row(
            pn.Column(
                selectStartDate,
                selectEndDate
            ),
            pn.Column(
                selectBrandFlow,
                #selectPrintFlow
            ),
            pn.Column(
                selectSubscr_TypeFlow
            )
        ),
        pn.Column(
                pn.panel(plotRegularInflowGraph),
                pn.panel(plotRegularOutflowGraph),
                pn.panel(plotSubscribersGraph),
                pn.panel(plotTransformersGraph),
                pn.panel(plotTransformersOutflowGraph),
                pn.panel(plotSwitchersGraph),
                pn.panel(plotSwitchersOutflowGraph)
        )
    )