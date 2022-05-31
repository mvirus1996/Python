import itertools
import math

import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
from sklearn.metrics import mean_absolute_percentage_error

import constants as c

def add_churn_pct(df):
    #  Calculates churn percentage
    df = df.set_index('Date')
    df_cache = df.groupby(['brand', 'subscr_type', 'pricecat']).apply(
        lambda x: x['churncheck'] / x['currentcheck'].shift(1)).reset_index()

    df_cache.rename(columns={0: 'churnpercentage'}, inplace=True)
    df_cache.rename(columns={'predicted_mean': 'churnpercentage'}, inplace=True)
    df = df.merge(df_cache, how='left', on=['brand', 'subscr_type', 'pricecat', 'Date'])

    df['churnpercentage'][df['churnpercentage'] > 1] = 1
    df['churnpercentage'][df['churnpercentage'] < 0] = 0
    print('max churn %', df['churnpercentage'].max())
    print('min churn %', df['churnpercentage'].min())

    df['churnpercentage'] = df['churnpercentage'].fillna(0)
    return df


def add_churn_pct_v2(df_preds, info=False):
    """
    Provided dataframe with predictions, calculates churn percentage
    for each brand, package type and price type combination

    Args:
        df_preds ():
        info ():

    Returns:

    """
    churn = df_preds.set_index("Date").groupby(['brand', 'subscr_type', 'pricecat']).apply(
        lambda x: x['churncheck'] / x['currentcheck'].shift(1)).reset_index()

    if 'Date' not in churn:
        churn = churn.melt(id_vars=["brand", "subscr_type", "pricecat"],
                           var_name="Date",
                           value_name="churnpercentage")

    if (0 in churn.columns) or ('predicted_mean' in churn.columns):
        churn = churn.rename(columns={0: 'churnpercentage',
                                      "predicted_mean": 'churnpercentage'})

    churn['churnpercentage'][churn['churnpercentage'] > 1] = 1
    churn['churnpercentage'][churn['churnpercentage'] < 0] = 0

    churn = churn.sort_values(['brand', 'subscr_type', 'pricecat', 'Date'])
    churn = churn.fillna(0).round(6)

    df_preds = pd.merge(df_preds, churn,
                        how='left',
                        on=['brand', 'subscr_type', 'pricecat', 'Date'])
    if info:
        print('max churn %', df_preds['churnpercentage'].max())
        print('min churn %', df_preds['churnpercentage'].min())
    
    if 'churnpercentage_x' in df_preds.columns:
        del df_preds['churnpercentage_x']
        df_preds.rename(columns={'churnpercentage_y': 'churnpercentage'}, inplace=True)
    return df_preds


def calculate_diff_model_res(actual, forecast):
    df1 = actual
    df2 = forecast

    df1.sort_values('Date')
    df2.sort_values('Date')
    colNames = [i for i in
                "newcheck;churncheck;switcher_outflow;trans_outflow;inflow_transformers;inflow_switchers;currentcheck".split(
                    ";")]
    data = []
    for _, row in df1.iterrows():
        val1 = df2.loc[(df2['brand'] == row['brand'])
                       & (df2['pricecat'] == row['pricecat'])
                       & (df2['subscr_type'] == row['subscr_type'])]

        ans = {}
        val1 = val1.reset_index()['index']
        for i in colNames:
            ans[i] = round(row[i] - list(df2.loc[val1][i])[0], 2)
        data.append(ans)

    data = pd.DataFrame(data)
    return data
    # data.to_csv(os.path.join(os.getcwd(), "csv files", "forecast_diff.csv"), sep=";")


def mean_absolute_perc_error(y_true, y_pred):
    mape = mean_absolute_percentage_error(y_true, y_pred)
    return mape


def debug(brand, sub_type, price_type, flow, model, results):
    print('Params for {} {} {} {}'.format(brand, sub_type, price_type, flow))

    if model == 'pmdarima':
        print(results.params())
        print(results.summary())

    elif model == 'statsmodels':
        print(results.summary())
        print(results.param_terms)


