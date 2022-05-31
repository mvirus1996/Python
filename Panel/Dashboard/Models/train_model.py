import itertools
import os
import pickle
import time
import warnings

import numpy as np
import pmdarima as pm
import statsmodels.api as sm

import constants as c
from Models import processing

warnings.simplefilter('ignore')


def fit_model(endog, exog, model_type):
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

        if exog is not None:
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

    best_model = fit_model(endog=endog,
                           exog=exog,
                           model_type=config['model'])

    model_dict.update({config['id']: best_model})

    return model_dict


def train_package(relations, sub_type, brand,
                  df, df_campaign, train_start,
                  train_end):
    """
    Provided brand and package, trains one brand-package combination (e.g. DS-DIGI) in full
    and saves corresponding PKL file to its destination folder

    Args:
        relations ():
        sub_type ():
        brand ():
        df ():
        df_campaign ():
        train_end (str): end date of the training period
        train_start (str): start date of the training period
        brand (str): desired brand for training, one of ['DS','NB']
        sub_type (str): desired package/subcription type for training, e.g. DIGI, or ZADI

    Returns:
        None - saves PKL file to destination
    """
    start_time = time.time()

    relation = relations[(relations.sub_type == sub_type) &
                         (relations.brand == brand)]
    model_dict = {}

    for flow in relation.id.unique():
        config = relation[relation.id == flow].iloc[0].to_dict()
        print('training: {}'.format(config['id']))

        model_dict = train_flow(df=df,
                                df_campaign=df_campaign,
                                config=config,
                                model_dict=model_dict,
                                train_start=train_start,
                                train_end=train_end)

    if model_dict != {}:
        pkl_filepath = os.path.join(c.CURRENT_DIR, 'data', 'PKL File', "{}_{}.pkl".format(brand, sub_type))
        pickle.dump(model_dict, open(pkl_filepath, 'wb'))

        print('dumped PKL to {}'.format(pkl_filepath))
        print('took {:.2f} seconds'.format(time.time() - start_time))

    else:
        print('model dict for {}_{} is empty, not saving it'.format(brand, sub_type))


def train(brand=None,
          sub_type=None,
          train_start=c.TRAIN_BEGIN_DATE,
          train_end=c.TRAIN_END_DATE,
          data_path=c.SWITCH_TRANS_FINAL_PATH,
          campaigns_agg_path=c.CAMPAIGN_CLUSTERS_AGGREGATED_PATH,
          campaigns_active_path=c.CAMPAIGN_CLUSTERS_ACTIVE_PATH,
          relations_path=c.RELATIONS_SRC_PATH
          ):
    """

    Function that trains series one by one in the entire dataset. Accepts training start and end date,
    and path to campaign, customers inflow/outflow and customer relations files

    Args:
        relations_path (str):  path to csv file with flows relationships
        campaigns_active_path (str): path to file which contains activated campaigns
        campaigns_agg_path (str): path to file which contains inflow in the past per campaign
        data_path (str): path to the customer flows data
        train_end (str): end date of the training period
        train_start (str): start date of the training period
        brand (str): desired brand for training, one of ['DS','NB']
        sub_type (str): desired package/subcription type for training, e.g. DIGI, or ZADI

    Returns:

    """
    df, df_campaign = processing.read_data(cutoff_date=train_end,
                                           data_path=data_path,
                                           campaigns_agg_path=campaigns_agg_path,
                                           campaigns_active_path=campaigns_active_path)

    relations = processing.read_relations(relations_path)

    if (brand is None) & (sub_type is None):
        for brand in relations.brand.unique():
            for sub_type in relations.sub_type.unique():
                train_package(relations=relations,
                              sub_type=sub_type,
                              brand=brand,
                              df=df,
                              df_campaign=df_campaign,
                              train_start=train_start,
                              train_end=train_end)

    elif (brand is not None) and (sub_type is None):
        for sub_type in relations.sub_type.unique():
            train_package(relations=relations,
                          brand=brand,
                          sub_type=sub_type,
                          df=df,
                          df_campaign=df_campaign,
                          train_start=train_start,
                          train_end=train_end)

    elif (brand is not None) and (sub_type is not None):
        train_package(relations=relations,
                      sub_type=sub_type,
                      brand=brand,
                      df=df,
                      df_campaign=df_campaign,
                      train_start=train_start,
                      train_end=train_end)

    else:
        raise ValueError("please specify both brand "
                         "and package type, or only brand, "
                         "or set both to None"
                         " to train all models")
