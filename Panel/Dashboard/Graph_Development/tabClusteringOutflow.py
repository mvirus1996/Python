from pandas.core.frame import DataFrame
import panel as pn
import plotly.graph_objs as go
import pandas as pd
import os, tornado
import constants as c
import dashboard_constants as dc
from Models import processing

currentDir = os.path.join(os.getcwd(),'data')
dateColumn = 'Date'

def mainFun():
    global dummySlider
    global duplicate_df_cluster
    uname = tornado.escape.json_decode(pn.state.cookies['user'])
    try:
        df_cluster = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
    except: 
        df_cluster = pd.read_csv(c.FORECAST_FILEPATH, sep=';')
    
    # convert string to datetime format
    df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn], dayfirst=True)
    df_properties = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'_data.csv'), sep=';')

    # Drop-downs for different variables for flow tab
    selectBrand = pn.widgets.Select(name='Brand', options=list(df_cluster['brand'].unique()), value=list(df_properties['Brand'])[-1])
    selectPackage = pn.widgets.Select(name='Package Type', options=list(df_cluster['subscr_type'].unique()), value=list(df_properties['Package'])[-1])
    selectPrint = pn.widgets.Select(name='Prijs Type', options=list(df_cluster['pricecat'].unique()), value=list(df_properties['Prijs'])[-1])
    
    selectIntegrity = pn.widgets.FloatSlider(name='Churn Multiplier value', start=0.1, end=3.0, step=0.05, value=list(df_properties['Multiplier'])[-1])
    
    submit= pn.widgets.Button(name='Submit', button_type='primary', width=250)
    duplicate_df_cluster = df_cluster.copy()
    from .main_dev import dummySlider

    global previousDSliderValue
    previousDSliderValue = 0
    
    @pn.depends(selectedBrand = selectBrand, selectedPackage = selectPackage, selectedPrint = selectPrint, selectedIntegrity = selectIntegrity, dSlider = dummySlider)
    def createGraph(selectedBrand, selectedPackage, selectedPrint, selectedIntegrity, dSlider):
        print("second ------------------------------")
        global mutipleValue
        global duplicate_df_cluster
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        df_properties = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'_data.csv'), sep=';')
        try:
            mutipleValue = list(df_properties[(df_properties['Brand'] == selectedBrand)
                                    &( df_properties['Package'] == selectedPackage)
                                    &(df_properties['Prijs'] == selectedPrint)
                                ]["Multiplier"])[0]
        except:
            mutipleValue = 1
        try:
            df_cluster = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
            duplicate_df_cluster = df_cluster.copy()
        except: 
            df_cluster = pd.read_csv(c.FORECAST_FILEPATH, sep=';')
        df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn], dayfirst=True)
    
        traces = []
        df_cluster_outflow = pd.read_csv(c.FORECAST_FILEPATH, sep=';')
        
        dup_df_cluster = df_cluster.copy()

        df_cluster_outflow = df_cluster_outflow[(df_cluster_outflow['brand'] == selectedBrand)
                                        & (df_cluster_outflow['subscr_type'] == selectedPackage)
                                        & (df_cluster_outflow['pricecat'] == selectedPrint)
                                        & (df_cluster_outflow[dateColumn] >= dc.SLIDER_DATE)]

        dup_df_cluster = dup_df_cluster[(dup_df_cluster['brand'] == selectedBrand)
                                        & (dup_df_cluster['subscr_type'] == selectedPackage)
                                        & (dup_df_cluster['pricecat'] == selectedPrint)
                                        & (dup_df_cluster[dateColumn] >= dc.SLIDER_DATE)]

        dup_df_cluster_integrity = dup_df_cluster[dup_df_cluster['forecast'] == 1]
        selectedIntegrity = round(selectedIntegrity,2)

        if selectedIntegrity != mutipleValue:
            # Updated Churn Calculation
            dup_df_cluster_integrity['churncheck'] = dup_df_cluster['churncheck'] * (selectedIntegrity/mutipleValue)
            dup_df_cluster_integrity['nettosaldo'] = dup_df_cluster_integrity['newcheck'] - dup_df_cluster_integrity['churncheck'] + dup_df_cluster_integrity[
                'inflow_switchers'] + dup_df_cluster_integrity['inflow_transformers'] - dup_df_cluster_integrity['switcher_outflow'] - dup_df_cluster_integrity['trans_outflow']
            
            latest_actuals = dup_df_cluster.loc[(dup_df_cluster['Date'] == c.TRAIN_END_DATE)]

            latest_actuals['nettosaldo'] = latest_actuals['currentcheck']

            dup_df_cluster_integrity = latest_actuals.append(dup_df_cluster_integrity, ignore_index=False).fillna(0)

            dup_df_cluster_integrity['currentcheck'] = dup_df_cluster_integrity.groupby(['brand', 'subscr_type', 'pricecat'])['nettosaldo'].transform(
                pd.Series.cumsum)

            for i in dup_df_cluster_integrity.index:
                duplicate_df_cluster.loc[i, 'churncheck'] = round(dup_df_cluster_integrity.loc[i, 'churncheck'])
                duplicate_df_cluster.loc[i, 'currentcheck'] = round(dup_df_cluster_integrity.loc[i, 'currentcheck'])

            dup_df_cluster = processing.add_churn_pct_v2(dup_df_cluster)
            dup_df_cluster = dup_df_cluster.groupby([dateColumn, 'forecast'])['churncheck'].sum().reset_index()
            df_cluster_outflow = df_cluster_outflow.groupby([dateColumn, 'forecast'])['churncheck'].sum().reset_index()
            dup_df_cluster_integrity = dup_df_cluster_integrity.groupby(dateColumn)['churncheck'].sum().reset_index()
           
        traces.append(go.Scatter(x=dup_df_cluster_integrity[dateColumn], y=dup_df_cluster_integrity['churncheck'], mode='lines', marker_color='#e84393', name='Adjusted'))
        traces.append(go.Scatter(x=dup_df_cluster[dup_df_cluster['forecast'] == 0][dateColumn], y=dup_df_cluster[dup_df_cluster['forecast'] == 0]['churncheck'], mode='lines', marker_color='#34495e', name='Actual'))
        traces.append(go.Scatter(x=df_cluster_outflow[df_cluster_outflow['forecast'] == 1][dateColumn], y=df_cluster_outflow[df_cluster_outflow['forecast'] == 1]['churncheck'], mode='lines', marker_color='#4cd137', name='forecasted'))
            
        # Create layout for graph
        layout = go.Layout(
            showlegend=True, 
            width=1300, 
            height=500,
            autosize=False,
            margin=dict(l=0, r=0, t=30,b=10),
            xaxis=dict(title='Date'),
            yaxis=dict(title='Regular Outflow')
        ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectedBrand = selectBrand, selectedPackage = selectPackage, selectedPrint = selectPrint, dSlider = dummySlider)
    def createPercentageGraph(selectedBrand, selectedPackage, selectedPrint, dSlider):
        global previousDSliderValue
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        
        try:
            df_cluster_name = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), sep=';')
        except: 
            df_cluster_name = pd.read_csv(c.FORECAST_FILEPATH, sep=';')

        df_cluster_name[dateColumn] = pd.to_datetime(df_cluster_name[dateColumn], dayfirst=True)
        df_cluster = pd.read_csv(c.FORECAST_FILEPATH, sep=';')
        df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn], dayfirst=True)
        
        traces = []
        if previousDSliderValue != dSlider:
            previousDSliderValue = dSlider
            dup_df_cluster_adjusted = processing.add_churn_pct_v2(df_cluster_name[(df_cluster_name['brand'] == selectedBrand)
                                        & (df_cluster_name['subscr_type'] == selectedPackage)
                                        & (df_cluster_name['pricecat'] == selectedPrint)
                                        & (df_cluster_name['forecast'] == 1)])
            dup_df_cluster_adjusted = dup_df_cluster_adjusted.iloc[1:]
            dup_df_cluster_adjusted[dateColumn] = pd.to_datetime(dup_df_cluster_adjusted[dateColumn], dayfirst=True)
            
            dup_df_cluster_adjusted['nettosaldo'] = dup_df_cluster_adjusted['newcheck'] \
                            + dup_df_cluster_adjusted['inflow_switchers'] \
                            + dup_df_cluster_adjusted['inflow_transformers'] \
                            - dup_df_cluster_adjusted['churncheck'] \
                            - dup_df_cluster_adjusted['switcher_outflow'] \
                            - dup_df_cluster_adjusted['trans_outflow']

            for _, row in dup_df_cluster_adjusted.iterrows():
                val = df_cluster_name.loc[(df_cluster_name['Date'] == row['Date'])
                                &(df_cluster_name['brand'] == row['brand'])
                                &(df_cluster_name['pricecat'] == row['pricecat'])
                                &(df_cluster_name['subscr_type'] == row['subscr_type'])
                                &(df_cluster_name['forecast'] == 1)]
                val = val.reset_index()['index']
                df_cluster_name.loc[val, 'churnpercentage'] = row['churnpercentage']
                df_cluster_name.loc[val, 'nettosaldo'] = row['nettosaldo']
            df_cluster_name['nettosaldo'] = df_cluster_name['nettosaldo'].round(2)
            df_cluster_name.to_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), index=False, sep=';')
            
            traces.append(go.Scatter(x=dup_df_cluster_adjusted[dateColumn], y=dup_df_cluster_adjusted['churnpercentage'], mode='lines', marker_color='#e84393', name="Adjusted"))
          
        dup_df_cluster = df_cluster.copy()
        dup_df_cluster_actual = dup_df_cluster[(dup_df_cluster['brand'] == selectedBrand)
                                        & (dup_df_cluster['subscr_type'] == selectedPackage)
                                        & (dup_df_cluster['pricecat'] == selectedPrint)
                                        & (dup_df_cluster[dateColumn] >= dc.SLIDER_DATE)
                                        & (dup_df_cluster['forecast'] == 0)]

        dup_df_cluster_forecast = dup_df_cluster[(dup_df_cluster['brand'] == selectedBrand)
                                        & (dup_df_cluster['subscr_type'] == selectedPackage)
                                        & (dup_df_cluster['pricecat'] == selectedPrint)
                                        & (dup_df_cluster['forecast'] == 1)]
        
        dup_df_cluster = dup_df_cluster.groupby(dateColumn)['churnpercentage'].sum().reset_index()
        
        traces.append(go.Scatter(x=dup_df_cluster_actual[dateColumn], y=dup_df_cluster_actual['churnpercentage'], mode='lines', marker_color='#34495e', name="Actual"))
        traces.append(go.Scatter(x=dup_df_cluster_forecast[dateColumn], y=dup_df_cluster_forecast['churnpercentage'], mode='lines', marker_color='#4cd137', name="Forecast"))
          
        # Create layout for graph
        layout = go.Layout(
            width=1300, 
            height=500,
            autosize=False,
            margin=dict(l=0, r=0, t=30,b=10),
            xaxis=dict(title='Date'),
            yaxis=dict(title='Outflow Percentage')
        ) 
        
        return go.Figure(data=traces, layout=layout)

    @pn.depends(selectBrand, selectPackage, selectPrint, dummySlider)
    def changeMultiplier(b, p, pp, dSlider):
		
        global mutipleValue
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        print("got to change multiplier ", dSlider)
        df_properties = pd.read_csv(os.path.join(currentDir, 'User Data', uname+'_data.csv'), sep=';')
        try:
            val = list(df_properties[(df_properties['Brand'] == b)
                                &( df_properties['Package'] == p)
                                &(df_properties['Prijs'] == pp)
                            ]["Multiplier"])[0]
            print(selectIntegrity.value, val)
            selectIntegrity.value = val
        except: 
            selectIntegrity.value = 1
        mutipleValue = selectIntegrity.value
    
    def updateDataFrame(event):
        global mutipleValue
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        duplicate_df_cluster.to_csv(os.path.join(currentDir, 'User Data', uname+'.csv'), index=False, sep=';')
        df_cluster = duplicate_df_cluster.copy()
        df_cluster[dateColumn] = pd.to_datetime(df_cluster[dateColumn], dayfirst=True)
        
        try:
            val = df_properties.loc[(df_properties['Brand'] == selectBrand.value)
                                &( df_properties['Package'] == selectPackage.value)
                                &(df_properties['Prijs'] == selectPrint.value)
                            ]
            val = df_properties.reset_index()['index']
            
            df_properties.drop(list(val), inplace=True)
            df_properties.loc[len(df_properties)] = [round(selectIntegrity.value, 1), selectBrand.value, selectPackage.value, selectPrint.value]
        except Exception as e:
            df_properties.loc[len(df_properties)] = [round(selectIntegrity.value, 1), selectBrand.value, selectPackage.value, selectPrint.value]
        
        df_properties.to_csv(os.path.join(currentDir, 'User Data', uname+'_data.csv'), index=False, sep=';')
        
        mutipleValue = selectIntegrity.value
        dummySlider.value += 1


    submit.on_click(updateDataFrame)
    return pn.Column(
        pn.Row(
            pn.Column(
                selectIntegrity,
                submit
            ),
            selectBrand,
            selectPackage,
            selectPrint
        ),
        pn.Column(
            changeMultiplier,
            createGraph,
            createPercentageGraph
        )
    )