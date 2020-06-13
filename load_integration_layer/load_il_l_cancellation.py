from helper_functions.initialize_spark_session import initialize_spark_session
from pyspark.sql.functions import col
from sql_queries.sql_constants import dict_dbs_locations, dict_dbs_names
from sql_queries.sql_constants import missing_val_replace_alphanumeric,missing_val_replace_numeric


def load_l_cancellation(spark, integration_layer_loc, landing_zone_name):
    delta_l_cancellation = DeltaTable.forPath(spark, integration_layer_loc + '/L_CANCELLATION')

    df_LZ_l_cancellation = spark.sql(f"""
        SELECT 
        CODE
        ,DESCRIPTION
        FROM {landing_zone_name}.L_CANCELLATION
    """)

    delta_l_cancellation.alias("oldData") \
        .merge(df_LZ_l_cancellation.alias("newData"), "oldData.CODE = newData.CODE") \
        .whenMatchedUpdate(set={"DESCRIPTION": col("newData.DESCRIPTION")}) \
        .whenNotMatchedInsert(values={"CODE": col("newData.CODE"), "DESCRIPTION": col("newData.DESCRIPTION")}) \
        .execute()


if __name__ == '__main__':
    spark = initialize_spark_session('load_il_l_cancellation')
    from delta.tables import *

    integration_layer_loc = dict_dbs_locations.get('INTEGRATION_LAYER_LOC')
    landing_zone_name = dict_dbs_names.get('LANDING_ZONE_NAME')

    load_l_cancellation(spark, integration_layer_loc, landing_zone_name)