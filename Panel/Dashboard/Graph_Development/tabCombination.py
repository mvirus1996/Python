import pandas as pd
import panel as pn
import os
import csv
import plotly.graph_objs as go
import glob
import numpy as np

from Models import train_model

currentDir = os.path.join(os.getcwd(),'data')
dateColumn = 'Date'

# Get dataset from csv file
df_combination = pd.read_csv(os.path.join(currentDir, 'FinalCampaign_File_Type.csv'), error_bad_lines=False, sep=';')

# convert string to datetime format
df_combination[dateColumn] = pd.to_datetime(df_combination[dateColumn])
df_combination = df_combination.fillna(0)

# create a new column for selectIntegrityDate date-slider
mon_year = df_combination[dateColumn].dt.strftime('%b-%Y')
df_combination.insert(1, 'mon_year', mon_year)
df_combination = df_combination.sort_values(by=dateColumn)

df_combination2 = df_combination[df_combination['forecasted']==1]

# Get all the combinations in the csv file
listOfCombinations = ['Select All']
for i in list(df_combination['combination'].unique()):
    listOfCombinations.append(i)

df_stunt = pd.read_csv('data/FinalCampaignFile_DS_ZADI_STUNT.csv', error_bad_lines=False, sep=';')
tableFileName = ''
download_table_df = pd.DataFrame()

# create exo value 
def createExoValue():
    global df_stunt
    global tableFileName
    brand = 'DS'
    sub_type = 'ZADI'
    pricecat = 'STUNT'
    tableFileName = brand+"_"+sub_type+'_'+pricecat
    dup_df = df.copy()
    dup_df['Date'] = pd.to_datetime(dup_df['Date'], dayfirst=True)
    dup_df['Date'] = dup_df['Date'] + pd.offsets.MonthEnd(0) 

    df_stunt['startdatum'] = pd.to_datetime(df_stunt['startdatum'], dayfirst=True)
    df_stunt['startdatum'] = df_stunt.startdatum.dt.strftime('%Y-%m-%d')
    df_stunt['startdatum'] = pd.DatetimeIndex(df_stunt['startdatum'])

    # #Filter Data - Start with STUNT  
    df_filter = dup_df.loc[(dup_df['brand'] == brand)
                    &(dup_df['subscr_type'] == sub_type)
                    &(dup_df['pricecat'] == pricecat)
                    &(dup_df['Date'] >= '2018-01-01')
                    &(dup_df['Date'] <= '2020-07-31')]
    df_filter = df_filter.set_index('Date')

    df_exo_full_stunt = df_stunt.loc[(df_stunt['combination'] == 'VITRINE')
                    & (df_stunt['startdatum'] >= '2018-01-01')
                    & (df_stunt['startdatum'] <= '2020-07-31')]

    mean_exo = np.mean(df_exo_full_stunt['persoon_id'])
    std_exo = np.std(df_exo_full_stunt['persoon_id'])

    ubound = mean_exo + 1.65*std_exo
    lbound = mean_exo - 1.28*std_exo
    uubound = mean_exo + 1.28*std_exo
    llbound = mean_exo - 0.71*std_exo

    df_exo_adjusted_stunt = df_exo_full_stunt.copy()
    df_exo_adjusted_stunt['exo'] =np.where(df_exo_adjusted_stunt['persoon_id'] > ubound, 1 ,
                            np.where(df_exo_adjusted_stunt['persoon_id'] < lbound, 0 ,
                            np.where(df_exo_adjusted_stunt['persoon_id'] > uubound, 0.8 ,   
                            np.where(df_exo_adjusted_stunt['persoon_id'] < llbound, 0.2 , 0.5))))

    df_stunt = df_exo_adjusted_stunt.copy()

createExoValue()

df_stunt_main = df_stunt.copy()

# create a new column for selectIntegrityDate date-slider
mon_year = df_stunt['startdatum'].dt.strftime('%b-%Y')
df_stunt.insert(len(df_stunt.columns), 'mon_year', mon_year)
df_stunt = df_stunt.sort_values(by='startdatum')
df_stunt['forecasted'] = np.where(df_stunt['startdatum'].dt.year >= 2019 , 1, 0)

