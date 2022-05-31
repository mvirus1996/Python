import fire
import pandas as pd

import constants as c
from Models import train_model, predict_model, processing, test_accuracy


def main(info=c.INFO, train=c.TRAIN,
         add_overlapping_actuals=True,
         save_accuracy=c.MEASURE_ACCURACY):

    """ This is the main function that trains the models and
        saves the predictions for the dashboard"""

    if train:
        print('starting training')
        print('using historical data from {} to {}'.format(c.TRAIN_BEGIN_DATE, c.TRAIN_END_DATE))
        print('forecasting from {} to {}'.format(c.FORECAST_BEGIN_DATE, c.FORECAST_END_DATE))
        train_model.train()

    else:
        print('skipping training')

    print('starting predicting')
    print('predicting from {} to {}'.format(c.FORECAST_BEGIN_DATE, c.FORECAST_END_DATE))

    df_forecast = pd.DataFrame()
    relations = processing.read_relations(c.RELATIONS_SRC_PATH)

    for brand in relations.brand.unique():
        brand_relations = relations[relations.brand == brand]

        for sub_type in brand_relations.sub_type.unique():
            df_preds = predict_model.model_predict(brand=brand,
                                                   sub_type=sub_type,
                                                   start_date=c.FORECAST_BEGIN_DATE,
                                                   end_date=c.FORECAST_END_DATE,
                                                   info=info)

            df_forecast = df_forecast.append(df_preds)

    if add_overlapping_actuals:
        df_actuals, _ = processing.read_data(cutoff_date=c.LATEST_COMPLETE_ACTUALS_DATE,
                                             data_path=c.SWITCH_TRANS_FINAL_PATH,
                                             campaigns_agg_path=c.CAMPAIGN_CLUSTERS_AGGREGATED_PATH,
                                             campaigns_active_path=c.CAMPAIGN_CLUSTERS_ACTIVE_PATH)

    else:
        df_actuals, _ = processing.read_data(cutoff_date=c.TRAIN_END_DATE,
                                             data_path=c.SWITCH_TRANS_FINAL_PATH,
                                             campaigns_agg_path=c.CAMPAIGN_CLUSTERS_AGGREGATED_PATH,
                                             campaigns_active_path=c.CAMPAIGN_CLUSTERS_ACTIVE_PATH)

    processing.merge_and_save(df_actuals=df_actuals,
                              df_forecast=df_forecast,
                              save_path=c.FORECAST_FILEPATH,
                              static_save_path=c.STATIC_FORECAST_FILEPATH)

    if save_accuracy:
        test_accuracy.get_accuracy_per_flow(forecast_path=c.FORECAST_FILEPATH,
                                            start_date =c.FORECAST_BEGIN_DATE,
                                            end_date = c.LATEST_COMPLETE_ACTUALS_DATE)


if __name__ == "__main__":
    fire.Fire(main)