def calculate_diff_model_res(df1, df2):
    df1.fillna(0)
    df2.fillna(0)
    df1['Date'] = pd.to_datetime(df1['Date'], dayfirst=True)
    df2['Date'] = pd.to_datetime(df2['Date'], dayfirst=True)

    listOfComb = []
    for i in ['brand', 'subscr_type', 'pricecat']:
        listOfComb.append(list(df1[i].unique()))

    colNames = [i for i in
                "newcheck;churncheck;switcher_outflow;trans_outflow;inflow_transformers;inflow_switchers;currentcheck".split(
                    ";")]

    mon_year = df1['Date'].dt.strftime('%b-%Y')
    df1.insert(1, 'mon_year', mon_year)
    mon_year = df2['Date'].dt.strftime('%b-%Y')
    df2.insert(1, 'mon_year', mon_year)

    data = []
    for combs in list(itertools.product(*listOfComb)):
        val = df1.loc[(df1['brand'] == combs[0])
                      & (df1['subscr_type'] == combs[1])
                      & (df1['pricecat'] == combs[2])
                      & (df1['Date'] >= '2020-07-01')
                      & (df1['Date'] <= '2021-12-01')]

        if not val.empty:
            for _, row in val.iterrows():
                val1 = df2.loc[(df2['mon_year'] == row['mon_year'])
                               & (df2['brand'] == row['brand'])
                               & (df2['pricecat'] == row['pricecat'])
                               & (df2['subscr_type'] == row['subscr_type'])
                               & (df2['Date'] >= '2020-07-31')
                               & (df2['Date'] <= '2021-01-31')]

                ans = {'Date': row['Date'], 'brand': row['brand'], 'subscr_type': row['subscr_type'],
                       'pricecat': row['pricecat']}
                if not val1.empty:
                    val1 = val1.reset_index()['index']
                    for i in colNames:
                        ans[i + '_actual'] = round(row[i], 2)
                        ans[i + '_forecasted'] = round(list(df2.loc[val1][i])[0], 2)
                        ans['diff_' + i] = round(row[i] - list(df2.loc[val1][i])[0], 2)

                    data.append(ans)

    data = pd.DataFrame(data)
    g_list = ['newcheck_actual', 'churncheck_actual', 'switcher_outflow_actual',
              'trans_outflow_actual', 'inflow_transformers_actual', 'inflow_switchers_actual', 'currentcheck_actual',
              'newcheck_forecasted', 'churncheck_forecasted', 'switcher_outflow_forecasted',
              'trans_outflow_forecasted', 'inflow_transformers_forecasted', 'inflow_switchers_forecasted',
              'currentcheck_forecasted',
              'diff_newcheck', 'diff_churncheck', 'diff_switcher_outflow', 'diff_trans_outflow',
              'diff_inflow_transformers',
              'diff_inflow_switchers', 'diff_currentcheck']

    for col in g_list:
        data[col] = data[col].fillna(0)
        data[col] = data[col].astype(int)

    data = data[
        ['Date', 'brand', 'subscr_type', 'pricecat', 'newcheck_actual', 'churncheck_actual', 'switcher_outflow_actual',
         'trans_outflow_actual', 'inflow_transformers_actual', 'inflow_switchers_actual', 'currentcheck_actual',
         'newcheck_forecasted', 'churncheck_forecasted', 'switcher_outflow_forecasted',
         'trans_outflow_forecasted', 'inflow_transformers_forecasted', 'inflow_switchers_forecasted',
         'currentcheck_forecasted',
         'diff_newcheck', 'diff_churncheck', 'diff_switcher_outflow', 'diff_trans_outflow', 'diff_inflow_transformers',
         'diff_inflow_switchers', 'diff_currentcheck']]

    return data