# Drop-downs for different variables for Combination tab
selectBrandCombination = pn.widgets.Select(name='Brand', options=['DS', 'BVL'], value='DS')
selectPrintCombination = pn.widgets.Select(name='Print', options=['DIGI', 'PRINT'], value='DIGI')
selectPriceCombination = pn.widgets.Select(name='Package Type', options=['DIGI','ZADI','WEDI','Print_full'], value='ZADI')
selectSubscr_TypeCombination = pn.widgets.Select(name='Price Category', options=['STUNT', 'BASE', 'PROMO'], value='STUNT')

selectIntegrityDate = pn.widgets.DiscreteSlider(name='Select planning Month', options=list(df_stunt[df_stunt['forecasted']==1]['mon_year'].unique()), value=list(df_stunt[df_stunt['forecasted']==1]['mon_year'])[0])
selectIntegrity = pn.widgets.TextInput(name='Enter Inflow Effect', value='0')
selectCombination = pn.widgets.Select(name='Inflow channel', options=['KORTING', 'VITRINE'], value='VITRINE')
# messages = pn.widgets.TextInput(value='', disabled=True) 

# Button for Combination tab
trainButton = pn.widgets.Button(name='Re-Train Model', button_type='primary', width=250)
downloadButtonInflow = pn.widgets.Button(name='Download table as CSV', button_type='primary', width=250)
# downloadButtonOutflow = pn.widgets.Button(name='Download Outflow as CSV', button_type='primary', width=250)

# Titles
title = 'PANEL Dashboard - SUBSCRIBER - INFLOW'
title2 = '<H4> Inflow / Outflow </H4>'
titleIntegrity = '<H6> Campaign Intensity: </H6>'
titleDate = '<h6> Select a date to change Exogenous value: </h6>'
titleBrand = '<h6> Pick one or more option(s) from the dropdown below: </h6>'
titleInflow = '<h6> Pick any check type from the dropdown below: </h6>'

# declaration of bootstrap
bootstrap = pn.template.BootstrapTemplate(title=title)

# Global variables
location = 0
previousCombination = ''
inflow_prediction = pd.DataFrame()
outflow_prediction = pd.DataFrame()
inflow_actual_prediction = pd.DataFrame()
outflow_actual_prediction = pd.DataFrame()
inflow_actual = pd.DataFrame()
outflow_actual = pd.DataFrame()

# show exo value in input field according to date selected
@pn.depends(selectedIntegrityDate=selectIntegrityDate)
def changeIntegrityValue(selectedIntegrityDate):
    global location
    if selectCombination.value == 'Select All':
        return
    location = df_stunt.loc[(df_stunt['mon_year'] == selectedIntegrityDate)
                            & (df_stunt['combination'] == selectCombination.value)
                        ].index[0]
    try:
        data = df_stunt.loc[location , 'exo']
        val = str(round(data, 2))
    except Exception as e:
        print('error 1 ',e)
        val = '0'
    selectIntegrity.value = val
    return

# interaction function for combination tab
@pn.depends(selectedCombination=selectCombination, selectedIntegrity = selectIntegrity)
def plotCombinationGraphInflow(selectedIntegrity, selectedCombination):
    global location
    global df_stunt
    global inflow_prediction
    global inflow_actual_prediction
    global inflow_actual
    traces = []
    
    df_stunt.loc[df_stunt['startdatum'] == df_stunt.loc[location, 'startdatum'], 'exo'] = float(selectedIntegrity)
    
    actual, inflow_predicted, outflow_predicted = predict_stunt.predict_stunt(df_stunt.loc[location, 'startdatum'], selectedIntegrity)
    inflow_prediction = inflow_predicted
    inflow_actual = actual
    if inflow_actual_prediction.empty:
        inflow_actual_prediction = inflow_predicted.copy()
    traces.append(go.Scatter(x=actual[dateColumn], y=actual['newcheck'], mode='lines', color='#2980b9', name='Inflow Actual'))
    traces.append(go.Scatter(x=inflow_actual_prediction['index'], y=inflow_actual_prediction['predicted_mean'], mode='lines', color='#27ae60', name='Inflow Forecasted'))
    traces.append(go.Scatter(x=inflow_predicted['index'], y=inflow_predicted['predicted_mean'], mode='lines', color='#e84393', name='Inflow Adjusted'))
      
    # Create layout for graph
    layout = go.Layout(
        showlegend=True, 
        width=900, 
        height=400,
        margin=dict(l=0, r=0, t=30,b=10),
        autosize=False,
        xaxis=dict(title='Date'),
        yaxis=dict( title='Inflow')
    ) 
    
    return go.Figure(data=traces, layout=layout)

