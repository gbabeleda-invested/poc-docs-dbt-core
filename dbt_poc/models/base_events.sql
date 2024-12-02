with 
    raw as (
        
        select

            transaction_id,
            purchase_price,
            product_value,
            product_name,
            first_name,
            last_name,
            email,
            gender,
            customer_country,
            client_country,
            transaction_date

        from {{ source('dagster', 'events_table') }}

    )

select * from raw