def read_data(cutoff_date=c.TRAIN_END_DATE,
              data_path=c.SWITCH_TRANS_FINAL_PATH,
              campaigns_agg_path=c.CAMPAIGN_CLUSTERS_AGGREGATED_PATH,
              campaigns_active_path=c.CAMPAIGN_CLUSTERS_ACTIVE_PATH):
    """
    Provided end of the training period, and path to data sources
    for main customer flow types and main campaign files,
    returns formatted custmomer and campaign files

    Args:
        cutoff_date ():
        data_path ():
        campaigns_agg_path ():
        campaigns_active_path ():

    Returns:

    """
    df_flows = pd.read_csv(data_path, sep=';')
    df_flows = df_flows.fillna(0).drop_duplicates()

    df_flows['subscr_type'] = df_flows['subscr_type'].replace(
        {'Fractions': 'FRACTIONS', 'Print_full': 'FULL', 'PROMO1': 'PROMO', 'SPNSOR': 'SPONSOR',
         "Weekend": "WEEKEND", "Schools": "SCHOOLS"})
    df_flows['Date'] = pd.to_datetime(df_flows['Date'], dayfirst=True)
    df_flows['Date'] = df_flows['Date'] + pd.offsets.MonthEnd(0)
    df_flows = df_flows[df_flows.Date <= cutoff_date]

    df_campaign_agg = pd.read_csv(campaigns_agg_path, sep=';')
    df_campaign_agg['Date'] = pd.to_datetime(df_campaign_agg['Date'])
    df_campaign_agg['Date'] = df_campaign_agg['Date'].dt.strftime('%Y-%m-%d')
    df_campaign_agg.rename(columns={'amount': 'inflow'}, inplace=True)
    df_campaign_agg = df_campaign_agg.loc[(df_campaign_agg['Date'] <= cutoff_date)]

    df_campaign = pd.read_csv(campaigns_active_path, sep=';')
    df_campaign = df_campaign.loc[df_campaign['active'] == 1].groupby(['brand', 'packagetype', 'prijstype', 'Date'])[
        'inflow'].sum().reset_index()

    df_campaign = df_campaign.append(df_campaign_agg)

    df_campaign['Date'] = pd.to_datetime(df_campaign['Date'])
    df_campaign['Date'] = df_campaign['Date'].dt.strftime('%Y-%m-%d')
    df_campaign['Date'] = pd.DatetimeIndex(df_campaign['Date'])

    df_campaign['packagetype'] = df_campaign['packagetype'].str.upper()

    return df_flows, df_campaign


def debug(brand, sub_type, price_type, flow, model, results):
    print('Params for {} {} {} {}'.format(brand, sub_type, price_type, flow))

    if model == 'pmdarima':
        print(results.params())
        print(results.summary())

    elif model == 'statsmodels':
        print(results.summary())
        print(results.param_terms)


def exo_endo_fix(df_exo, df_endo):
    # Added shape equality for endo & exo
    df_exo.reset_index(inplace=True)
    df_endo_index = df_endo.index
    df_endo_index = df_endo_index.to_frame(index=False, name='Date')
    df_exo = df_endo_index.merge(df_exo, on='Date', how='outer')
    df_exo = df_exo.set_index('Date')
    df_exo = df_exo.fillna(0)

    return df_exo


def filter_df(df, brand, sub_type, pricecat,
              start_date, end_date):
    """
    Privided total flow dataframe returns a dataframe with only one brand, one package and one pricecategory

    Returns:
        df_fitler: a dataframe of one brand, subscription type and price

    """
    df_filter = df.loc[(df['brand'] == brand)
                       & (df['subscr_type'] == sub_type)
                       & (df['pricecat'] == pricecat)
                       & (df['Date'] >= start_date)
                       & (df['Date'] <= end_date)]

    df_filter = df_filter.set_index('Date')

    return df_filter


def get_campaigns(df_campaign, brand, sub_type, pricecat,
                  start_date, end_date):
    """
    Provided campaign df with all packages returns just a slice of df with
    only one brand, package and price type

    Args:
        df_campaign ():
        brand ():
        sub_type ():
        pricecat ():
        start_date ():
        end_date ():

    Returns:
        df_campaign_train: dataframe with only one pricecat
    """
    df_campaign_train = df_campaign.loc[(df_campaign['brand'] == brand)
                                        & (df_campaign['packagetype'] == sub_type)
                                        & (df_campaign['prijstype'] == pricecat)
                                        & (df_campaign['Date'] >= start_date)
                                        & (df_campaign['Date'] <= end_date)]

    df_campaign_train = df_campaign_train.set_index('Date')

    return df_campaign_train


