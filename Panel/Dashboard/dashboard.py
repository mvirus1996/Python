import os, glob, sys, tornado
import pandas as pd
import panel as pn

currentDir = os.path.join(os.getcwd(), 'data')

try:
    uname = tornado.escape.json_decode(pn.state.cookies['user'])
    print("cookies loggedin: ",pn.state.cookies['user'])
    cred = pd.read_csv(os.path.join(currentDir, 'Credentials.csv'), error_bad_lines=False)
    filename = [os.path.basename(i) for i in glob.glob(os.path.join(currentDir,'User Data',"*.csv"))]
    
    switch_file = pd.read_csv(os.path.join(currentDir, 'switchtransfinal_with_forecast.csv'), sep=';')
    active_file = pd.read_csv(os.path.join(currentDir, 'ClusteredCampaignEffectMonthlyPredictionActive.csv'), sep=';')
    for i in cred['name']:
        if i+'.csv' not in filename:
            print('not', i)
            switch_file.to_csv(os.path.join(currentDir, "User Data", i+".csv"), sep=';', index = False)
        if i+'_active.csv' not in filename:
            active_file.to_csv(os.path.join(currentDir, 'User Data', i+'_active.csv'), index=False, sep=';')
        if i+'_data.csv' not in filename:
            df = pd.DataFrame([[1, 'DS', 'ZADI', 'BASE']], columns = ['Multiplier', 'Brand', 'Package', 'Prijs'])
            df.to_csv(os.path.join(currentDir, "User Data", i+"_data.csv"), index=False, sep=";")
    
    from Graph_Development import main_dev
    
    main_dev.mainFun()

except Exception as e:
    print('app error: ', e)
    sys.exit()


#bokeh serve --port 8000 --address localhost --keep-alive 20000 --enable-xsrf-cookies --auth-module=auth.py  dashboard.py