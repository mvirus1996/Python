import pandas as pd
import panel as pn
import os, itertools, tornado
import plotly.graph_objs as go
import datetime as dt

import constants as c
import dashboard_constants as dc

currentDir = os.path.join(os.getcwd(),'data')
dateColumn = 'Date'

def mainFun():
    uname = tornado.escape.json_decode(pn.state.cookies['user'])
    try:
        print("inside try tabflow: ")
        df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
    except: 
        df_flow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

    # convert string to datetime format
    df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

    df_flow = df_flow.fillna(0)  
    df_flow = df_flow.round(2) 

    allPackage = ['Select All']
    for i in list(df_flow['subscr_type'].unique()):
        allPackage.append(i)

    allPrice = ['Select All']
    for i in list(df_flow['pricecat'].unique()):
        allPrice.append(i)

    allBrand = []
    for i in list(df_flow['brand'].unique()):
        allBrand.append(i)

    #Dynamically get all the fields according to its types
    flowType = []
    for i in df_flow.columns:
        if df_flow[i].dtype == 'int64':
            flowType.append(i)
        if df_flow[i].dtype == 'float64':
            flowType.append(i)

    # create a new column for selectIntegrityDate date-slider
    mon_year = df_flow[dateColumn].dt.strftime('%b-%Y')
    df_flow.insert(1, 'mon_year', mon_year)
    df_flow = df_flow.sort_values(by=dateColumn)

    # Drop-downs for different variables for flow tab
    selectBrandFlow = pn.widgets.Select(name='Brand', options=allBrand, value='DS')
    selectSubscr_TypeFlow = pn.widgets.MultiChoice(name='Package Type', options=allPackage, value=['ZADI'], solid=False)
    selectPriceFlow = pn.widgets.MultiChoice(name='Price Category', options=allPrice, value=['BASE'], solid=False)
    selectFlowType = pn.widgets.MultiChoice(name='Flow Type', options=flowType, value=[flowType[0]], solid=False)
    selectDateRange = pn.widgets.DateRangeSlider(name='Date Range', start=dt.datetime(2017, 1, 1), end=dt.datetime(2019, 1, 1), value=(dt.datetime(2016, 1, 1), dt.datetime(2020, 7, 1)))
    selectEndDate = pn.widgets.DiscreteSlider(name='Select End Date', options=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique()), value=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique())[-1])
    selectStartDate = pn.widgets.DiscreteSlider(name='Select Start Date', options=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique()), value=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique())[0])

    # Buttons
    downloadButton = pn.widgets.Button(name='Download as CSV', button_type='primary', width=250)

    from .main_dev import dummySlider

    renameGraph = {
        'newcheck': 'Inflow',
        'churncheck': 'Outflow',
        'currentcheck': 'Active Subscribers',
        'inflow_transformers': 'Transformers Inflow',
        'inflow_switchers': 'Switchers Inflow',
        'trans_outflow': 'Transformers Outflow',
        'switcher_outflow': 'Switchers Outflow'
    }

    @pn.depends(selectedDateRange=selectDateRange, selectedBrand = selectBrandFlow, dSlider = dummySlider)
    def plotTotalGraph(selectedDateRange,selectedBrand, dSlider):
        print("Third ------------------ ", dSlider)
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        try:
            df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_flow = pd.read_csv(os.path.join(currentDir, 'switchtransfinal_with_forecast.csv'), sep=';')

        # convert string to datetime format
        df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

        df_flow = df_flow.fillna(0)  
        df_flow = df_flow.round(2) 
        # create a new column for selectIntegrityDate date-slider
        mon_year = df_flow[dateColumn].dt.strftime('%b-%Y')
        df_flow.insert(1, 'mon_year', mon_year)
        df_flow = df_flow.sort_values(by=dateColumn)

        traces = []
        df_graph = df_flow.loc[(df_flow[dateColumn] >= dc.SLIDER_DATE)]
       

        df_flow['newcheck'] = df_flow['newcheck'].astype(int)
        df_flow['churncheck'] = df_flow['churncheck'].astype(int)


        df_graph = df_graph.loc[(df_graph['brand'] == selectedBrand)]
        df_graph = df_graph.groupby(df_graph[dateColumn].dt.year)['newcheck'].sum()
        df_graph = df_graph.reset_index(name = "newcheck")
        
        traces.append(go.Bar(x=df_graph[dateColumn], y=df_graph['newcheck'], text=list(df_graph['newcheck']), textposition='auto', marker_color='#34495e',name='Total Inflow'))

        df_graph = df_flow.loc[(df_flow[dateColumn] >= dc.SLIDER_DATE)]
        df_graph = df_graph.loc[(df_graph['brand'] == selectedBrand)]
        df_graph = df_graph.groupby(df_graph[dateColumn].dt.year)['churncheck'].sum()
        df_graph = df_graph.reset_index(name = "churncheck")
        traces.append(go.Bar(x=df_graph[dateColumn], y=df_graph['churncheck'], text=list(df_graph['churncheck']), textposition='auto', marker_color='#4cd137',name='Total Outflow'))
        
        layout = go.Layout(
            showlegend=True, 
            width=1000, 
            height=500,
            autosize=False,
            hovermode="closest",
            margin=dict(l=0, r=0, t=30,b=10),
            xaxis=dict(title='Date'),
            yaxis=dict( title='Total Inflow/Outflow')
        )
        return go.Figure(data=traces, layout=layout)

    # interaction function newcheck
    @pn.depends(selectedPrice = selectPriceFlow, selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotRegularInflowGraph(selectedPrice, selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
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

        layout=go.Layout()
                
        traces = []
        listOfSelections = []
        listOfName = []

        listOfSelections.append([selectedBrand])
        listOfName.append('brand')
        if 'Select All' in selectedSubscr_Type:
            listOfSelections.append(list(df_flow['subscr_type'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedSubscr_Type)
            listOfName.append('subscr_type')
        if 'Select All' in selectedPrice:
            listOfSelections.append(list(df_flow['pricecat'].unique()))
            listOfName.append('pricecat')
        else:
            listOfSelections.append(selectedPrice)
            listOfName.append('pricecat')

        listOfSelections.append(['newcheck'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0]) 
                        & (df_flow['subscr_type'] == combs[1])
                        & (df_flow['pricecat'] == combs[2])]
            rename = combs[3]
            if combs[3] in renameGraph:
                rename = renameGraph[combs[3]]

            traces.append(go.Scatter(x=df_graph[dateColumn], y=df_graph[combs[3]], mode='lines',  name=combs[1]+' '+combs[2]+'<br> Actual'))
            traces.append(go.Scatter(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[3]], mode='lines', name=combs[1]+' '+combs[2]+'<br> Forecasted'))
            
            # Create layout for graph
            layout = go.Layout(
                title="Regular Inflow",
                showlegend=True, 
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                width=800, 
                height=500,
                autosize=False,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Regular Inflow')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedPrice = selectPriceFlow, selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotRegularOutflowGraph(selectedPrice, selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
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
        if 'Select All' in selectedPrice or selectedPrice == []:
            listOfSelections.append(list(df_flow['pricecat'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedPrice)
            listOfName.append('pricecat')

        listOfSelections.append(['churncheck'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0])
                        & (df_flow['subscr_type'] == combs[1])
                        & (df_flow['pricecat'] == combs[2])]
                        #& (df_flow['print'] ==  combs[3])]
            
            rename = combs[3]
            if combs[3] in renameGraph:
                rename = renameGraph[combs[3]]

            traces.append(go.Scatter(x=df_graph[dateColumn], y=df_graph[combs[3]], mode='lines', name=combs[1]+' '+combs[2]+'<br>Actual'))
            traces.append(go.Scatter(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[3]], mode='lines', name=combs[1]+' '+combs[2]+'<br>Forecasted'))
            
            # Create layout for graph
            layout = go.Layout(
                title="Regular Outflow",
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=800, 
                height=500,
                autosize=False,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Regular Outflow')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedPrice = selectPriceFlow, selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotSubscribersGraph(selectedPrice, selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
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
        if 'Select All' in selectedPrice or selectedPrice == []:
            listOfSelections.append(list(df_flow['pricecat'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedPrice)
            listOfName.append('pricecat')

        listOfSelections.append(['currentcheck'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0]) 
                        & (df_flow['subscr_type'] == combs[1])
                        & (df_flow['pricecat'] == combs[2])]
                        #& (df_flow['print'] ==  combs[3])]
            
            rename = combs[3]
            if combs[3] in renameGraph:
                rename = renameGraph[combs[3]]
            
            traces.append(go.Scatter(x=df_graph[dateColumn], y=df_graph[combs[3]], mode='lines', name=combs[1]+' '+combs[2]+'<br> Actual'))
            traces.append(go.Scatter(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[3]], mode='lines', name=combs[1]+'_'+combs[2]+'<br> Forecasted'))
            
            # Create layout for graph
            layout = go.Layout(
                title=rename.capitalize(),
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=800, 
                height=500,
                autosize=False,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Active Subscribers')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedPrice = selectPriceFlow, selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotTransformersGraph(selectedPrice, selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
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
        if 'Select All' in selectedPrice or selectedPrice == []:
            listOfSelections.append(list(df_flow['pricecat'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedPrice)
            listOfName.append('pricecat')
        listOfSelections.append(['inflow_transformers'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0])  
                        & (df_flow['subscr_type'] == combs[1])
                        & (df_flow['pricecat'] == combs[2])]

            rename = combs[3]
            if combs[3] in renameGraph:
                rename = renameGraph[combs[3]]
                
            traces.append(go.Scatter(x=df_graph[dateColumn], y=df_graph[combs[3]], mode='lines', name=combs[1]+'_'+combs[2]+'<br> Actual'))
            traces.append(go.Scatter(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[3]], mode='lines',  name=combs[1]+'_'+combs[2]+'<br> Forecasted'))

            # Create layout for graph
            layout = go.Layout(
                title=rename.capitalize(),
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=800, 
                height=500,
                autosize=False,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Transformers Inflow')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedPrice = selectPriceFlow, selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotTransformersOutflowGraph(selectedPrice, selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
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
        if 'Select All' in selectedPrice or selectedPrice == []:
            listOfSelections.append(list(df_flow['pricecat'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedPrice)
            listOfName.append('pricecat')
        listOfSelections.append(['trans_outflow'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0])  
                        & (df_flow['subscr_type'] == combs[1])
                        & (df_flow['pricecat'] == combs[2])]
                        #& (df_flow['print'] ==  combs[3])]
            rename = combs[3]
            if combs[3] in renameGraph:
                rename = renameGraph[combs[3]]
                
            traces.append(go.Scatter(x=df_graph[dateColumn], y=df_graph[combs[3]], mode='lines',  name=combs[1]+'_'+combs[2]+'<br> Actual'))
            traces.append(go.Scatter(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[3]], mode='lines',  name=combs[1]+'_'+combs[2]+'<br> Forecasted'))

            # Create layout for graph
            layout = go.Layout(
                title=rename.capitalize(),
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=800, 
                height=500,
                autosize=False,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Transformers Outflow')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedPrice = selectPriceFlow, selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotSwitchersGraph(selectedPrice, selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
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
        if 'Select All' in selectedPrice or selectedPrice == []:
            listOfSelections.append(list(df_flow['pricecat'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedPrice)
            listOfName.append('pricecat')
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
                        & (df_flow['subscr_type'] == combs[1])
                        & (df_flow['pricecat'] == combs[2])]
                        #& (df_flow['print'] ==  combs[3])]
            rename = combs[3]
            if combs[3] in renameGraph:
                rename = renameGraph[combs[3]]
                
            traces.append(go.Scatter(x=df_graph[dateColumn], y=df_graph[combs[3]], mode='lines', name=combs[1]+'_'+combs[2]+'<br> Actual'))
            traces.append(go.Scatter(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[3]], mode='lines', name=combs[1]+'_'+combs[2]+'<br> Forecasted'))
            
            # Create layout for graph
            layout = go.Layout(
                title=rename.capitalize(),
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=800, 
                height=500,
                autosize=True,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Switchers Inflow')
            ) 
        
        return go.Figure(data=traces, layout=layout)

    # Switchers Outflow
    @pn.depends(selectedPrice = selectPriceFlow, selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def plotSwitchersOutflowGraph(selectedPrice, selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
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
        if 'Select All' in selectedPrice or selectedPrice == []:
            listOfSelections.append(list(df_flow['pricecat'].unique()))
            listOfName.append('subscr_type')
        else:
            listOfSelections.append(selectedPrice)
            listOfName.append('pricecat')
        #listOfSelections.append([selectedPrint])
        #listOfName.append('print')
        listOfSelections.append(['switcher_outflow'])
        
        # Permutation for all combinations of dropdown
        for combs in list(itertools.product(*listOfSelections)):
            filename = ''
            for com in combs:
                filename = filename+'_'+com

            df_graph = df_flow.loc[(df_flow['brand'] == combs[0])
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0])
                        & (df_flow['subscr_type'] == combs[1])
                        & (df_flow['pricecat'] == combs[2])]
            rename = combs[3]
            if combs[3] in renameGraph:
                rename = renameGraph[combs[3]]
                
            traces.append(go.Scatter(x=df_graph[dateColumn], y=df_graph[combs[3]], mode='lines', name=combs[1]+'_'+combs[2]+'<br> Actual'))
            traces.append(go.Scatter(x=df_graph[df_graph['forecast'] == 1][dateColumn], y=df_graph[df_graph['forecast'] == 1][combs[3]], mode='lines', name=combs[1]+'_'+combs[2]+'<br> Forecasted'))
            
            # Create layout for graph
            layout = go.Layout(
                title=rename.capitalize(),
                colorway=["#002540", "#6DB432", "#A79B94", "#0070F7", "#FF9A00", "#FE0089", "#DB291D", "#853B92", "#844257", "#CD9854", "#9E6F98", "#7E412E", "#048D79", "#40008B"],
                showlegend=True, 
                width=800, 
                height=500,
                autosize=True,
                margin=dict(l=0, r=0, t=30,b=10),
                xaxis=dict(title='Date'),
                yaxis=dict(title='Switchers Outflow')
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
                    selectBrandFlow
                ),
                pn.Column(
                    selectPriceFlow,
                ),
                pn.Column(
                    selectSubscr_TypeFlow
                )
            ),
            pn.Column(
                pn.Row(
                    pn.panel(plotTotalGraph),
                ),
                pn.Row(
                    pn.panel(plotRegularInflowGraph),
                    pn.Spacer(),
                    pn.panel(plotRegularOutflowGraph)
                ),
                pn.Row(
                    pn.panel(plotTransformersGraph),
                    pn.Spacer(),
                    pn.panel(plotTransformersOutflowGraph)
                ),
                pn.Row(
                    pn.panel(plotSwitchersGraph),
                    pn.Spacer(),
                    pn.panel(plotSwitchersOutflowGraph)
                ),
                pn.Row(
                    pn.panel(plotSubscribersGraph)
                )
            ),
            css_classes=['tabFlow'],
        )