def get_exog(df,
             df_campaign,
             config,
             start_date,
             end_date,
             endog=None,
             align_endog=True):
    """
    Provided config file, prepares an exogenous array for training
    returns exogenous array

    Args:
        df ():
        df_campaign ():
        config ():
        start_date ():
        end_date ():
        endog ():
        align_endog ():

    Returns:

    """
    if config['exog'] == 'campaigns':
        exog = get_campaigns(df_campaign=df_campaign,
                             brand=config['brand'],
                             sub_type=config['sub_type'],
                             pricecat=config['pricecat'],
                             start_date=start_date,
                             end_date=end_date)

        if align_endog:
            exog = exo_endo_fix(exog, endog)

        exog = exog['inflow']

    elif config['exog'] == "other_flow":
        exog = filter_df(df=df,
                         brand=config['brand'],
                         sub_type=config['sub_type'],
                         pricecat=config['exog_pricecat'],
                         start_date=start_date,
                         end_date=end_date)

        exog = exog[config['exog_flow']]

        if 'exog_lag' in config:
            exog = exog.shift(config['exog_lag'].astype(int))

    elif (config['exog'] == np.nan) or (config['exog'] is None) or (math.isnan(config['exog'])):
        exog = None

    else:
        raise ValueError("Exog should be one of 'campaigns', 'other_flow', or 'null'")

    if exog is not None:
        assert exog.isna().sum() != len(exog), 'exog only contains NaNs for {}'.format(config['id'])
        exog = exog.fillna(0)

    return exog


def check_exog(exog_predict, start_date, end_date, config):
    """
    Checks whether exogenous array is ready for prediction
    Provided exogenous array, returns True or False, and an exogenous array back

    Args:
        exog_predict ():
        start_date ():
        end_date ():

    Returns:

    """
    if exog_predict is None:
        check = True

    else:
        if len(exog_predict) == c.STEPS_AHEAD:
            check = True

        elif len(exog_predict) == 0:
            print('resetting exog of {} to 0 due to no exog contents'.format(config['id']))
            exog_predict = exog_predict.reindex(index=pd.date_range(start=start_date,
                                                                    end=end_date,
                                                                    freq="M"))
            exog_predict = exog_predict.fillna(0)
            check = True


        else:
            exog_predict = exog_predict.reindex(index=pd.date_range(start=start_date,
                                                                    end=end_date,
                                                                    freq="M"))
            exog_predict = exog_predict.fillna(0)

            if len(exog_predict) == c.STEPS_AHEAD:
                check = True

            else:
                check = False
                print('reindexing of exog failed for {}'.format(config['id']))

    return exog_predict, check


def get_exog_predict(df_actuals,
                     df_preds,
                     df_campaign,
                     config,
                     start_date,
                     end_date):
    if config['exog'] == 'campaigns':
        exog = get_campaigns(df_campaign=df_campaign,
                             brand=config['brand'],
                             sub_type=config['sub_type'],
                             pricecat=config['pricecat'],
                             start_date=start_date,
                             end_date=end_date)

        exog = exog['inflow']

    elif config['exog'] == "other_flow":
        assert len(df_preds) > 0, 'empty predictions, can not use dependency'

        exog = filter_df(df=df_preds,
                         brand=config['brand'],
                         sub_type=config['sub_type'],
                         pricecat=config['exog_pricecat'],
                         start_date=start_date,
                         end_date=end_date)

        exog = exog[config['exog_flow']]

        if 'exog_lag' in config:
            start_date = pd.to_datetime(start_date) - pd.DateOffset(months=config['exog_lag'])
            end_date = pd.to_datetime(start_date) + pd.DateOffset(months=config['exog_lag'])

            last_actuals = filter_df(df=df_actuals,
                                     brand=config['brand'],
                                     sub_type=config['sub_type'],
                                     pricecat=config['exog_pricecat'],
                                     start_date=start_date,
                                     end_date=end_date)

            last_actuals = last_actuals[config['exog_flow']]

            exog = last_actuals.append(exog)
            exog = exog.shift(config['exog_lag'].astype(int))
            exog = exog.dropna()

    elif (config['exog'] == np.nan) or (config['exog'] is None) or (math.isnan(config['exog'])):
        exog = None

    else:
        raise ValueError("Exog should be one of 'campaigns', 'other_flow', or 'null'")

    return exog


def get_endog_name(config, info=False):
    """
    Gets the endogenous model_id name

    Args:
        config ():

    Returns:

    """
    if info:
        print(config['flow_type'], config['flow_direction'])

    if config['flow_type'] == 'regular':
        if config['flow_direction'] == 'inflow':
            endog_name = 'newcheck'

        elif config['flow_direction'] == 'outflow':
            endog_name = 'churncheck'

    elif config['flow_type'] == 'trans':
        if config['flow_direction'] == 'inflow':
            endog_name = 'inflow_transformers'

        elif config['flow_direction'] == 'outflow':
            endog_name = 'trans_outflow'

    elif config['flow_type'] == 'switcher':
        if config['flow_direction'] == 'inflow':
            endog_name = 'inflow_switchers'

        if config['flow_direction'] == 'outflow':
            endog_name = 'switcher_outflow'

    elif config['flow_type'] == 'active':
        if config['flow_direction'] == 'total':
            endog_name = 'currentcheck'
    else:
        raise ValueError("Wrong flow type or direction specified")

    if info:
        print('result: {}'.format(endog_name))

    return endog_name


