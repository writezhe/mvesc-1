import os, sys
parentdir = os.path.abspath('/home/zzhang/mvesc/ETL')
sys.path.insert(0,parentdir)
from feature_utilities import *()

import yaml

def df2postgres(df, table_name, nrows=-1, if_exists='fail', schema='raw'):
    """ dump dataframe object to postgres database
    
    :param pandas.DataFrame df: dataframe
    :param int nrows: number of rows to write to table;
    :return str table_name: table name of the sql table
    :rtype str
    """
    # create a postgresql engine to wirte to postgres
    engine = postgres_engine_generator()
    
    #write the data frame to postgres
    if nrows==-1:
        df.to_sql(table_name, engine, schema=schema, index=False, if_exists=if_exists)
    else:
        df.iloc[:nrows, :].to_sql(table_name, engine, schema=schema, index=False, if_exists=if_exists)
    return table_name

def get_table_of_student_in_grade_which_year():
    """
    """

    # sql_agg_by_grade_year = """create table clean.grade_year_max_pairs as
    # (select student_lookup, grade, max(school_year) from clean.all_snapshots group by student_lookup, grade);"""

    with postgres_pgconnection_generator() as connection:
        # read in clean.oaaogt table
        # oaa_raw = read_table_to_df(connection, 'oaaogt_numeric', schema = 'clean', nrows = -1)
        all_snapshots = read_table_to_df(connection, 'all_snapshots', schema = 'clean', nrows = -1)
    
    # summarize all_snapshots to figure out the year for each student's test grade
    #   use max year to choose
    year_took_oaa = all_snapshots.groupby(['student_lookup', 'grade']).agg({'school_year': 'max'})
    year_took_oaa = year_took_oaa.reset_index('grade')

    wide_year_took_oaa = year_took_oaa.pivot(columns='grade', values='school_year')
    wide_year_took_oaa.columns = ['was_in_grade_{}'.format(int(x)) for x in wide_year_took_oaa.columns]
    wide_year_took_oaa.reset_index(inplace=True)
    print('appropriate table created in python')

    # write to postgres
    df2postgres(wide_year_took_oaa, 'grade_year_max_pairs', schema = 'clean', if_exists = 'replace')
    # print confirmation
    print('grade_year_max_pairs has been created from dataframe')


def convert_oaa_ogt_to_numeric():
    """ creates clean.oaaogt_numeric

    """
    with postgres_pgconnection_generator() as connection:
        # read in clean.oaaogt table
        oaa_raw = read_table_to_df(connection, 'oaaogt', schema = 'clean', nrows = -1)
    
    # store original for debugging
    orig_oaa_raw = oaa_raw
    
    # drop ogt columns
    oaa_raw = oaa_raw.loc[:, 'student_lookup':'eighth_socstudies_ss']

    # get unique tests from oaa
    uniqueColNames = pd.Series(pd.Series([x[:-3] for x in oaa_raw.columns]).unique())
    uniqueColNames = uniqueColNames[uniqueColNames.str.contains('fourth_write') == False]
    list_of_year_test_types = uniqueColNames[6:]
    print(list_of_year_test_types)

    # mapping for the non-numeric values
    map_in_place_cheating_to_none = {'DNA':None, 'INV':None, 'DNS':None, '99':None, 'TOG':None}
    map_new_col_for_cheating_indicator = {'INV':'cheat', None:'missing'}
    
    for year_test_type in list_of_year_test_types:
        if (oaa_raw[year_test_type+'_ss'].dtype == np.float64 or oaa_raw[year_test_type+'_ss'].dtype == np.int64):
            print(year_test_type + ' is already a numeric')
        else:
            # make mapping replacements and
            # make a new indicator column for cheat/no-cheat
            oaa_raw[year_test_type+'_ss'].replace(map_in_place_cheating_to_none, inplace = True)
            oaa_raw[year_test_type + '_cheat'] = oaa_raw[year_test_type+'_ss'].map(map_new_col_for_cheating_indicator)

            # convert a weird backtick to a 1 (assumed) in strings
            #   debug by printing the weird values to make sure conversion is okay
            print(oaa_raw[year_test_type+'_ss'][oaa_raw[year_test_type+'_ss'].str.contains("`") == True])
            oaa_raw[year_test_type+'_ss'] = oaa_raw[year_test_type+'_ss'].str.replace('`', '1')
            
            # strip any leftover non-numeric characters
            oaa_raw[year_test_type+'_ss'] = oaa_raw[year_test_type+'_ss'].str.replace(pat = '[^0-9]+', repl = "")

            # make numeric switchover
            oaa_raw[year_test_type+'_ss'] = pd.to_numeric(oaa_raw[year_test_type+'_ss'])

            # need to replace the missing values in the newly created column
            oaa_raw[year_test_type+'_cheat'].fillna('not_a_num', inplace = True)
            oaa_raw[year_test_type+'_cheat'].replace({'not_a_num':0, 'cheat':1, 'missing':None}, inplace = True)

    # write table as oaaogt_numeric
    df2postgres(oaa_raw, 'oaaogt_numeric', schema = 'clean', if_exists = 'replace')
    # print confirmation
    print('oaaogt_numeric has been created')
    # return list of columns
    return list_of_year_test_types

