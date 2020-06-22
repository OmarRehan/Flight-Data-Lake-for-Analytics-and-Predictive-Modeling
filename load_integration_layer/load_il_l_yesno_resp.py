from helper_functions.initialize_spark_session import initialize_spark_session
from pyspark.sql.functions import col
from constants import dict_dbs_locations, dict_dbs_names


def load_l_yesno_resp(spark, integration_layer_loc, landing_zone_name):
    delta_l_yesno_resp = DeltaTable.forPath(spark, integration_layer_loc + '/L_YESNO_RESP')

    df_LZ_l_yesno_resp = spark.sql(f"""
        SELECT 
        CAST(CODE AS INTEGER) AS CODE
        ,DESCRIPTION
        FROM {landing_zone_name}.L_YESNO_RESP
    """)

    delta_l_yesno_resp.alias("oldData") \
        .merge(df_LZ_l_yesno_resp.alias("newData"), "oldData.CODE = newData.CODE") \
        .whenMatchedUpdate(set={"DESCRIPTION": col("newData.DESCRIPTION")}) \
        .whenNotMatchedInsert(values={"CODE": col("newData.CODE"), "DESCRIPTION": col("newData.DESCRIPTION")}) \
        .execute()


if __name__ == '__main__':
    spark = initialize_spark_session('load_l_yesno_resp')
    from delta.tables import *

    integration_layer_loc = dict_dbs_locations.get('INTEGRATION_LAYER_LOC')
    landing_zone_name = dict_dbs_names.get('LANDING_ZONE_NAME')

    load_l_yesno_resp(spark, integration_layer_loc, landing_zone_name)