def save_business_relations(relations,
                            save_path=c.RELATIONS_BUSINESS_OVERVIEW_PATH):
    """
    Save the same contents as in relations file (model_overview.csv)
    but in a more business-user friendly language

    Accepts path to the original model_overview file,
    returns updated more readable model_overview_business file

    """
    business_version = relations.copy(deep=True)
    business_version.columns = ['Brand', 'Print', 'Package', 'Price', 'Customer',
                                'Direction', 'Depends on', 'Dep Price', 'Dep Direction', 'Lag',
                                "Model", 'Comment']

    business_version['Dep Direction'] = business_version['Dep Direction'].replace('newcheck', 'Inflow')
    business_version['Dep Direction'] = business_version['Dep Direction'].replace('churncheck', 'Outflow')

    business_version['Dep Direction'] = business_version['Dep Direction'].replace('inflow', '')
    business_version.loc[business_version.Model.isna(), 'Model'] = 'To-Do'
    business_version.loc[~business_version.Model.isin(['To-Do', 'Excluded']), 'Model'] = 'Included'

    business_version.to_excel(save_path, index=False)


def read_relations(relations_src_path=c.RELATIONS_SRC_PATH,
                   save_business_view=True):
    """
    Reads relations csv and returns relations dataframe with id

    Args:
        save_business_view (bool): whether to save extra excel file with better naming for business users
        relations_src_path (str): path to relations.csv file

    Returns:

    """

    relations = pd.read_csv(relations_src_path,
                            sep=',')

    if "model" not in relations.columns:
        relations = pd.read_csv(relations_src_path,
                                sep=';')

    if save_business_view:
        save_business_relations(relations=relations,
                                save_path=c.RELATIONS_BUSINESS_OVERVIEW_PATH)

    relations['model'].replace('pm', 'pmdarima', inplace=True)
    relations['sub_type'] = relations['sub_type'].replace({'Fractions': 'FRACTIONS',
                                                           'Print_full': 'FULL',
                                                           "Weekend": "WEEKEND",
                                                           "Schools": "SCHOOLS"})

    relations = relations[~relations['model'].isna()]
    relations = relations[relations['model'] != 'Excluded']

    relations = relations[~relations['flow_direction'].isna()]

    exog_directions = relations[relations.exog == 'other_flow']['exog_flow'].unique()

    assert 'inflow' not in exog_directions, "wrong exog flow in relations file" \
                                            ", should not be 'inflow' for other_flow " \
                                            "exogenous input"

    # flow type goes into model naming
    relations.flow_type = relations.flow_type.replace({"Regular": 'regular',
                                                       "Transformers": "trans",
                                                       "Switchers": "switcher",
                                                       "Active": "active"
                                                       })

    relations.flow_direction = relations.flow_direction.replace({'Inflow': 'inflow',
                                                                 "Outflow": 'outflow',
                                                                 "Total": "total"})

    relations['id'] = relations['brand'] + '_' \
                      + relations['sub_type'] + '_' \
                      + relations['pricecat'].str.lower() + '_' \
                      + relations['flow_type'] + '_' \
                      + relations['flow_direction']

    return relations


def update_output_matrix(df_preds, preds, config, endog_col):
    """
    Updates prediction dataframe with the new predictions

    Args:
        df_preds ():
        preds ():
        config ():
        endog_col ():

    Returns:

    """
    assert preds.isna().sum() == 0, 'nans in predictions'

    preds = preds.to_frame(name=endog_col).copy()
    preds['brand'] = config['brand']
    preds['subscr_type'] = config['sub_type']
    preds['pricecat'] = config['pricecat']
    preds['print'] = config['PrintvsDigi']
    preds = preds.reset_index().fillna(0)
    preds.rename(columns={'index': 'Date'}, inplace=True)

    if len(df_preds.columns) == 0:
        df_preds = preds

    else:
        loc_filter = ((df_preds.brand == config['brand']) &
                      (df_preds.subscr_type == config['sub_type']) &
                      (df_preds.pricecat == config['pricecat']))

        if len(df_preds[loc_filter]) == 0:
            df_preds = df_preds.append(preds)

        else:
            df_preds.loc[loc_filter, endog_col] = preds[endog_col]

    return df_preds


