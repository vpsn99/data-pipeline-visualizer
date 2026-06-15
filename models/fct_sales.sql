select
    customer_name,
    sum(amount) as total_amount,
    count(*) as order_count
from {{ ref('int_customer_orders') }}
group by customer_name
having sum(amount) > 100