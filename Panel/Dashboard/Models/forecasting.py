import itertools
import warnings

import numpy as np
import pandas as pd
import pmdarima as pm
import statsmodels.api as sm

import constants as c
from Models import processing

warnings.simplefilter('ignore')


def train_model(endog, exog, model_type):
    """ Provided model type and endog/exog values trains the model
        and returns the best result specification

    Args:
        exog_name ():
        endog_name ():
        exog_df ():
        endog_df ():
        model_type (str): type of model 'statsmodel' or 'pmdarima'

    Returns:

    """
    if model_type == 'statsmodels':
        p = d = q = range(0, 2)
        pdq = list(itertools.product(p, d, q))
        seasonal_pdq = [(x[0], x[1], x[2], 12)
                        for x in list(itertools.product(p, d, q))]

        aic_best = np.inf
        result_best = None

        for param in pdq:
            for param_seasonal in seasonal_pdq:
                #   try:
                mod = sm.tsa.statespace.SARIMAX(endog=endog,
                                                exog=exog,
                                                order=param,
                                                seasonal_order=param_seasonal,
                                                enforce_stationarity=False,
                                                enforce_invertibility=False)
                results = mod.fit(disp=False)
                if 10 <= results.aic <= aic_best:
                    result_best = results
                    aic_best = results.aic

    elif model_type == "GLS":
        mod = sm.GLS(endog=endog,
                     exog=exog,
                     missing='drop')

        result_best = mod.fit(disp=False, freq="M")

        return result_best

    elif model_type == 'pmdarima':
        exog = exog.fillna(0).values.reshape(-1, 1)

        result_best = pm.auto_arima(y=endog,
                                    X=exog,
                                    trace=False,
                                    suppress_warnings=True,
                                    seasonal=True,
                                    random_seed=16,
                                    start_p=0,
                                    start_q=0,
                                    m=12)


    else:
        raise ValueError('Incorrect model type specified. Model type must be one of pmdarima, GSL or statmodels')

    assert result_best is not None, 'resulting model is None'

    return result_best


def train_flow(df, df_campaign,
               config, model_dict,
               train_start, train_end):
    """Provided relations dict and flow, returns the models for that flow
        by first selecting correct endogenous and exogenous variables, and then
        training the model

    """
    endog_df = processing.filter_df(df=df,
                                    brand=config['brand'],
                                    sub_type=config['sub_type'],
                                    pricecat=config['pricecat'],
                                    start_date=train_start,
                                    end_date=train_end)

    endog_col = processing.get_endog_name(config)

    endog = endog_df[endog_col]

    exog = processing.get_exog(df=df,
                               df_campaign=df_campaign,
                               endog=endog,
                               config=config,
                               start_date=train_start,
                               end_date=train_end,
                               align_endog=True
                               )

    best_model = train_model(endog=endog,
                             exog=exog,
                             model_type=config['model'])

    model_dict.update({config['id']: best_model})

    return model_dict


def predict_flow(model_dict, model_id, start_date,
                 end_date, model_type, exog=None):
    """
    Predicts one flow (one brand, subscription, package, and model id combination
    model id is prijstype + type of customers + direction of flow

    Args:
        model_dict ():
        brand ():
        sub_type ():
        model_id ():
        start_date ():
        end_date ():
        exog ():

    Returns:

    """

    if model_type == 'statsmodels':
        preds = model_dict[model_id].predict(exog=exog,
                                             start=start_date,
                                             end=end_date)

    elif model_type == 'pmdarima':
        exog = exog.values.reshape(-1, 1)

        preds = model_dict[model_id].predict(X=exog,
                                             n_periods=len(exog))

        preds = pd.Series(preds, index=pd.date_range(start=start_date,
                                                     end=end_date, freq="M"))


    elif model_type == 'GLS':
        preds = model_dict[model_id].predict(exog=exog)

    else:
        raise ValueError("Model should be of type statsmodels, pmdarima or GLS not {}".format(model_type))

    preds[preds < 0] = 0
    preds = preds.astype(int)

    return preds


def predict(flow, df,
            df_preds, df_campaign,
            relations, rerun_ids, model_dict,
            start_date=c.FORECAST_BEGIN_DATE,
            end_date=c.FORECAST_END_DATE):
    """
    Provided a flow id and dataframes with actuals, campaigns and latest predictions,
    predicts the value for a given id and updates the df_preds dataframe

    Args:
        flow ():
        df ():
        df_preds ():
        df_campaign ():
        relations ():
        rerun_ids ():
        model_dict ():
        start_date ():
        end_date ():

    Returns:

    """
    config = relations[relations.id == flow].iloc[0].to_dict()

    exog_predict = processing.get_exog_predict(df_actuals=df,
                                               df_preds=df_preds,
                                               df_campaign=df_campaign,
                                               config=config,
                                               start_date=start_date,
                                               end_date=end_date)

    exog_predict, check_exog = processing.check_exog(exog_predict=exog_predict,
                                                     start_date=start_date,
                                                     end_date=end_date,
                                                     config=config)

    if check_exog is False:
        rerun_ids.append(flow)

    else:
        preds = predict_flow(model_dict=model_dict,
                             model_id=config['id'],
                             start_date=start_date,
                             end_date=end_date,
                             model_type=config['model'],
                             exog=exog_predict)

        endog_col = processing.get_endog_name(config)
        df_preds = processing.update_output_matrix(df_preds, preds, config, endog_col)

    return df_preds, rerun_ids
