import logging
from sql_queries.integration_layer_ddl import ddl_create_integration_layer_db, dict_integration_layer_standard_lookups, \
    schema_flights, schema_city_demographics
from constants import dict_dbs_locations, dict_dbs_names
from helper_functions.initialize_spark_session import initialize_spark_session
import os
from pyspark.sql.functions import col

logging.basicConfig(level=logging.INFO, format="%(asctime)s: %(levelname)s: %(message)s ")

if __name__ == '__main__':
    spark = initialize_spark_session('create_integration_layer')

    from delta.tables import *

    # Creating the integration_layer database in spark sql
    try:

        db_name = dict_dbs_names.get('INTEGRATION_LAYER_NAME')
        db_loc = dict_dbs_locations.get('INTEGRATION_LAYER_LOC')

        spark.sql(
            ddl_create_integration_layer_db.format(integration_layer_db_name=db_name, integration_layer_db_loc=db_loc))

        spark.sql(f'USE {db_name}')

        logging.info(f'{db_name} has been created.')

    except Exception as e:
        logging.error(f'Failed to create the {db_name} db in spark sql,{e}')
        spark.stop()
        raise Exception(f'Failed to create the {db_name}, {e}')

    # getting a list of tables names already in the db to check if they already exist
    try:
        df_exist_tables = spark.sql('SHOW TABLES')

    except Exception as e:
        logging.error(f'Failed to retrieve tables names,{e}')
        spark.stop()
        raise Exception(f'Failed to retrieve tables names,{e}')

    # creating integration_layer standard lookups
    try:
        # Looping over the spark schemas to create them in HDFS
        for table_name, table_schema in dict_integration_layer_standard_lookups.items():
            if df_exist_tables.filter(col("tableName").isin(table_name.lower())).select("tableName").count() == 0:
                table_loc = os.path.join(db_loc, table_name)

                # An empty df with a table schema to save it as delta, as current delta supports creating tables using dataframe syntax only
                df = spark.createDataFrame(spark.sparkContext.emptyRDD(), table_schema)

                # Saving the Dataframe into the corresponding path on HDFS
                df.write.format("delta").save(table_loc)

                # Creating the table in Spark SQL schema
                spark.sql(f"""CREATE TABLE {db_name}.{table_name} USING DELTA LOCATION '{table_loc}'""")

                logging.info(f'{table_name} has been created in {db_name}')

    except Exception as e:
        logging.error(f"Failed to create {table_name},{e}")
        spark.stop()
        raise Exception(f"Failed to create {table_name},{e}")

    # Creating Flights fact table, this is separated because this should be partitioned by date
    try:

        if df_exist_tables.filter(col("tableName").isin('FLIGHTS'.lower())).select("tableName").count() == 0:
            flights_loc = os.path.join(db_loc, 'FLIGHTS')

            # An empty df with a table schema to save it as delta, as current delta supports creating tables using dataframe syntax only
            flights_df = spark.createDataFrame(spark.sparkContext.emptyRDD(), schema_flights)

            # Saving the Dataframe into the corresponding path on HDFS
            flights_df.write.partitionBy(['YEAR', 'MONTH']).format("delta").save(flights_loc)

            # Creating the table in Spark SQL schema
            spark.sql(f"""CREATE TABLE {db_name}.FLIGHTS USING DELTA LOCATION '{flights_loc}'""")
            # spark.sql("""CREATE TABLE INTEGRATION_LAYER.'FLIGHTS' USING DELTA LOCATION 'hdfs://localhost:9000/FLIGHTS_DL/INTEGRATION_LAYER/FLIGHTS'""")

            logging.info(f'FLIGHTS has been created in {db_name}')

    except Exception as e:
        logging.error(f"Failed to create FLIGHTS table,{e}")
        spark.stop()
        raise Exception(f"Failed to create FLIGHTS,{e}")

    # Creating City Demographics
    try:

        if df_exist_tables.filter(col("tableName").isin('CITY_DEMOGRAPHICS'.lower())).select("tableName").count() == 0:
            table_loc = os.path.join(db_loc, 'CITY_DEMOGRAPHICS')

            # An empty df with a table schema to save it as delta, as current delta supports creating tables using dataframe syntax only
            table_df = spark.createDataFrame(spark.sparkContext.emptyRDD(), schema_city_demographics)

            # Saving the Dataframe into the corresponding path on HDFS
            table_df.write.format("delta").save(table_loc)

            # Creating the table in Spark SQL schema
            spark.sql(f"""CREATE TABLE {db_name}.CITY_DEMOGRAPHICS USING DELTA LOCATION '{table_loc}'""")

            logging.info(f'CITY_DEMOGRAPHICS has been created in {db_name}')

    except Exception as e:
        logging.error(f"Failed to create CITY_DEMOGRAPHICS table,{e}")
        spark.stop()
        raise Exception(f"Failed to create CITY_DEMOGRAPHICS,{e}")
