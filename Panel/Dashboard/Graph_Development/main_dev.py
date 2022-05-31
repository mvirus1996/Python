import panel as pn
import os, tornado
import pandas as pd

import constants as c


def mainFun():
    raw_css = ''
    currentDir = os.path.join(os.getcwd(), 'data')
    bootstrap = pn.template.BootstrapTemplate()
    raw_css = """
        *{ 
            box-sizing: border-box 
            padding: 0px;
            margin: 0px;
        }

        .bk-root * { 
            box-sizing: content-box 
        }

        #header-items{
            display: flex;
            justify-content: space-between;
            align-items: center;
            width: 75%;
        }

        #header-items div:nth-child(1){
            width: 25%;
            color: white;
            font-size: 15px;
            text-justify: center;
        }

        #header-items div:nth-child(2){
            width: 25%;
        }
        
        .bk-root .bk-tabs-header.bk-above .bk-headers, .bk-root .bk-tabs-header.bk-below .bk-headers{
            font-size:16px;
            font-weight: bold;
        }

        .cm-toggle input{
            -webkit-appearance: none;
            -webkit-tap-highlight-color: transparent;
            position: relative;
            border: 0;
            outline: 0;
            cursor: pointer;
            margin: 10px;
        }
        
        .cm-toggle input:after{
            content: '';
            width: 30px;
            height: 14px;
            display: inline-block;
            background: red;
            border-radius: 18px;
            clear: both;
        }
        
        .cm-toggle input:before{
            content: '';
            width: 16px;
            height: 16px;
            display: block;
            position: absolute;
            left: -1px;
            top: -1px;
            border-radius: 50%;
            background: rgb(255,255,255);
            box-shadow: 1px 1px 3px rgba(0,0,0,0.6);
        }
        
        .cm-toggle input:checked:before{
            left: 16px;
            box-shadow: -1px 1px 3px rgba(0,0,0,0.6)
        }
        
        .cm-toggle input:checked:after{
            background: green;
            border-radius: 50px;
        }

        .bk-cell-select{
            margin: 75px;
        }

        .slick-column-name{
            font-size: 16px;
            font-weight: bold;
        }

        .slick-cell{
            font-size: 14px;
        }

        table{
            width: 300%;
        }

        th{
            background-color: #576574;
            color: white;
        }

        td{
            background-color: #cbfaac;
        }

        td, th{
            padding: 5px 10px;
            text-align: center;
        }
    """

    uname = tornado.escape.json_decode(pn.state.cookies['user'])

    logoutbutton = pn.widgets.Button(name='LogOut', button_type='danger', width=100)
    global dummySlider
    dummySlider = pn.widgets.IntSlider(name="dummy", start=1, end=100, value=1)
    global activeDFSlider
    activeDFSlider = pn.widgets.IntSlider(name="active dummy", start=1, end=100, value=1)
    reset = pn.widgets.Button(name='Reset', button_type='primary', width=100)
    spinner = pn.indicators.LoadingSpinner(value=True, width=40, height=40)

    #pn.extension(raw_css=[raw_css], js_files=js_files)
    pn.extension(raw_css=[raw_css])
    pn.state.sync_busy(spinner)
    
    
    tabs = pn.Tabs(margin=(30,0))
    tabs.clear()
    from . import tabFlow, tabTotalInflow, tabTotalOutflow, tabFlow2, tabFlow_copy, tabFlow2_copy, tabClusteringInflow, tabClusteringOutflow, tabSummaryInOut, tabSummaryActiveSubscr
    
    
    tabs.extend([
        ('Campaign Driver', tabClusteringInflow.mainFunCluster()),  
        ('Churn Driver', tabClusteringOutflow.mainFun()),
        ('Summary by price type (Linechart)', tabFlow.mainFun()),
        ('Summary by price type  (Barchart)', tabFlow_copy.mainFun()),
        ('Summary by package type (Linechart)', tabFlow2.mainFun()),
        ('Summary by package type (Barchart)', tabFlow2_copy.mainFun()),
        ('Inflow Insights', tabTotalInflow.mainFun()),
        ('Outflow Insights', tabTotalOutflow.mainFun()),
        ('Summary Inflow/Outflow', tabSummaryInOut.mainFun()),
        ('Summary Active Subscribers', tabSummaryActiveSubscr.mainFun())
    ])

    def resetAdjustment(event):
        uname = tornado.escape.json_decode(pn.state.cookies['user'])
        switch_file = pd.read_csv(c.FORECAST_FILEPATH, sep=';')
        active_file = pd.read_csv(c.CAMPAIGN_CLUSTERS_ACTIVE_PATH, sep=';')
        switch_file.to_csv(os.path.join(currentDir, "User Data", uname+".csv"), sep=';', index = False)
        active_file.to_csv(os.path.join(currentDir, 'User Data', uname+'_active.csv'), index=False, sep=';')
        df = pd.DataFrame([[1, 'DS', 'ZADI', 'BASE']], columns = ['Multiplier', 'Brand', 'Package', 'Prijs'])
        df.to_csv(os.path.join(currentDir, "User Data", uname+"_data.csv"), index=False, sep=";")

        if activeDFSlider.value == 100:
            activeDFSlider.value = 0
        else:
            activeDFSlider.value += 1

        if dummySlider.value == 100:
            dummySlider.value = 0
        else:
            dummySlider.value += 1

    logoutbutton.js_on_click(code="window.location.href='%s'" % pn.state.curdoc.session_context.logout_url)
    reset.on_click(resetAdjustment)
    uname = tornado.escape.json_decode(pn.state.cookies['user'])
    name = uname.split('@')[0]
    try:
        fname, _ = name.split('.')
    except:
        fname = name
    
    bootstrap = pn.template.BootstrapTemplate(
        header=["Welcome "+fname.capitalize(), "Dashboard_14.0 ", reset, logoutbutton], title='', 
        header_background='#535c68', 
        favicon=os.path.join(currentDir, 'Img','favlogo.jpg'), 
        logo=os.path.join(currentDir, 'Img', 'logo.svg'),
        busy_indicator=spinner     
    )
    bootstrap.main.append(
            pn.Column(
            tabs,
            css_classes=['tabs-class']
        )
    )
    return bootstrap.servable()
