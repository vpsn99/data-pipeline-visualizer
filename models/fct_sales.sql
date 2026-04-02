with orders as (
    select * from {{ ref('stg_orders') }}
),
customers as (
    select * from {{ ref('stg_customers') }}
)
select
    c.customer_name,
    sum(o.amount) as total_amount,
    count(*) as order_count
from orders o
inner join customers c
    on o.customer_id = c.customer_id
   and o.region_id = c.region_id
where o.amount > 0
group by c.customer_name
having sum(o.amount) > 100