# interaction function for combination tab
@pn.depends(selectedCombination=selectCombination, selectedIntegrity = selectIntegrity)
def plotCombinationGraphOutflow(selectedIntegrity, selectedCombination):
    global location
    global df_stunt
    global outflow_prediction
    global outflow_actual_prediction
    global outflow_actual
    traces = []
    
    df_stunt.loc[df_stunt['startdatum'] == location, 'exo'] = float(selectedIntegrity)
    
    actual, inflow_predicted, outflow_predicted = predict_stunt.predict_stunt(df_stunt.loc[location, 'startdatum'], selectedIntegrity)
    outflow_prediction = outflow_predicted
    outflow_actual = actual
    if outflow_actual_prediction.empty:
        outflow_actual_prediction = outflow_predicted.copy()
    traces.append(go.Scatter(x=actual[dateColumn], y=actual['churncheck'], mode='lines', color='#2980b9', name='Outflow Actual'))
    traces.append(go.Scatter(x=outflow_actual_prediction['index'], y=outflow_actual_prediction[0], mode='lines', color='#27ae60', name='Outflow Forecasted'))
    traces.append(go.Scatter(x=outflow_predicted['index'], y=outflow_predicted[0], mode='lines', color='#e84393', name='Outflow Adjusted'))
        
    # Create layout for graph
    layout = go.Layout(
        showlegend=True, 
        width=800, 
        height=400,
        margin=dict(l=0, r=0, t=30,b=10),
        autosize=False,
        xaxis=dict(title='Date'),
        yaxis=dict( title='Outflow')
    ) 
    
    return go.Figure(data=traces, layout=layout)