def sort_ids(relations, brand, sub_type):
    """ Sorts ids to first predict flows with no dependencies
        and then to predict items that rely on other flows"""

    relations = relations[(relations.sub_type == sub_type) &
                          (relations.brand == brand)]

    first = relations[relations.exog.isna()].id.tolist()
    second = relations[relations.exog == 'campaigns'].id.tolist()
    last = relations[relations.exog == 'other_flow'].id.tolist()

    sorted_ids = first + second + last

    return sorted_ids


def calculate_active_subscribers(df_actuals, df_preds,
                                 brand, sub_type):
    """
    Provided predictions and actuals, adds actuals to get current check value

    Args:
        df_actuals (pd.DataFrame): actual values
        df_preds (pd.DataFrame): predicted values
        brand (str): brand of interest
        sub_type (str): subscription type of interest

    Returns:

    """
    latest_actuals = df_actuals.loc[(df_actuals['Date'] == c.TRAIN_END_DATE) &
                                    (df_actuals.subscr_type == sub_type) &
                                    (df_actuals.brand == brand)].sort_values(['pricecat', 'Date'])

    latest_actuals['nettosaldo'] = latest_actuals['currentcheck']
    latest_actuals['forecast'] = 0

    if 'currentcheck' in df_preds:
        if df_preds['currentcheck'].isna().sum() == 0:
            df_preds = latest_actuals.append(df_preds)
            print('skip calculation of active subscribers for {} {}, already predicted'.format(brand, sub_type))

        else:
            predicted_current_df = df_preds.loc[~df_preds.currentcheck.isna()]
            no_current_df = df_preds.loc[df_preds.currentcheck.isna()]

            no_current_df = format_active_subscribers(df_preds=no_current_df,
                                                      latest_actuals=latest_actuals)
            df_preds = predicted_current_df.append(no_current_df)

    else:
        df_preds = format_active_subscribers(df_preds=df_preds,
                                             latest_actuals=latest_actuals)

    df_preds[c.FILLNA_COLS] = df_preds[c.FILLNA_COLS].fillna(0)
    df_preds[c.COLUMNS_TO_ROUND] = df_preds[c.COLUMNS_TO_ROUND].astype(int)

    df_preds = df_preds[df_preds['forecast'] == 1]
    df_preds = df_preds.sort_values(['brand', 'subscr_type', 'pricecat', 'Date'])
    df_preds = df_preds.reset_index(drop=True)

    return df_preds


def format_predictions(df_preds):
    """
    Formats predictions in a standardized way, and calculate the net customer flow
    Accepts dataframe with predictions, returns dataframe with an added nettosaldo column,
    where nettosaldo is a calculation of customer flow in that month (inflow - outflow).
    if current active subscribers are directly predicted by the model, skips nettosaldo calculation

    Args:
        df_preds (pd.DataFrame):

    Returns:

    """
    df_preds['forecast'] = 1

    if 'currentcheck' not in df_preds.columns:
        df_preds[c.FILLNA_COLS] = df_preds[c.FILLNA_COLS].fillna(0)

        df_preds['nettosaldo'] = df_preds['newcheck'] \
                                 + df_preds['inflow_switchers'] \
                                 + df_preds['inflow_transformers'] \
                                 - df_preds['churncheck'] \
                                 - df_preds['switcher_outflow'] \
                                 - df_preds['trans_outflow']

        # df_preds['nettosaldo'] = df_preds['nettosaldo'] * (-1)

    elif 'currentcheck' in df_preds.columns:
        if df_preds.currentcheck.isna().sum() == 0:
            pass

        else:
            current_df = df_preds.loc[~df_preds.currentcheck.isna()]
            non_current_df = df_preds.loc[df_preds.currentcheck.isna()]

            non_current_df[c.FILLNA_COLS] = non_current_df[c.FILLNA_COLS].fillna(0)
            non_current_df['nettosaldo'] = non_current_df['newcheck'] \
                                           + non_current_df['inflow_switchers'] \
                                           + non_current_df['inflow_transformers'] \
                                           - non_current_df['churncheck'] \
                                           - non_current_df['switcher_outflow'] \
                                           - non_current_df['trans_outflow']
            # non_current_df['nettosaldo'] = non_current_df['nettosaldo'] * (-1)
            df_preds = current_df.append(non_current_df)

    df_preds = df_preds.drop_duplicates(subset=['brand', 'subscr_type', 'pricecat', 'Date'])

    return df_preds


