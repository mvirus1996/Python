import panel as pn
import plotly.graph_objs as go
import pandas as pd
import os, pickle, tornado
from bokeh.models import ColumnDataSource, TableColumn, DateFormatter, DataTable

from Models import predict_model
import constants as c
import dashboard_constants as dc



Actual_Begin_Date = dc.ACTUAL_BEGIN_DATE
Actual_End_Date = dc.ACTUAL_END_DATE
uname = tornado.escape.json_decode(pn.state.cookies['user'])
previousDummyValue = 0

def mainFunCluster():
    global checkMultipleChange

    uname = tornado.escape.json_decode(pn.state.cookies['user'])
    currentDir = c.CURRENT_DIR
    dateColumn = 'Date'

    checkMultipleChange = 0
    print("uanme in inflow: ",uname)

    df_final_static = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

    df_cluster = pd.read_csv(os.path.join(currentDir, 'data', 'User Data', uname+'_active.csv'), error_bad_lines=False, sep=';')
    df_cluster2 = pd.read_csv(os.path.join(currentDir, 'data', 'CampagnesCountClusteredPerMonth.csv'), sep=';')

    df_cluster = df_cluster.fillna(0) 
    df_cluster['active'] = df_cluster['active'].astype(int)

    df_cluster2 = df_cluster2.fillna(0)  

    # convert string to datetime format
    df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn])
    df_cluster2[dateColumn] = pd.to_datetime(df_cluster2[dateColumn]).dt.tz_localize(None)


    # create a new column for selectIntegrityDate date-slider
    mon_year = df_cluster[dateColumn].dt.strftime('%b-%Y')
    df_cluster.insert(1, 'mon_year', mon_year)
    df_cluster = df_cluster.sort_values(by=dateColumn)

    listKanaal = ['Select All']
    for i in list(df_cluster['KanaalType'].unique()):
        listKanaal.append(i)

    listCluster = ['Select All']
    for i in list(df_cluster['Actie_Type'].unique()):
        listCluster.append(i)

    # Drop-downs for different variables for flow tab
    selectBrand = pn.widgets.Select(name='Brand', options=list(df_cluster['brand'].unique()), value='DS')
    selectPackage = pn.widgets.Select(name='Package Type', options=list(df_cluster['packagetype'].unique()), value='ZADI')
    selectPrijsType = pn.widgets.Select(name='Prijs Type', options=list(df_cluster['prijstype'].unique()), value='STUNT')
    selectCombination = pn.widgets.Select(name='Inflow Channel', options=listKanaal, value='Select All')
    selectCluster = pn.widgets.Select(name='Campaign Type', options=listCluster, value='Select All')

    selectDummySlider = pn.widgets.IntSlider(name='Dummy Slider', start=0, end=100, step=1)

    selectStartDate = pn.widgets.DiscreteSlider(name='Select Start Date', options=list(df_cluster['mon_year'].unique()), value=list(df_cluster[df_cluster[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique())[0])
    selectEndDate = pn.widgets.DiscreteSlider(name='Select End Date', options=list(df_cluster['mon_year'].unique()), value=list(df_cluster[df_cluster[dateColumn] >= dc.SLIDER_DATE]['mon_year'].unique())[-1])
    
    # Global variables
    source = ColumnDataSource(df_cluster)
    
    stunt_regular_inflow: any
    stunt_regular_outflow: any
    stunt_trans_outflow: any
    stunt_switch_outflow: any
    promo_predict_inflow_trans: any

    #################################################################


    submit = pn.widgets.Button(name='Submit', button_type='primary', width=250)
    uname = tornado.escape.json_decode(pn.state.cookies['user'])

    from .main_dev import dummySlider, activeDFSlider

    @pn.depends(selectedBrand = selectBrand, selectedPackage = selectPackage,  selectedCombination = selectCombination, selectedPrijsType = selectPrijsType, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, selectedCluster = selectCluster, aSlider = activeDFSlider)
    def createTable(selectedBrand, selectedPackage, selectedPrijsType, selectedStartDate, selectedEndDate, selectedCombination, selectedCluster, aSlider):
		
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        df_cluster = pd.read_csv(os.path.join(currentDir, 'data', 'User Data', uname+'_active.csv'), error_bad_lines=False, sep=';')
        df_cluster = df_cluster.fillna(0) 
        df_cluster['active'] = df_cluster['active'].astype(int)
        df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn]) 
        mon_year = df_cluster[dateColumn].dt.strftime('%b-%Y')
        df_cluster.insert(1, 'mon_year', mon_year)        
        
        global source
        dup_df_cluster = df_cluster.copy()
        
        if selectedCombination == 'Select All':
            selectedCombination = list(df_cluster['KanaalType'].unique())
        else:
            selectedCombination = [selectedCombination]
        if selectedCluster == 'Select All':
            selectedCluster = list(df_cluster['Actie_Type'].unique())
        else:
            selectedCluster = [selectedCluster]
        dup_df_cluster = dup_df_cluster[(dup_df_cluster['brand'] == selectedBrand)
                                        & (dup_df_cluster['packagetype'] == selectedPackage)
                                        & (dup_df_cluster['prijstype'] == selectedPrijsType)
                                        & (dup_df_cluster['KanaalType'].isin(selectedCombination))
                                        & (dup_df_cluster['Actie_Type'].isin(selectedCluster))
                                        & (dup_df_cluster[dateColumn] >= list(df_cluster[df_cluster['mon_year'] == selectedStartDate][dateColumn])[0])
                                        & (dup_df_cluster[dateColumn] <= list(df_cluster[df_cluster['mon_year'] == selectedEndDate][dateColumn])[0])]
        dup_df_cluster = dup_df_cluster.sort_values(by=[dateColumn, "inflow"])
        
        source = ColumnDataSource(dup_df_cluster)

        columns = [TableColumn(field = "Date", title = "Date",
            formatter = DateFormatter()),
            TableColumn(field = 'brand', title = 'Brand'),
            TableColumn(field = 'packagetype', title = 'Package Type'),
            TableColumn(field = 'KanaalType', title = 'Kanaal'),
            TableColumn(field = 'Actie_Type', title = 'Campaign Type'),
            TableColumn(field = 'clusters', title = 'Size'),
            TableColumn(field = 'inflow', title = '#Instroom')]

        data_table = DataTable(source = source, columns = columns, width = 1200, height = 350, editable = False, selectable="checkbox", row_height=45, min_width=45)
        
        source.selected.indices  = [i for i, n in enumerate(dup_df_cluster['active']) if n == 1]
        return data_table

    @pn.depends(selectedBrand = selectBrand, selectedPackage = selectPackage, selectedPrijsType = selectPrijsType, selectedDummySlider = selectDummySlider, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, selectedCluster = selectCluster, selectedCombination = selectCombination, aSlider = activeDFSlider)
    def createGraphInflow(selectedBrand, selectedPackage, selectedPrijsType, selectedDummySlider, selectedStartDate, selectedEndDate, selectedCluster, selectedCombination, aSlider):
		
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        df_cluster = pd.read_csv(os.path.join(currentDir, 'data', 'User Data', uname+'_active.csv'), error_bad_lines=False, sep=';')
        df_cluster = df_cluster.fillna(0) 
        df_cluster['active'] = df_cluster['active'].astype(int)
        df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn])
        mon_year = df_cluster[dateColumn].dt.strftime('%b-%Y')
        df_cluster.insert(1, 'mon_year', mon_year)
        df_cluster = df_cluster.sort_values(by=[dateColumn, "inflow"])
        
        global previousDummyValue
        global source
        
        traces = []

        startDate = list(df_cluster[df_cluster['mon_year'] == selectedStartDate][dateColumn])[0]
        endDate = list(df_cluster[df_cluster['mon_year'] == selectedEndDate][dateColumn])[0] 
        
        if previousDummyValue != selectedDummySlider:
            previousDummyValue = selectedDummySlider
            
            dup_df_cluster = df_cluster.copy()
            if selectedCombination == 'Select All':
                selectedCombination = list(df_cluster['KanaalType'].unique())
            else:
                selectedCombination = [selectedCombination]
            if selectedCluster == 'Select All':
                selectedCluster = list(df_cluster['Actie_Type'].unique())
            else:
                selectedCluster = [selectedCluster]
            dup_df_cluster = dup_df_cluster[(dup_df_cluster['brand'] == selectedBrand)
                                            & (dup_df_cluster['packagetype'] == selectedPackage)
                                            & (dup_df_cluster['prijstype'] == selectedPrijsType)
                                            & (dup_df_cluster['Actie_Type'].isin(selectedCluster))
                                            & (dup_df_cluster[dateColumn] >= list(dup_df_cluster[dup_df_cluster['mon_year'] == selectedStartDate][dateColumn])[0])
                                            & (dup_df_cluster[dateColumn] <= list(dup_df_cluster[dup_df_cluster['mon_year'] == selectedEndDate][dateColumn])[0])]

            dup_df_cluster_group = dup_df_cluster.copy()
            
            dup_df_cluster_group = dup_df_cluster_group.sort_values(by=[dateColumn, "inflow"])
            
            dup_df_cluster_group.reset_index(inplace=True)

            dup_df_cluster_group['active'] = 0
            df_cluster.loc[dup_df_cluster_group['index'], 'active'] = 0
            
            for i in source.selected.indices[:]:
                dup_df_cluster_group.loc[i, 'active'] = 1
                df_cluster.loc[dup_df_cluster_group.loc[i]['index'], 'active'] = 1
            df_cluster_dup = df_cluster.copy()
            del df_cluster_dup['mon_year']
            ACTIVE_PATH = os.path.join(currentDir, 'data', 'User Data', uname+'_active.csv')
            df_cluster_dup.to_csv(ACTIVE_PATH, index=False, sep=';')
            
            # New Code for on-the-fly forecast
            output_csv = predict_model.model_predict(brand=selectedBrand,
                                                    sub_type=selectedPackage,
                                                    # full_actuals=True,
                                                    campaigns_active_path=ACTIVE_PATH)
            
            output_csv = output_csv.fillna(0)
            output_csv =  output_csv.loc[(output_csv['brand'] == selectedBrand)
                            & (output_csv['subscr_type'] == selectedPackage)
                            # & (output_csv['pricecat'] == selectedPrijsType)
                            & (output_csv['forecast'] == 1)
                            & (output_csv[dateColumn] >= startDate)
                            & (output_csv[dateColumn] <= endDate)]

            output_csv[dateColumn] = pd.to_datetime(output_csv[dateColumn])
            
            df_flow = pd.read_csv(os.path.join(currentDir, 'data', 'User Data', uname+'.csv'), sep=';')
            df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn])
            for _, row in output_csv.iterrows():
                val = df_flow.loc[(df_flow['Date'] == row['Date'])
                                &(df_flow['brand'] == row['brand'])
                                &(df_flow['pricecat'] == row['pricecat'])
                                &(df_flow['subscr_type'] == row['subscr_type'])
                                &(df_flow['forecast'] == 1)]
                val = val.reset_index()['index']
                for i in ['brand','print','subscr_type','Date','pricecat','newcheck','churncheck','switcher_outflow','trans_outflow','inflow_transformers','inflow_switchers','currentcheck','forecast','nettosaldo','churnpercentage']:
                    df_flow.loc[val, i] = row[i]
            
            df_flow.to_csv(os.path.join(currentDir, 'data', 'User Data', uname+'.csv'), index=False, sep=';')
            df_properties = pd.read_csv(os.path.join(currentDir, 'data', 'User Data', uname+'_data.csv'), sep=';')
            
            try:
                val = df_properties.loc[(df_properties['Brand'] == selectedBrand)
                                        &(df_properties['Package'] == selectedPackage)
                                        &(df_properties['Prijs'] == selectedPrijsType)]
                val = val.reset_index()['index']
                df_properties.loc[val, 'Multiplier'] = 1
                df_properties.to_csv(os.path.join(currentDir, 'data', 'User Data', uname+'_data.csv'), index=False, sep=';')
            except Exception as e:
                print('cluster inflow property set', e)

            dummySlider.value += 1
            
        df_flow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

        df_flow = df_flow.fillna(0)
        df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn], dayfirst=True)
        df_flow.loc[(df_flow['Date']>=c.TRAIN_BEGIN_DATE) & (df_flow['Date']<=c.TRAIN_END_DATE), 'forecast']=0
        df_flow.loc[(df_flow['Date']>=c.FORECAST_BEGIN_DATE) & (df_flow['Date']<=c.FORECAST_END_DATE), 'forecast']=1
    
        dup_df_cluster_forecasted = df_flow.loc[(df_flow['brand'] == selectedBrand)
                    & (df_flow['subscr_type'] == selectedPackage)
                    & (df_flow['pricecat'] == selectedPrijsType)                                
                    & (df_flow[dateColumn] >= startDate)
                    & (df_flow[dateColumn] <= endDate)] 
        
        dup_df_cluster_actual = df_flow.loc[(df_flow['brand'] == selectedBrand)
                    & (df_flow['subscr_type'] == selectedPackage)
                    & (df_flow['pricecat'] == selectedPrijsType)                                  
                    & (df_flow['forecast'] ==  0)]
        dup_df_cluster_actual = dup_df_cluster_actual.loc[(dup_df_cluster_actual[dateColumn] >= Actual_Begin_Date)]
        traces.append(go.Scatter(x=dup_df_cluster_actual[dateColumn], y=dup_df_cluster_actual['newcheck'], mode='lines', marker_color='#34495e', name='Actual'))
        
        try:
            df_graph = pd.read_csv(os.path.join(currentDir, 'data', 'User Data', uname+'.csv'), sep=';')
            df_graph[dateColumn] = pd.to_datetime(df_graph[dateColumn])
            df_graph = df_graph.loc[(df_graph['brand'] == selectedBrand)
                    & (df_graph['subscr_type'] == selectedPackage)
                    & (df_graph['pricecat'] == selectedPrijsType)
                    & (df_graph['forecast'] == 1)
                    & (df_graph[dateColumn] >= startDate)
                    & (df_graph[dateColumn] <= endDate)]
            traces.append(go.Scatter(x=df_graph[dateColumn], y=df_graph['newcheck'], mode='lines', marker_color='#e84393', name='Adjusted'))
            
        except:
            print('no data') 
        traces.append(go.Scatter(x=dup_df_cluster_forecasted[dateColumn], y=dup_df_cluster_forecasted['newcheck'], mode='lines', marker_color='#2ecc71', name='Forecasted'))
        # Create layout for graph
        layout = go.Layout(
            showlegend=True, 
            width=1200, 
            height=500,
            autosize=False,
            margin=dict(l=0, r=0, t=30,b=10),
            xaxis=dict(title='Date'),
            yaxis=dict(title='Regular Inflow')
        ) 
        return go.Figure(data=traces, layout=layout)


    @pn.depends(selectedBrand = selectBrand, selectedPackage = selectPackage, selectedPrijsType = selectPrijsType, selectedDummySlider = selectDummySlider, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, selectedCombination = selectCombination, selectedCluster = selectCluster, dSlider = dummySlider)
    def createGraphOutflow(selectedBrand, selectedPackage, selectedPrijsType, selectedDummySlider, selectedStartDate, selectedEndDate, selectedCombination, selectedCluster, dSlider):
        
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        traces = []
        df_final_global = pd.read_csv(c.FORECAST_FILEPATH, sep=';')
        df_final_global[dateColumn] = pd.to_datetime(df_final_global[dateColumn], dayfirst=True)
        
        mon_year = df_final_global[dateColumn].dt.strftime('%b-%Y')
        df_final_global.insert(1, 'mon_year', mon_year)

        startDate = list(df_final_global[df_final_global['mon_year'] == selectedStartDate][dateColumn])[0]
        endDate = list(df_final_global[df_final_global['mon_year'] == selectedEndDate][dateColumn])[0]

        df_final_globalset = df_final_global.loc[(df_final_global['brand'] == selectedBrand)
                    & (df_final_global['subscr_type'] == selectedPackage)
                    & (df_final_global['pricecat'] == selectedPrijsType)
                    & (df_final_global[dateColumn] >= startDate)
                    & (df_final_global[dateColumn] <= endDate)]

        try: 
            df_flow = pd.read_csv(os.path.join(currentDir, 'data', 'User Data', uname+'.csv'), sep=';')
            df_flow = df_flow.fillna(0)
            df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn])
            df_flow = df_flow[(df_flow['brand'] == selectedBrand)
                    & (df_flow['subscr_type'] == selectedPackage)
                    & (df_flow['pricecat'] == selectedPrijsType)
                    & (df_flow['forecast'] ==  1)                                    
                    & (df_flow[dateColumn] >= startDate)
                    & (df_flow[dateColumn] <= endDate)]
            traces.append(go.Scatter(x=df_flow[dateColumn], y=df_flow['churncheck'], mode='lines', marker_color='#e84393', name='Adjusted'))
        except:
            pass
        traces.append(go.Scatter(x=df_final_globalset[df_final_globalset['forecast']==1][dateColumn], y=df_final_globalset[df_final_globalset['forecast']==1]['churncheck'], mode='lines', marker_color='#2ecc71', name='Forecasted'))
        # Create layout for graph
        layout = go.Layout(
            showlegend=True, 
            width=900, 
            height=500,
            autosize=False,
            margin=dict(l=0, r=0, t=30,b=10),
            xaxis=dict(title='Date'),
            yaxis=dict(title='Regular Outflow')
        ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedBrand = selectBrand, selectedPackage = selectPackage, selectedPrijsType = selectPrijsType, selectedDummySlider = selectDummySlider, selectedStartDate = selectStartDate, selectedEndDate = selectEndDate, selectedCombination = selectCombination, selectedCluster = selectCluster, dSlider = dummySlider)
    def createTableTotal(selectedBrand, selectedPackage, selectedPrijsType, selectedDummySlider, selectedStartDate, selectedEndDate, selectedCombination, selectedCluster, dSlider):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        global previousDummyValue
        
        df_clusterTotal = pd.read_csv(c.FORECAST_FILEPATH, sep=';')
        df_clusterSum = df_clusterTotal[df_clusterTotal['forecast'] == 1]
        df_clusterSum[dateColumn] = pd.to_datetime(df_clusterSum[dateColumn])
        mon_year = df_clusterSum[dateColumn].dt.strftime('%b-%Y')
        df_clusterSum.insert(1, 'mon_year', mon_year)

        startDate = list(df_cluster[df_cluster['mon_year'] == selectedStartDate][dateColumn])[0]
        endDate = list(df_cluster[df_cluster['mon_year'] == selectedEndDate][dateColumn])[0]

        df_clusterSum = df_clusterSum.loc[(df_clusterSum['brand'] == selectedBrand)
                    & (df_clusterSum['pricecat'] == selectedPrijsType)
                    & (df_clusterSum['subscr_type'] == selectedPackage)                                   
                    & (df_clusterSum[dateColumn] >= startDate)
                    & (df_clusterSum[dateColumn] <= endDate)]

        df_clusterSum = df_clusterSum[["Date","brand","subscr_type","pricecat","newcheck","churncheck","currentcheck",
                                            "switcher_outflow","trans_outflow","inflow_switchers",
                                            "inflow_transformers"]]
        try: 
            df_flow = pd.read_csv(os.path.join(currentDir, 'data', 'User Data', uname+'.csv'), sep=';')
            df_flow = df_flow.fillna(0)
            df_flow['newcheck'] = df_flow['newcheck'].astype(int)
            df_flow['currentcheck'] = df_flow['currentcheck'].astype(int)
            df_flow['churncheck'] = df_flow['churncheck'].astype(int)
            df_flow[dateColumn] = pd.to_datetime(df_flow[dateColumn])
            df_clusterSum = df_flow.loc[(df_flow['brand'] == selectedBrand)
                    & (df_flow['pricecat'] == selectedPrijsType)
                    & (df_flow['subscr_type'] == selectedPackage)
                    & (df_flow['forecast'] == 1)]
        except:
            pass

        
        df_clusterSum[dateColumn] = df_clusterSum[dateColumn].astype(str)
        
        source = ColumnDataSource(df_clusterSum)

        columns = [
            TableColumn(field = 'Date', title = 'Date'),
            TableColumn(field = 'brand', title = 'Brand'),
            TableColumn(field = 'subscr_type', title = 'Package Type'),
            TableColumn(field = 'pricecat', title = 'Prijs Type'),
            TableColumn(field = 'currentcheck', title = 'Active Subscribers'),
            TableColumn(field = 'newcheck', title = 'Regular Inflow'),
            TableColumn(field = 'inflow_transformers', title = 'Transformer Inflow'),
            TableColumn(field = 'inflow_switchers', title = 'Switcher Inflow'),
            TableColumn(field = 'churncheck', title = 'Regular Outflow'),
            TableColumn(field = 'trans_outflow', title = 'Transformer Outflow'),
            TableColumn(field = 'switcher_outflow', title = 'Switcher Outflow')]
        

        data_table = DataTable(source = source, columns = columns, width=1750, height = 350, editable = False, row_height=45, min_width=45, index_position=None, fit_columns=True)
        
        return data_table

    def getChecked(event):
        global checkMultipleChange
        checkMultipleChange = 1
        
        global previousDummyValue
        if previousDummyValue == 100:
            previousDummyValue = 0
        
        selectDummySlider.value = previousDummyValue+1

    submit.on_click(getChecked)


    global bootstrap
    bootstrap = pn.Column(
        pn.Row(
            pn.Column(
                selectStartDate,
                selectEndDate
            ),
            pn.Column(
                selectBrand,
                selectCombination
            ),
            pn.Column(
                selectPackage,
                selectCluster
            ),
            selectPrijsType
        ),
        pn.Row(
            pn.Column(
                
            )
        ),
        pn.Row(
                createTable,
                submit,
                css_classes = ['cm-toggle']
        ),
        pn.Row(
                createGraphInflow,
                createGraphOutflow
        ),
        pn.Row(
            createTableTotal
        )
    )

    return bootstrap