with 
    base as (

        select * from {{ ref('base_events') }}

    ),

    marketing_report as (

        select 

            customer_country,
            sum(product_value) as total_value

        from base
        where transaction_date between 
            date_trunc('month', current_date) and
            (date_trunc('month', current_date) + interval '1 month - 1 day')
        group by 1

    )

select * from marketing_report