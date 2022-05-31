import panel as pn
import plotly.graph_objs as go
import pandas as pd
import os, tornado

import dashboard_constants as dc


Actual_Begin_Date = dc.ACTUAL_BEGIN_DATE
Actual_End_Date = dc.ACTUAL_END_DATE
uname = tornado.escape.json_decode(pn.state.cookies['user'])
previousDummyValue = 0

def mainFun():
    global checkMultipleChange

    uname = tornado.escape.json_decode(pn.state.cookies['user'])
    currentDir = os.path.join(os.getcwd(),'data')
    dateColumn = 'Date'

    checkMultipleChange = 0

    try:
        df_cluster = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
    except: 
        df_cluster = pd.read_csv(os.path.join(currentDir, 'switchtransfinal_with_forecast.csv'), sep=';')
    df_cluster = df_cluster[df_cluster[dateColumn] >= dc.SLIDER_DATE]
    # convert string to datetime format
    df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn], dayfirst=True)


    df_cluster = df_cluster.fillna(0)  
    df_cluster = df_cluster.round(2) 

    # create a new column for selectIntegrityDate date-slider
    mon_year = df_cluster[dateColumn].dt.strftime('%b-%Y')
    df_cluster.insert(1, 'mon_year', mon_year)
    df_cluster = df_cluster.sort_values(by=dateColumn)
    
    listPrint = ['Select All', 'Digi', 'Print']

    listSubscr_type = ['Select All']
    for i in list(df_cluster['subscr_type'].unique()):
        listSubscr_type.append(i)

    listPricecat = ['Select All']
    for i in list(df_cluster['pricecat'].unique()):
        listPricecat.append(i)

    # Drop-downs for different variables for flow tab
    selectBrand = pn.widgets.Select(name='Brand', options=list(df_cluster['brand'].unique()), value='DS')
    selectPrint = pn.widgets.Select(name='Package Group', options=listPrint, value='Select All')
    selectSubscr_type = pn.widgets.MultiChoice(name='Package Type', options=listSubscr_type, value=['Select All'])
    selectPricecat = pn.widgets.MultiChoice(name="Price", options=listPricecat, value=['Select All'])
    selectFlow = pn.widgets.Select(name="Flows", options=['Select All', 'Inflow', 'Outflow', 'Active Subscribers'], value='Select All')
    selectStartDate = pn.widgets.DiscreteSlider(name='Select Start Date', options=list(df_cluster['mon_year'].unique()), value=list(df_cluster[df_cluster[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique())[0])
    selectEndDate = pn.widgets.DiscreteSlider(name='Select End Date', options=list(df_cluster['mon_year'].unique()), value=list(df_cluster[df_cluster[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique())[-1])
    
    from .main_dev import dummySlider

    @pn.depends(selectBrand, selectPrint, selectSubscr_type, selectPricecat, selectFlow, selectStartDate, selectEndDate, dummySlider)
    def createFirstGraph(selectedBrand, selectedPrint, selectedSubscr_type, selectedPricecat, selectedFlow, selectedStartDate, selectedEndDate, dSlider):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        try:
            df_cluster = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_cluster = pd.read_csv(os.path.join(currentDir, 'switchtransfinal_with_forecast.csv'), sep=';')
        df_cluster = df_cluster[df_cluster[dateColumn] >= dc.SLIDER_DATE]
        # convert string to datetime format
        df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn], dayfirst=True)

        df_cluster = df_cluster.fillna(0)  
        df_cluster = df_cluster.round(2) 

        # create a new column for selectIntegrityDate date-slider
        mon_year = df_cluster[dateColumn].dt.strftime('%b-%Y')
        df_cluster.insert(1, 'mon_year', mon_year)
        df_cluster = df_cluster.sort_values(by=dateColumn)
    
        dup_df_cluster = df_cluster.copy()
        listOfSelection = []
        listOfSelection.append([selectedBrand])
        listOfPrint = []
        if selectedPrint == 'Select All' or selectedPrint == []:
            listOfPrint = ['Digi', 'Print']
            extcombs = ""
        else:
            listOfPrint.append(selectedPrint)
            extcombs = selectedPrint
        listOfSubscrType = []
        if 'Select All' in selectedSubscr_type or selectedSubscr_type == []:
            listOfSubscrType = [x for x in df_cluster['subscr_type'].unique()]
        else:
            listOfSubscrType = selectedSubscr_type
        listOfPrice = []
        if 'Select All' in selectedPricecat or selectedPricecat == []:
            listOfPrice = [x for x in df_cluster['pricecat'].unique()]
        else:
            listOfPrice = selectedPricecat
        
        traces = []
        
        df_graph = dup_df_cluster[
                    (dup_df_cluster['brand'] == selectedBrand)
                    & (dup_df_cluster['print'].isin(listOfPrint))
                    & (dup_df_cluster['subscr_type'].isin(listOfSubscrType))
                    & (dup_df_cluster['pricecat'].isin(listOfPrice))
                    & (dup_df_cluster[dateColumn] >= list(dup_df_cluster[dup_df_cluster['mon_year'] == selectedStartDate][dateColumn])[0])
                    & (dup_df_cluster[dateColumn] <= list(dup_df_cluster[dup_df_cluster['mon_year'] == selectedEndDate][dateColumn])[0]) ]

        df_graph = df_graph.groupby(df_graph[dateColumn].dt.to_period('M'))['churncheck', 'newcheck', 'currentcheck'].sum().reset_index()
        df_graph = df_graph.round(2)
        df_graph[dateColumn] = df_graph[dateColumn].astype(str)
        traces.append(go.Bar(x=df_graph[dateColumn], y=df_graph['currentcheck'], text=list(df_graph['currentcheck']), textposition='auto', marker_color='#2ecc71', name=selectedBrand+" "+extcombs+" Active Subscribers"))
    
        layout = go.Layout(
            showlegend=True, 
            colorway=['#34495e', '#4cd137', '#f368e0', '#16a085', '#d35400', '#f39c12', '#8e44ad'],
            width=1800, 
            height=600,
            autosize=False,
            margin=dict(l=0, r=0, t=30,b=10),
            xaxis=dict(title='Date'),
            yaxis=dict(title='Active Subscribers')
        ) 

        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectBrand, selectSubscr_type, selectPrint, selectPricecat, selectFlow, selectStartDate, selectEndDate, dummySlider)
    def createTable(selectedBrand, selectedSubscr_type, selectedPrint, selectedPricecat, selectedFlow, selectedStartDate, selectedEndDate, dSlider):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        try:
            df_cluster = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_cluster = pd.read_csv(os.path.join(currentDir, 'switchtransfinal_with_forecast.csv'), sep=';')
        df_cluster = df_cluster[df_cluster[dateColumn] >= dc.SLIDER_DATE]
        # convert string to datetime format
        df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn], dayfirst=True)

        df_cluster = df_cluster.fillna(0)  
        df_cluster = df_cluster.round(2) 

        # create a new column for selectIntegrityDate date-slider
        mon_year = df_cluster[dateColumn].dt.strftime('%b-%Y')
        df_cluster.insert(1, 'mon_year', mon_year)
        df_cluster = df_cluster.sort_values(by=dateColumn)

        dup_df_cluster = df_cluster.copy()
        listOfSelection = []
        listOfSelection.append([selectedBrand])
        listOfPrint = []
        if selectedPrint == 'Select All' or selectedPrint == []:
            listOfPrint = ['Digi', 'Print']
        else:
            listOfPrint.append(selectedPrint)
        listOfSubscrType = []
        if 'Select All' in selectedSubscr_type or selectedSubscr_type == []:
            listOfSubscrType = [x for x in df_cluster['subscr_type'].unique()]
        else:
            listOfSubscrType = selectedSubscr_type
        listOfPrice = []
        if 'Select All' in selectedPricecat or selectedPricecat == []:
            listOfPrice = [x for x in df_cluster['pricecat'].unique()]
        else:
            listOfPrice = selectedPricecat

        df_graph = dup_df_cluster[(dup_df_cluster['brand'] == selectedBrand)
                & (dup_df_cluster['print'].isin(listOfPrint))
                & (dup_df_cluster['subscr_type'].isin(listOfSubscrType))
                & (dup_df_cluster['pricecat'].isin(listOfPrice))
                & (dup_df_cluster[dateColumn] >= list(dup_df_cluster[dup_df_cluster['mon_year'] == selectedStartDate][dateColumn])[0])
                & (dup_df_cluster[dateColumn] <= list(dup_df_cluster[dup_df_cluster['mon_year'] == selectedEndDate][dateColumn])[0])]
        
        df_graph['churncheck'] = (-1) * df_graph['churncheck']
        
        download_table_df = df_graph.copy()
        download_table_df = download_table_df.groupby(download_table_df[dateColumn].dt.to_period('M'))['churncheck', 'newcheck', 'currentcheck'].sum().reset_index()
        download_table_df = download_table_df.round(2)
        if 'Inflow' != selectedFlow and 'Select All' != selectedFlow:
            del download_table_df['newcheck']
        if 'Outflow' != selectedFlow and 'Select All' != selectedFlow:
            del download_table_df['churncheck']
        if 'Active Subscribers' != selectedFlow and 'Select All' != selectedFlow:
            del download_table_df['currentcheck']

        table_df = download_table_df
        colName = []
        renameGraph = {
        'newcheck': 'Instroom',
        'churncheck': 'Uitstroom',
        'currentcheck': 'Active Subscribers'
        }
        table_df.rename(columns=renameGraph, inplace=True)
        table_df[dateColumn] = table_df[dateColumn].astype(str)

        # capitalize the column names
        for i in table_df.columns:
            if i.find('_') != -1:
                val = '<b>'
                for j in i.split('_'):
                    val = val+j.capitalize()+'<br>'
                colName.append(val+'</b>')
            else:
                colName.append('<b>'+i.capitalize()+'</b>')
                
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
            width=1700, 
            height=600,
            margin=dict(l=10, r=0, t=30,b=10),
        )
        return go.Figure(data=data, layout=layout)
    
    # function for click event to download file
    from io import StringIO
    def downloadFile():
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        try:
            df_cluster = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_cluster = pd.read_csv(os.path.join(currentDir, 'switchtransfinal_with_forecast.csv'), sep=';')
        df_cluster = df_cluster[df_cluster[dateColumn] >= dc.SLIDER_DATE]
        # convert string to datetime format
        df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn], dayfirst=True)

        df_cluster = df_cluster.fillna(0)  
        table_df = df_cluster.round(2) 

        del table_df['forecast']
        # table_df = df_cluster[(df_cluster['forecast'] == 1)]
        
        renameGraph = {
        'churncheck': 'Regular Outflow',
        'newcheck': 'Regular Inflow',
        'currentcheck': 'Active Subscribers',
        }
        table_df.rename(columns=renameGraph, inplace=True)
        table_df[dateColumn] = table_df[dateColumn].astype(str)

        sample_df = pd.DataFrame(table_df)
        sio = StringIO()
        sample_df.to_csv(sio,sep=";",index=False)
        sio.seek(0)
        return sio

    # function call for download csv
    #downloadButton.on_click(downloadFile)
    downloadButton = pn.widgets.FileDownload(callback=downloadFile, button_type="primary", label="Download as CSV", filename="Subscriber_Overview.csv")
    

    return pn.Column(
        pn.Row(
            selectBrand,
            selectPrint,
            selectSubscr_type,
            selectPricecat,
            selectFlow
        ),
        pn.Row(
                downloadButton,
                width=250
        ),
        createFirstGraph,
        createTable
    )
