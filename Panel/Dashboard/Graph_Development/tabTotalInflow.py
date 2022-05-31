import pandas as pd
import panel as pn
import os, tornado
import plotly.graph_objs as go
import datetime as dt
import csv
import numpy as np

import dashboard_constants as dc

currentDir = os.path.join(os.getcwd(),'data')
dateColumn = 'Date'

def mainFun():
    uname = tornado.escape.json_decode(pn.state.cookies['user'])
    print("hii from total inflow")
    # Get all the dataset from csv file
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

    renameGraph = {
        'newcheck': 'Regular Inflow',
        'currentcheck': 'Active Subscribers',
        'inflow_transformers': 'Transformers Inflow',
        'inflow_switchers': 'Switchers Inflow'
    }

    df_flow.rename(columns=renameGraph, inplace=True)

    #Dynamically get all the fields according to its types
    flowType = ['Select All']
    for i in df_flow.columns:
        if df_flow[i].dtype == 'int64' and i.lower().find('inflow') > -1:
            flowType.append(i)
        if df_flow[i].dtype == 'float64' and i.lower().find('inflow') > -1:
            flowType.append(i)

    # Drop-downs for different variables for flow tab
    selectBrandFlow = pn.widgets.Select(name='Brand', options=list(df_flow['brand'].unique()), value='DS')
    #selectPrintFlow = pn.widgets.Select(name='Print', options=list(df_flow['print'].unique()), value=df_flow['print'][0])
    selectSubscr_TypeFlow = pn.widgets.Select(name='Package Type', options=list(df_flow['subscr_type'].unique()), value=df_flow['subscr_type'][0])
    selectPriceFlow = pn.widgets.Select(name='Price Category', options=list(df_flow['pricecat'].unique()), value=df_flow['pricecat'][0])
    selectFlowType = pn.widgets.MultiChoice(name='Flow Type', options=flowType, value=[flowType[0]], solid=False)
    selectStartDate = pn.widgets.DiscreteSlider(name='Select Start Date', options=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique()), value=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique())[0])
    selectEndDate = pn.widgets.DiscreteSlider(name='Select End Date', options=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique()), value=list(df_flow[df_flow[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique())[-1])
    
    # Buttons
    #downloadButton = pn.widgets.Button(name='Download as CSV', button_type='primary', width=250)
    from .main_dev import dummySlider

    # Titles
    title = 'PANEL Dashboard - SUBSCRIBER - INFLOW'

    # declaration of bootstrap
    bootstrap = pn.template.BootstrapTemplate(title=title)

    download_table_df = pd.DataFrame()
    tableFileName = ''

    @pn.depends(selectedPrice = selectPriceFlow, selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, selectedFlowType = selectFlowType, dSlider = dummySlider)
    def flowTotalTable(selectedPrice, selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, selectedFlowType, dSlider):
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
        df_flow.rename(columns=renameGraph, inplace=True)

        table_df_flow = df_flow.loc[(df_flow['brand'] == selectedBrand)
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow['subscr_type'] == selectedSubscr_Type)
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0])
                        & (df_flow['pricecat'] == selectedPrice)]
        
        del table_df_flow['forecast']

        table_df = pd.DataFrame()

        selectedFlowType_dup = selectedFlowType
        if selectedFlowType == []:
            selectFlowType.value = [flowType[0]]
        if 'Select All' in selectedFlowType:
            selectedFlowType_dup = flowType.copy()
            selectedFlowType_dup.remove('Select All')

        selectedFlowType_dup.append('Active Subscribers')
        
        for i in selectedFlowType_dup:
            if table_df.empty:
                table_df = table_df_flow.groupby(table_df_flow[dateColumn].dt.to_period('M'))[i].sum().reset_index()
            else:
                newCol = table_df_flow.groupby(table_df_flow[dateColumn].dt.to_period('M'))[i].sum().reset_index()[i]
                table_df.insert(len(table_df.columns), i, newCol, True) 
        if table_df.empty:
            return
        table_df[dateColumn] = table_df[dateColumn].astype(str)
        
        download_table_df = table_df.copy()
        tableFileName = selectedBrand+'_'+selectedSubscr_Type+'_'+selectedPrice+'.csv'
        colName = []
        
        # capitalize the column names
        for i in table_df.columns:
            if i.find('_') != -1:
                val = '<b>'
                for j in i.split('_'):
                    val = val+j.capitalize()+'<br>'
                colName.append(val+'</b>')
            else:
                colName.append('<b>'+i.capitalize()+'</b>')
        # print("colName: ",colName)
        data = go.Table(
            columnwidth=[1,1],
            header=dict(
                    values=colName,
                    line_color='darkslategray',
                    fill_color='lightskyblue',
                    font_size=12,
                    height=30,
                    align=['center', 'center'],
            ), 
            cells=dict(values= [table_df[val] for val in table_df.columns],
                    line_color='darkslategray',
                    fill_color='lightcyan',
                    font_size=12,
                    height=30
            )
        )
        layout = go.Layout(
            width=1200, 
            height=600,
            margin=dict(l=10, r=0, t=30,b=10),
        )
        return go.Figure(data=data, layout=layout) 

    @pn.depends(selectedPrice = selectPriceFlow, selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, selectedFlowType = selectFlowType, dSlider = dummySlider)
    def flowTotalGraph(selectedPrice, selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, selectedFlowType, dSlider):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        traces = []
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
        df_flow.rename(columns=renameGraph, inplace=True)

        table_df_flow = df_flow.loc[(df_flow['brand'] == selectedBrand)
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow['subscr_type'] == selectedSubscr_Type)
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0])
                        & (df_flow['pricecat'] == selectedPrice)]
        
        del table_df_flow['forecast']

        table_df = pd.DataFrame()

        selectedFlowType_dup = selectedFlowType

        if 'Select All' in selectedFlowType:
            selectedFlowType_dup = flowType.copy()
            selectedFlowType_dup.remove('Select All')
        
        for i in selectedFlowType_dup:
            if table_df.empty:
                table_df = table_df_flow.groupby(table_df_flow[dateColumn].dt.to_period('M'))[i].sum().reset_index()
            else:
                newCol = table_df_flow.groupby(table_df_flow[dateColumn].dt.to_period('M'))[i].sum().reset_index()[i]
                table_df.insert(len(table_df.columns), i, newCol, True) 
        if table_df.empty:
            return 
        table_df[dateColumn] = table_df[dateColumn].astype(str)
        
        for i in selectedFlowType_dup:
            print(i, "got here")
            rename = i
            if i in renameGraph:
                rename = renameGraph[i]
            traces.append(go.Bar(x=table_df[dateColumn], y=table_df[i], text=list(table_df[i]), textposition='auto', name=rename))

        layout = go.Layout(
            showlegend=True, 
            width=1300, 
            height=500,
            autosize=False,
            margin=dict(l=0, r=0, t=30, b=10),
            barmode='stack',
            xaxis=dict(title='Date'),
            yaxis=dict( title='Total Regular Inflow')
        )
        
        return go.Figure(data=traces, layout=layout)
        
    @pn.depends(selectedPrice = selectPriceFlow, selectedBrand = selectBrandFlow, selectedSubscr_Type = selectSubscr_TypeFlow, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, dSlider = dummySlider)
    def flowTotalGraphCurrent(selectedPrice, selectedSubscr_Type, selectedBrand, selectedStartDate, selectedEndDate, dSlider):
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
        df_flow.rename(columns=renameGraph, inplace=True)
        
        table_df_flow = df_flow.loc[(df_flow['brand'] == selectedBrand)
                        & (df_flow[dateColumn] >= list(df_flow[df_flow['mon_year'] == selectedStartDate][dateColumn])[0])
                        & (df_flow['subscr_type'] == selectedSubscr_Type)
                        & (df_flow[dateColumn] <= list(df_flow[df_flow['mon_year'] == selectedEndDate][dateColumn])[0])
                        & (df_flow['pricecat'] == selectedPrice)]
        
        table_df = pd.DataFrame()
        
        if table_df.empty:
            table_df = table_df_flow.groupby(table_df_flow[dateColumn].dt.to_period('M'))['Active Subscribers'].sum().reset_index()
        else:
            newCol = table_df_flow.groupby(table_df_flow[dateColumn].dt.to_period('M'))['Active Subscribers'].sum().reset_index()['Active Subscribers']

            table_df.insert(len(table_df.columns), 'Active Subscribers', newCol, True) 
        if table_df.empty:
            return 
        table_df[dateColumn] = table_df[dateColumn].astype(str)
        traces = []
        
        traces.append(go.Bar(x=table_df[dateColumn], y=table_df['Active Subscribers'], text=list(table_df['Active Subscribers']), textposition='auto', name='Active Subscribers'))

        layout = go.Layout(
            showlegend=True, 
            width=1300, 
            height=500,
            autosize=False,
            margin=dict(l=0, r=0, t=30,b=10),
            barmode='stack',
            xaxis=dict(title='Date'),
            yaxis=dict( title='Total Active Subscribers')
        )
        
        return go.Figure(data=traces, layout=layout)
        
    # function for click event to download file
    from io import StringIO
    def downloadFile():
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        renameGraph = {
        'churncheck': 'Regular Outflow',
        'newcheck': 'Regular Inflow',
        'currentcheck': 'Active Subscribers',
        }
        try:
            df_flow = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_flow = pd.read_csv(os.path.join(currentDir, 'switchtransfinal_with_forecast.csv'), sep=';')

        # convert string to datetime format
        df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)

        df_flow = df_flow.fillna(0)  
        table_df = df_flow.round(2) 
        table_df.rename(columns=renameGraph, inplace=True)

        # table_df = df_flow.loc[(df_flow['forecast'] == 1)]
        
        del table_df['forecast']

        table_df[dateColumn] = table_df[dateColumn].astype(str)
        
        sample_df = pd.DataFrame(table_df)
        sio = StringIO()
        sample_df.to_csv(sio,sep=";",index=False)
        sio.seek(0)
        return sio

    # function call for download csv
    #downloadButton.on_click(downloadFile)
    downloadButton = pn.widgets.FileDownload(callback=downloadFile, button_type="primary", label="Download as CSV", filename="Subscriber_overview.csv")
    
    #pn.config.sizing_mode = 'stretch_width'

    return  pn.Column(
            pn.Row(
                pn.Column(
                    selectStartDate,
                    selectEndDate
                ),
                pn.Column(
                    selectBrandFlow,
                    #selectPrintFlow,
                ),
                pn.Column(
                    selectPriceFlow,
                    selectSubscr_TypeFlow
                ),
                pn.Column(
                    selectFlowType
                )
            ),
            pn.Row(
                downloadButton
            ),
            pn.Column(
                pn.Row(
                    flowTotalGraph
                ),
                pn.Row(
                    flowTotalGraphCurrent
                ),
                flowTotalTable
            )
        )
