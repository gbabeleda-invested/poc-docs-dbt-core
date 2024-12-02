with 
    base as (

        select * from {{ ref('base_events') }}

    ),

    finance_report as (

        select 

            customer_country,
            count(transaction_id) as total_transactions

        from base
        where transaction_date between 
            date_trunc('month', current_date) and
            (date_trunc('month', current_date) + interval '1 month - 1 day')
        group by 1

    )

select * from finance_report