import os
import pathlib

import pandas as pd
from dateutil.relativedelta import relativedelta

TRAIN = True
DEBUG = False
INFO = False
MEASURE_ACCURACY = False

CURRENT_DIR = pathlib.Path(__file__).parents[0].absolute()

# input
SWITCH_TRANS_FINAL_PATH = os.path.join(CURRENT_DIR, 'data/switchtransfinal.csv')
CAMPAIGN_CLUSTERS_AGGREGATED_PATH = os.path.join(CURRENT_DIR, 'data/CampagnesCountClusteredPerMonth_Aggregated.csv')
CAMPAIGN_CLUSTERS_ACTIVE_PATH = os.path.join(CURRENT_DIR, 'data/ClusteredCampaignEffectMonthlyPredictionActive.csv')

TRAIN_BEGIN_DATE = '2016-01-01'
TRAIN_END_DATE = '2021-06-30'

STEPS_AHEAD = 18
FORECAST_BEGIN_DATE = (pd.to_datetime(TRAIN_END_DATE) + relativedelta(months=+ 1)).to_period('M').to_timestamp('M')
FORECAST_END_DATE = (pd.to_datetime(TRAIN_END_DATE) + relativedelta(months=+ 18)).to_period('M').to_timestamp('M')

LATEST_COMPLETE_ACTUALS_DATE = TRAIN_END_DATE

RELATIONS_SRC_PATH = os.path.join(CURRENT_DIR, 'model_overview.csv')

# output
DATA_DIR = os.path.join(CURRENT_DIR, 'data')
PKL_SAVE_DIR = os.path.join(DATA_DIR, 'PKL File')
FORECAST_FILEPATH = os.path.join(DATA_DIR, "switchtransfinal_with_forecast.csv")
STATIC_FORECAST_FILEPATH = os.path.join(DATA_DIR, "switchtransfinal_with_forecast_static.csv")
ACCURACY_SAVE_PATH = os.path.join(DATA_DIR, 'output/accuracy_results.xlsx')
RELATIONS_BUSINESS_OVERVIEW_PATH = os.path.join(DATA_DIR, 'output/model_overview_business.xlsx')

COLUMNS_TO_ROUND = ['newcheck', 'churncheck', 'inflow_transformers', 'inflow_switchers',
                    'trans_outflow', 'switcher_outflow', 'currentcheck']

COLUMNS_ORDER = ['brand', 'print', 'subscr_type', 'pricecat',
                 'Date', 'forecast', 'currentcheck', 'newcheck','inflow_transformers','inflow_switchers',
                 'churncheck', 'trans_outflow','switcher_outflow', 'nettosaldo', 'churnpercentage']

FILLNA_COLS =['newcheck', 'inflow_transformers', 'inflow_switchers',
              'churncheck',   'switcher_outflow','trans_outflow']

DIGI_TYPES = ['ZADI', 'DIGI', 'PLUS', 'WEDI']