@pn.depends(selectedIntegrity = selectIntegrity)
def createCombinationTableInflow(selectedIntegrity):
    global download_table_df_inflow

    dup_df_stunt_main = df_stunt_main.copy()

    dup_df_stunt_main = dup_df_stunt_main.loc[
                    (dup_df_stunt_main['startdatum'] >= '2019-02-28')
                    ]

    dup_df_stunt_main['Inflow Budget'] = inflow_actual['newcheck'].values 
    dup_df_stunt_main['Inflow forecasted'] = inflow_actual_prediction['predicted_mean'].values    
    dup_df_stunt_main['Inflow Adjusted'] = inflow_prediction['predicted_mean'].values

    dup_df_stunt_main['Inflow forecasted'] = dup_df_stunt_main['Inflow forecasted'].astype(int)
    dup_df_stunt_main['Inflow Adjusted'] = dup_df_stunt_main['Inflow Adjusted'].astype(int)

    dup_df_stunt_main['Inflow forecasted'].round()
    dup_df_stunt_main['Inflow Adjusted'].round()

    dup_df_stunt_main['Outflow Budget'] = outflow_actual['churncheck'].values 
    dup_df_stunt_main['Outflow forecasted'] = outflow_actual_prediction[0].values    
    dup_df_stunt_main['Outflow Adjusted'] = outflow_prediction[0].values

    dup_df_stunt_main['Outflow forecasted'] = dup_df_stunt_main['Outflow forecasted'].astype(int)
    dup_df_stunt_main['Outflow Adjusted'] = dup_df_stunt_main['Outflow Adjusted'].astype(int)

    dup_df_stunt_main['Outflow forecasted'].round()
    dup_df_stunt_main['Outflow Adjusted'].round()

    for i in ['persoon_id', 'exo', 'promotioncode']:
        del dup_df_stunt_main[i]
    
    dup_df_stunt_main.rename(columns = {'combination': 'Inflow Channel'}, inplace = True)
    
    dup_df_stunt_main['startdatum'] = dup_df_stunt_main['startdatum'].astype(str)

    download_table_df_inflow = dup_df_stunt_main.copy()

    colName = []
    # capitalize the column names
    for i in dup_df_stunt_main.columns:
        print("columns  : ", i)
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
                    fill_color='#576574',
                    font_size=12,
                    font_color='white',
                    height=30,
                    align=['center', 'center'],
                    
            ), 
            cells=dict(values= [dup_df_stunt_main[val] for val in dup_df_stunt_main.columns],
                    line_color='darkslategray',
                    fill_color='#cbfaac',#'#e7f7b5',#'#bbffb9',
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

# @pn.depends(selectedIntegrity = selectIntegrity)
# def createCombinationTableOutflow(selectedIntegrity):
#     global download_table_df_outflow

#     dup_df_stunt_main = df_stunt_main.copy()

#     dup_df_stunt_main = dup_df_stunt_main.loc[
#                     (dup_df_stunt_main['startdatum'] >= '2019-02-28')
#                     ]
#     dup_df_stunt_main['Budget'] = outflow_actual['churncheck'].values 
#     dup_df_stunt_main['forecasted'] = outflow_actual_prediction[0].values    
#     dup_df_stunt_main['Adjusted'] = outflow_prediction[0].values

#     dup_df_stunt_main['forecasted'] = dup_df_stunt_main['forecasted'].astype(int)
#     dup_df_stunt_main['Adjusted'] = dup_df_stunt_main['Adjusted'].astype(int)

#     dup_df_stunt_main['forecasted'].round()
#     dup_df_stunt_main['Adjusted'].round()

#     for i in ['persoon_id', 'exo', 'promotioncode']:
#         del dup_df_stunt_main[i]
    
#     dup_df_stunt_main.rename(columns = {'combination': 'Outflow Channel'}, inplace = True)
    
#     dup_df_stunt_main['startdatum'] = dup_df_stunt_main['startdatum'].astype(str)

#     download_table_df_outflow = dup_df_stunt_main.copy()

#     colName = []
#     # capitalize the column names
#     for i in dup_df_stunt_main.columns:
#         print("columns  : ", i)
#         if i.find('_') != -1:
#             val = '<b>'
#             for j in i.split('_'):
#                 val = val+j.capitalize()+'<br>'
#             colName.append(val+'</b>')
#         else:
#             colName.append('<b>'+i.capitalize()+'</b>')

#     data = go.Table(
#             columnwidth=[1,1],
#             header=dict(
#                     values=colName,
#                     line_color='darkslategray',
#                     fill_color='lightskyblue',
#                     font_size=12,
#                     height=30,
#                     align=['center', 'center'],
#             ), 
#             cells=dict(values= [dup_df_stunt_main[val] for val in dup_df_stunt_main.columns],
#                     line_color='darkslategray',
#                     fill_color='lightcyan',
#                     font_size=12,
#                     height=30
#             )
#         )

#     layout = go.Layout(
#         width=900, 
#         height=600,
#         margin=dict(l=10, r=0, t=30,b=10),
#     )
#     return go.Figure(data=data, layout=layout)

# function to click event to train model
def trainModelAgain(event):
    return 
    name = selectBrandCombination.value+'_'+selectSubscr_TypeCombination.value+'_'+selectPriceCombination.value+'_'+selectPrintCombination.value+'_'+selectCombination.value
    for i in glob.glob(os.path.join(currentDir,"PKL File","*.pkl")):
        if os.path.basename(i).find(name) != -1:
            os.remove(i)
            break
    train_model.trainModel(selectBrandCombination.value, selectSubscr_TypeCombination.value, selectPriceCombination.value, selectPrintCombination.value, selectCombination.value) 

# function for click event to download file
def downloadFile(event):
    dup_tableFileName = tableFileName+'.csv'
    with open(dup_tableFileName, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(download_table_df_inflow.columns)
        csvwriter.writerows(download_table_df_inflow.values)
    # else:
    #     dup_tableFileName = tableFileName+'_Outflow.csv'
    #     with open(dup_tableFileName, 'w') as csvfile:
    #         csvwriter = csv.writer(csvfile)
    #         csvwriter.writerow(download_table_df_outflow.columns)
    #         csvwriter.writerows(download_table_df_outflow.values)

# function call for train model button
trainButton.on_click(trainModelAgain)

# function call for download csv
downloadButtonInflow.on_click(downloadFile)
# downloadButtonOutflow.on_click(downloadFile)

#pn.config.sizing_mode = 'stretch_width'

def mainFun():
    return pn.Column(
        pn.Row(
            pn.Column(
                titleIntegrity,
                selectIntegrityDate,
                selectIntegrity,
                changeIntegrityValue
            ),
            pn.Column(
                selectBrandCombination,
                selectPrintCombination,
                selectSubscr_TypeCombination
            ),
            pn.Column(
                selectPriceCombination,
            )
        ),
        pn.Row(
            trainButton
        ),
        pn.Row(
            plotCombinationGraphInflow,
            plotCombinationGraphOutflow
        ),
        pn.Row(
           downloadButtonInflow 
        ),
        pn.Row(
            createCombinationTableInflow
        ),
        css_classes=['tabCombination']
    )