def create_aggregate_stats_table(cursor, list_of_year_test_types):
    """ Make an aggregate temporary table
    """

    # join the grade year pairs
    
    grade_year_pairs = ['was_in_grade_{}'.format(x) for x in range(3,9)]
    grade_year_pairs = ', '.join(grade_year_pairs)

    sql_join_to_temp_table = """create temp table oaa_with_grade_year as
    (select t1.*, {list_of_grades} from clean.oaaogt_numeric as t1 
    left join clean.grade_year_max_pairs as t2 
    on t1.student_lookup = t2.student_lookup);""".format(list_of_grades = grade_year_pairs)
    # execute
    cursor.execute(sql_join_to_temp_table)

    corresponding_grade_dict = {'third' : 'was_in_grade_3',
        'fourth' : 'was_in_grade_4',
        'fifth' : 'was_in_grade_5',
        'sixth' : 'was_in_grade_6',
        'seventh' : 'was_in_grade_7',
        'eighth' : 'was_in_grade_8'}

    # create a separate aggregate table
    sql_create_agg_table = """drop table if exists agg_oaa_stats;
    create temp table agg_oaa_stats as
    (select {corresponding_grade} as year_test_taken,
        avg({score_column}) as {mean_col_name},
        count({score_column}) as {count_col_name},
        stddev_samp({score_column}) as {stddev_col_name}
        from oaa_with_grade_year group by {corresponding_grade});
        """.format(score_column = list_of_year_test_types.iloc[0] + "_ss",
                   mean_col_name = list_of_year_test_types.iloc[0] + "_mean",
                   count_col_name = list_of_year_test_types.iloc[0] + "_count",
                   stddev_col_name = list_of_year_test_types.iloc[0] + "_std",
                   corresponding_grade = corresponding_grade_dict[list_of_year_test_types.iloc[0].split("_")[0]])
    sql_create_agg_table += """
    update only agg_oaa_stats
    set year_test_taken =
        case
        when year_test_taken is null then 3000
        else year_test_taken
        end;"""
    # execute
    cursor.execute(sql_create_agg_table)    

    print("looping through and creating aggregates")
    prev_temp_table_name = "agg_oaa_stats"
    for test_name in list_of_year_test_types[1:]:
        print(test_name)

        sql_join_script = """
        create temp table {temp_table_name} as
        (select agg.*, t2.{mean_col_name},
            t2.{count_col_name}, t2.{stddev_col_name}
        from {prev_temp_table_name} as agg left join
            (select case 
                when {corresponding_grade} is null then 3000
                else {corresponding_grade}
                end 
                as year_test_taken, 
                avg({score_column}) as {mean_col_name},
                count({score_column}) as {count_col_name},
                stddev_samp({score_column}) as {stddev_col_name}
                from oaa_with_grade_year group by {corresponding_grade}) as t2
            on agg.year_test_taken = t2.year_test_taken);""".format(score_column = test_name + "_ss",
                   mean_col_name = test_name + "_mean",
                   count_col_name = test_name + "_count",
                   stddev_col_name = test_name + "_std",
                   corresponding_grade = corresponding_grade_dict[test_name.split("_")[0]],
                   temp_table_name = test_name + "_temp",
                   prev_temp_table_name = prev_temp_table_name)
        # assign for next iteration
        prev_temp_table_name = test_name + "_temp"
        # execute
        cursor.execute(sql_join_script)

    # Finally save final oaa aggregates table in clean
    print("finished making many temp tables, save into schema")
    sql_save_temp_table = """drop table if exists clean.oaa_aggregates;
    create table clean.oaa_aggregates as
    (select * from {final_temp_table_name});""".format(final_temp_table_name = list_of_year_test_types.iloc[-1]+"_temp")
    cursor.execute(sql_save_temp_table)

