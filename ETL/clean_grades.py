import os, sys

pathname = os.path.dirname(sys.argv[0])
full_pathname = os.path.abspath(pathname)
split_pathname = full_pathname.split(sep="mvesc")
base_pathname = os.path.join(split_pathname[0], "mvesc")
parentdir = os.path.join(base_pathname, "ETL")
sys.path.insert(0,parentdir)

from mvesc_utility_functions import clean_column,\
    postgres_pgconnection_generator

def clean_grades(clean_schema):
    """
    Python wrapper for sql script 

    :param str clean_schema: name of the clean schema
    :rtype: None
    """
    with postgres_pgconnection_generator() as connection:
        with connection.cursor() as cursor:

            # term type
            cursor.execute("""
            alter table {s}.all_grades add column clean_term text;
            alter table {s}.all_grades 
            alter column clean_term type text using
            case
            when lower(term) like '%year%final%' 
              or lower(term) like '%final%' 
              or lower(term_type) like '%final%' 
            then 'final'
            when lower(term) like '%1%sem%' then 'semester 1'
            when lower(term) like '%2%sem%' then 'semester 2'
            when lower(term) like '%9%week%' 
              or lower(term) like '%nine%week%'
              or lower(term) like '%quarter%' or lower(term) like '%grad%per%'
              then case
                when lower(term) like '%1%' then 'quarter 1'
                when lower(term) like '%2%' then 'quarter 2'
                when lower(term) like '%3%' then 'quarter 3'
                when lower(term) like '%4%' then 'quarter 4'
                else 'quarter'
              end
            when lower(term) like '%6%week%' or lower(term) like '%six%week%'
              then case
                when lower(term) like '%1%' then 'six weeks 1'
                when lower(term) like '%2%' then 'six weeks 2'
                when lower(term) like '%3%' then 'six weeks 3'
                when lower(term) like '%4%' then 'six weeks 4'
                when lower(term) like '%5%' then 'six weeks 5'
                when lower(term) like '%6%' then 'six weeks 6'
              end
            when lower(term) in ('1st','2nd','3rd','4th')
              and lower(term_type) = 'term' or lower(term_type) = 'quarter'
              then case
                when lower(term) like '%1%' then 'quarter 1'
                when lower(term) like '%2%' then 'quarter 2'
                when lower(term) like '%3%' then 'quarter 3'
                when lower(term) like '%4%' then 'quarter 4'
              end
            when lower(term) in ('1st','2nd','3rd','4th')
              and lower(term_type) = 'interim'
              then case
                when lower(term) like '%1%' then 'mid-quarter 1'
                when lower(term) like '%2%' then 'mid-quarter 2'
                when lower(term) like '%3%' then 'mid-quarter 3'
                when lower(term) like '%4%' then 'mid-quarter 4'
              end
            when lower(term) in ('1st','2nd','3rd','4th')
              and lower(term_type) = 'exam'
              then case
                when lower(term) like '%1%' then 'exam quarter 1'
                when lower(term) like '%2%' then 'exam quarter 2'
                when lower(term) like '%3%' then 'exam quarter 3'
                when lower(term) like '%4%' then 'exam quarter 4'
              end
            end;""".format(s=clean_schema))

            # term length
            cursor.execute("""
            alter table {clean_schema}.all_grades add column 
              percent_of_year float;
            alter table {clean_schema}.all_grades alter column percent_of_year 
              type float using
            case
              when clean_term like 'final' then 0
              when clean_term like 'exam' then 0
              when clean_term like 'semester%' then .5
              when clean_term like 'quarter%' then .25
              when clean_term like 'six weeks%' then 1/6.0
            end;""".format(clean_schema=clean_schema))

            # grade 
            cursor.execute("""
            alter table {clean_schema}.all_grades alter column grade 
            type int using
            case
              when grade like '**' then null
              when grade like '13' or grade like '14' then 23
              when grade like 'PS%' or grade like '-2%' then -1
              when grade like 'KG' then 0
              when grade like 'IN' or grade like 'DR' then null
              else grade::int
            end;""".format(clean_schema=clean_schema))
            
            # course code is ignored

            # course name is not standardized here, but is aggregated
            # in temporary tables in the grade feature generation code

            # school year
            cursor.execute("""
            alter table {s}.all_grades alter column school_year type int 
            using substring(school_year,1,4)::int;""".format(s=clean_schema))

            # district
            cursor.execute("""
            alter table {s}.all_grades alter column district type text using
            case when district like 'Maysville%' then 'Maysville'
                 when district like 'Ridgewood%' then 'Ridgewood'
                 when district like 'Franklin%' then 'Franklin'
                 else district
            end;""".format(s=clean_schema))
            
        connection.commit()