def format_active_subscribers(df_preds, latest_actuals):
    """
    Accepts dataframe with predictions and returns capped predictions,
    making sure that there is no scenario where outflow is higher than current active subscribers.
    Works by setting active subscribers to 0 if outflow is higher than inflow, and picking up
    the latest active subscribers for new active subscriber calculation

    example:

        month 1: active = 0
        month 2: inflow + 50 outflow - 30 = active: 20
        month 3: inflow + 30 outflow - 70 = active: 0
        month 4: inflow + 50 outflow - 30 = active: 20

    Args:
        df_preds (pd.DataFrame):

    Returns:

    """
    df_preds[c.FILLNA_COLS] = df_preds[c.FILLNA_COLS].fillna(0)
    df_preds['inflow'] = df_preds['newcheck'] + df_preds['inflow_transformers'] + df_preds['inflow_switchers']
    df_preds['outflow'] = df_preds['churncheck'] + df_preds['trans_outflow'] + df_preds['switcher_outflow']

    new_preds = pd.DataFrame()

    for pricecat in df_preds.pricecat.unique():
        latest_df = latest_actuals[latest_actuals.pricecat == pricecat]
        package_df = df_preds[df_preds.pricecat == pricecat]

        package_df = latest_df.append(package_df, ignore_index=False).reset_index(drop=True)
        package_df = package_df.sort_values(['Date']).set_index('Date')

        for row in package_df.iterrows():
            values = row[1]
            date = row[0]

            if date > pd.to_datetime(c.TRAIN_END_DATE):
                prev_date = (date + relativedelta(months=-1)).to_period('M').to_timestamp('M')

                prev_current = package_df.loc[prev_date, 'currentcheck']
                change = values['inflow'] - values['outflow']

                if prev_current + change < 0:
                    package_df.loc[date, 'currentcheck'] = 0

                else:
                    package_df.loc[date, 'currentcheck'] = package_df.loc[prev_date, 'currentcheck'] + values[
                        'inflow'] - values['outflow']

        new_preds = new_preds.append(package_df)

    new_preds = new_preds.reset_index(drop=False)
    new_preds = new_preds.drop(columns=['inflow', 'outflow'])

    return new_preds


def keep_only_forecasted(df_forecast):
    """Caculates how many months we have forecast ahead for
    If we only have actuals in the dataframe, it means there was no forecast
    Returns dataframe only with forecasted series"""

    df_forecast['n_months_forecasted'] = df_forecast.groupby(['brand', 'subscr_type', 'pricecat']).transform('sum')[
        'forecast']

    df_forecast = df_forecast[df_forecast['n_months_forecasted'] != 0]
    df_forecast = df_forecast.drop('n_months_forecasted', 1)

    return df_forecast


def merge_and_save(df_actuals, df_forecast, save_path=c.FORECAST_FILEPATH,
                   static_save_path=c.STATIC_FORECAST_FILEPATH):
    """
    Merges the two dataframes with old actuals and new forecasted figures

    Args:
        df_forecast (DataFrame): df with forecasted values
        df_actuals (DataFrame): df with forecasted actuals, can be overlapping or non-overlapping

    Returns:
        None, returns df_forecast, in any case saves it

    """
    df_actuals['forecast'] = 0

    df_forecast['print'] = np.where(df_forecast.subscr_type.isin(c.DIGI_TYPES), 'Digi', 'Print')
    df_forecast = pd.concat([df_forecast, df_actuals], axis=0).fillna(0)

    df_forecast = df_forecast.sort_values(['brand', 'subscr_type', 'pricecat', 'Date'])
    df_forecast = keep_only_forecasted(df_forecast)

    if len(df_forecast.columns) == len(c.COLUMNS_ORDER):
        df_forecast = df_forecast[c.COLUMNS_ORDER]

    # add churn to both historical and forecasted values
    df_forecast = add_churn_pct_v2(df_forecast)

    df_forecast.to_csv(save_path, sep=';', index=False)
    df_forecast.to_csv(static_save_path, sep=';', index=False)

    print('saved outputs to {}'.format(save_path))
    print('saved static outputs to {}'.format(static_save_path))
    print("prediction successful!")