def normalize_oaa_scores(cursor, list_of_year_test_types):
    """ makes a temporary table to perform the normalization for each test and joins it to a final table
    """

    corresponding_grade_dict = {'third' : 'was_in_grade_3',
        'fourth' : 'was_in_grade_4',
        'fifth' : 'was_in_grade_5',
        'sixth' : 'was_in_grade_6',
        'seventh' : 'was_in_grade_7',
        'eighth' : 'was_in_grade_8'}

    for test_name in list_of_year_test_types[0:1]:
        print(test_name)
        # create temporary table for calcuation
        sql_do_calculation = """drop table if exists {temp_table_name};
        create temp table {temp_table_name} as
        (select t1.student_lookup, t1.{test_name},
            t2.year_test_taken, t2.{mean_col_name}, 
            t2.{count_col_name}, t2.{stddev_col_name} from
            oaa_with_grade_year as t1 left join clean.oaa_aggregates as t2
            on t1.{corresponding_grade} = t2.year_test_taken);
        """.format(test_name = test_name + "_ss",
                   mean_col_name = test_name + "_mean",
                   count_col_name = test_name + "_count",
                   stddev_col_name = test_name + "_std",
                   temp_table_name = test_name + "_temp",
                   corresponding_grade = corresponding_grade_dict[test_name.split("_")[0]])

    # create temporary 

def generate_raw_snapshot_features(replace=False):
    schema, table = "model", "snapshots"
    with postgres_pgconnection_generator() as connection:
        with connection.cursor() as cursor:
            if replace:
                # make initial tables
                get_table_of_student_in_grade_which_year()
                list_of_year_test_types = convert_oaa_ogt_to_numeric()
            else:
                oaa_raw = read_table_to_df(connection, 'oaaogt', schema = 'clean', nrows = -1)
                # drop ogt columns
                oaa_raw = oaa_raw.loc[:, 'student_lookup':'eighth_socstudies_ss']
                # get unique tests from oaa
                uniqueColNames = pd.Series(pd.Series([x[:-3] for x in oaa_raw.columns]).unique())
                uniqueColNames = uniqueColNames[uniqueColNames.str.contains('fourth_write') == False]
                list_of_year_test_types = uniqueColNames[6:]

            print("Making aggregate OAA table in Clean Schema")
            print(list_of_year_test_types)
            create_aggregate_stats_table(cursor, list_of_year_test_types)
            connection.commit()

            # # merge in with snapshots
            # update_column_with_join(cursor, table, 
            #                         column_list = list_of_temp_cols, 
            #                         source_table = 'temp_snapshot_table')
            # print('Finished adding raw features from snapshots')

            # connection.commit()

            # # generate temp table for age-based snapshot features
            # list_of_temp_cols = blank(cursor)
            # # merge in with snapshots
            # update_column_with_join(cursor, table, 
            #                         column = list_of_temp_cols, 
            #                         source_table = 'temp_snapshot_table')
            # print 'Finished adding age-based features from snapshots'

            # optional parameters:
            #    source_column - if the source has a different name than desired
            #    source_schema - if the source is not a temporary table

def generate_x(replace=False):
    schema, table = "model", "test_scores"
    with postgres_pgconnection_generator() as connection:
        with connection.cursor() as cursor:
            create_feature_table(cursor, table, replace=replace)
            
            # generate temp table for raw snapshot features
            list_of_temp_cols = create_temp_table_of_raw_test_scores(cursor)
            # merge in with snapshots
            update_column_with_join(cursor, table, 
                                    column = list_of_temp_cols, 
                                    source_table = 'temp_test_table')
            print 'Finished adding raw features from test scores'
                
            # optional parameters:
            #    source_column - if the source has a different name than desired
            #    source_schema - if the source is not a temporary table