import os
import pickle

import pandas as pd

import constants as c
from Models import processing


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
        if exog is not None:
            exog = exog.values.reshape(-1, 1)

        preds = model_dict[model_id].predict(X=exog,
                                             n_periods=c.STEPS_AHEAD)

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
    
    if check_exog is True:
        preds = predict_flow(model_dict=model_dict,
                             model_id=config['id'],
                             start_date=start_date,
                             end_date=end_date,
                             model_type=config['model'],
                             exog=exog_predict)
        
        endog_col = processing.get_endog_name(config)
        df_preds = processing.update_output_matrix(df_preds, preds, config, endog_col)
        
    else:
        rerun_ids.append(flow)

    return df_preds, rerun_ids


def model_predict(brand=None,
                  sub_type=None,
                  info=True,
                  start_date=c.FORECAST_BEGIN_DATE,
                  end_date=c.FORECAST_END_DATE,
                  campaigns_agg_path=c.CAMPAIGN_CLUSTERS_AGGREGATED_PATH,
                  campaigns_active_path=c.CAMPAIGN_CLUSTERS_ACTIVE_PATH
                  ):

    if (brand is None) or (sub_type is None):
        raise ValueError("Please specify brand and sub_type for prediction")

    df, df_campaign = processing.read_data(cutoff_date=c.TRAIN_END_DATE,
                                           data_path=c.SWITCH_TRANS_FINAL_PATH,
                                           campaigns_agg_path=campaigns_agg_path,
                                           campaigns_active_path=campaigns_active_path)

    model_dict = pickle.load(open(os.path.join(c.PKL_SAVE_DIR, brand.upper() + '_' + sub_type.upper() + '.pkl'), 'rb'))
    relations = processing.read_relations(c.RELATIONS_SRC_PATH)

    df_preds = pd.DataFrame()
    rerun_ids = []

    flow_ids = processing.sort_ids(relations=relations,
                                   brand=brand,
                                   sub_type=sub_type)

    for flow in flow_ids:
        if info:
            print('predicting {}'.format(flow))

        df_preds, rerun_ids = predict(flow=flow,
                                      df=df,
                                      model_dict=model_dict,
                                      df_preds=df_preds,
                                      df_campaign=df_campaign,
                                      relations=relations,
                                      rerun_ids=rerun_ids,
                                      start_date=start_date,
                                      end_date=end_date
                                      )

        assert len(rerun_ids) == 0, 'dependencies mismatch, unable to finish predictions {}'.format(rerun_ids)

    df_preds = processing.format_predictions(df_preds)
    df_preds = processing.calculate_active_subscribers(df_actuals=df,
                                                       df_preds=df_preds,
                                                       brand=brand,
                                                       sub_type=sub_type)
    df_preds = processing.add_churn_pct_v2(df_preds)

    return df_preds
