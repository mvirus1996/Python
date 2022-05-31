import os

import numpy as np
import pandas as pd

import constants as c
from Models import processing as pr


def compare_actuals_forecast(brand='DS',
                             subscr_type='ZADI',
                             pricecat='BASE',
                             Test_Begin_Date=c.FORECAST_BEGIN_DATE,
                             Test_End_Date=c.LATEST_COMPLETE_ACTUALS_DATE,
                             ):
    currentDir = os.path.join(os.getcwd(), 'data')

    actual_data = pd.read_csv(os.path.join(currentDir, 'switchtransfinal.csv'), sep=';')

    predicted_data = pd.read_csv(os.path.join(currentDir, 'switchtransfinal_with_forecast.csv'), sep=';')

    df_actual_data = actual_data.loc[(actual_data['brand'] == brand)
                                     & (actual_data['subscr_type'] == subscr_type)
                                     & (actual_data['pricecat'] == pricecat)
                                     & (actual_data['Date'] >= Test_Begin_Date)
                                     & (actual_data['Date'] <= Test_End_Date)
                                     ]

    df_predicted_data = predicted_data.loc[(predicted_data['brand'] == brand)
                                           & (predicted_data['subscr_type'] == subscr_type)
                                           & (predicted_data['pricecat'] == pricecat)
                                           & (predicted_data['Date'] >= Test_Begin_Date)
                                           & (predicted_data['Date'] <= Test_End_Date)
                                           ]

    mean_absolute_perc_error = pr.mean_absolute_perc_error(df_actual_data['newcheck'], df_predicted_data['newcheck'])
    print("mean_absolute_perc_error: ", mean_absolute_perc_error)

    differences = pr.calculate_diff_model_res(df_actual_data, df_predicted_data)
    print("differences: ")
    print(differences)


def get_accuracy_per_flow(forecast_path=c.FORECAST_FILEPATH,
                          start_date=c.FORECAST_BEGIN_DATE,
                          end_date=c.LATEST_COMPLETE_ACTUALS_DATE,
                          info=True):
    """
    provided forecast path which contains both actuals and predictions,
    which is created by using 'add_overlapping_actuals' = True in conf.py
    calculates accuracies per flow type

    Args:
        forecast_path (str): path to the file with forecast

    Returns:

    """
    actuals = pd.read_csv(forecast_path, sep=';')
    actuals = actuals.drop(columns=['nettosaldo', 'churnpercentage', 'print'])

    print('calculating accuracy based on actuals from {} to {}'.format(start_date, end_date))

    actuals = actuals[(actuals['Date'] >= str(start_date)) &
                      (actuals['Date'] <= str(end_date))]

    forecast = actuals[actuals.forecast == 1]
    true = actuals[actuals.forecast == 0]

    forecast = forecast.drop('forecast', 1)
    true = true.drop('forecast', 1)

    assert len(true) > 0, 'Not enough actuals for desired dates to compare with predictions.' \
                          ' Check if predictions were created with add_overlapping_actuals flag' \
                          '=True in conf.py'

    true = true[true.subscr_type.isin(forecast.subscr_type.unique())]
    true = true[true.pricecat.isin(forecast.pricecat.unique())]

    if info:
        print('\nactuals contain:')
        for subscr_type in true.subscr_type.unique():
            print(subscr_type, true[true.subscr_type == subscr_type].pricecat.unique())

        print('\npredictions contain:')
        for subscr_type in forecast.subscr_type.unique():
            print(subscr_type, forecast[forecast.subscr_type == subscr_type].pricecat.unique())

    true = pd.melt(true,
                   id_vars=['Date', "brand", "subscr_type", 'pricecat'],
                   var_name="flow_type",
                   value_name="true")

    forecast = pd.melt(forecast,
                       id_vars=['Date', "brand", "subscr_type", 'pricecat'],
                       var_name="flow_type",
                       value_name="pred")

    compare = pd.merge(true,
                       forecast, on=['Date', 'brand', 'subscr_type', 'pricecat', 'flow_type'],
                       how='inner')

    compare['error'] = np.abs((compare['true'] - compare['pred']) / compare['true'])
    compare = compare.groupby(['brand', 'subscr_type', 'pricecat', 'flow_type']).mean()['error'].reset_index()
    compare = compare.rename(columns={'error': 'MAPE'})
    compare['accuracy'] = 1 - compare['MAPE']

    compare.to_excel(c.ACCURACY_SAVE_PATH,
                     index=False)

    print('\nsaved accuracy matrix to {}'.format(c.ACCURACY_SAVE_PATH))
