-- Output the number of movies in each category, sorted descending.
SELECT c.name, COUNT(*) as film_count
FROM film f JOIN film_category fc ON f.film_id = fc.film_id
JOIN category c on fc.category_id = c.category_id
group by c.name
ORDER BY film_count DESC;

-- Output the 10 actors whose movies rented the most, sorted in descending order.
select a.first_name, a.last_name, COUNT(*) as rental_count
from actor a
join film_actor fa on a.actor_id = fa.actor_id
join inventory i on fa.film_id = i.film_id
join rental r on i.inventory_id = r.inventory_id
group by a.actor_id, a.first_name, a.last_name
order by rental_count desc
limit 10;

-- Output the category of movies on which the most money was spent.
select c.name, SUM(p.amount) as total_spending
from category c
join film_category fc on c.category_id = fc.category_id
join inventory i on fc.film_id = i.film_id
join rental r on i.inventory_id = r.inventory_id
join payment p on r.rental_id = p.rental_id
group by c.category_id, c.name
order by total_spending desc
limit 1;

-- Исправленный запрос (СТЕ).
WITH sums_spendings AS (
    SELECT c.name, SUM(p.amount) AS total_spending
    FROM category c
    JOIN film_category fc ON c.category_id = fc.category_id
    JOIN inventory i ON fc.film_id = i.film_id
    JOIN rental r ON i.inventory_id = r.inventory_id
    JOIN payment p ON r.rental_id = p.rental_id
    GROUP BY c.category_id, c.name
    ORDER BY total_spending DESC
)
SELECT *
FROM sums_spendings
LIMIT 1;

--Вариант с DENSE_RANK() для ничьи.
WITH sums_spendings AS (
    SELECT c.name, SUM(p.amount) AS total_spending
    FROM category c
    JOIN film_category fc ON c.category_id = fc.category_id
    JOIN inventory i ON fc.film_id = i.film_id
    JOIN rental r ON i.inventory_id = r.inventory_id
    JOIN payment p ON r.rental_id = p.rental_id
    GROUP BY c.category_id, c.name
),
ranked AS (
    SELECT name, total_spending,
           DENSE_RANK() OVER (ORDER BY total_spending DESC) AS rnk
    FROM sums_spendings
)
SELECT name, total_spending
FROM ranked
WHERE rnk = 1
ORDER BY total_spending DESC;

-- Print the names of movies that are not in the inventory.
-- Write a query without using the IN operator.
select f.title
from film f
where not exists (
select 1
from inventory i
where i.film_id = f.film_id);

-- Output the top 3 actors who have appeared the most in movies in the “Children” category.
-- If several actors have the same number of movies, output all of them.
with appearance_count as (
select a.first_name, a.last_name, COUNT(f.film_id) as movies_count
from actor a
join film_actor fa on a.actor_id = fa.actor_id
join film f on fa.film_id = f.film_id
join film_category fc on f.film_id = fc.film_id
join category c on fc.category_id = c.category_id
where c.name = 'Children'
group by a.actor_id, a.first_name, a.last_name
)
select first_name, last_name, movies_count
from appearance_count
where movies_count IN (select distinct movies_count FROM appearance_count
order by movies_count desc
limit 3)
order by movies_count desc;

-- Output cities with the number of active and inactive customers (active - customer.active = 1).
-- Sort by the number of inactive customers in descending order.
select ci.city,
sum(case when cu.active = 1 then 1 else 0 end) as active_customers,
sum(case when cu.active = 0 then 1 else 0 end) as inactive_customers
from city ci
join address a on ci.city_id = a.city_id
join customer cu on a.address_id = cu.address_id
group by ci.city
order by inactive_customers desc;

-- Output the category of movies that have the highest number of total rental hours in the city
-- (customer.address_id in this city) and that start with the letter “a”.
-- Do the same for cities that have a “-” in them. Write everything in one query.
with category_city_hours as (
select c.name as category_name, ci.city,
SUM(COALESCE(EXTRACT(EPOCH FROM (r.return_date - r.rental_date)) / 3600, 0)) AS total_rental_hours
from category c
join film_category fc on c.category_id = fc.category_id
join film f on fc.film_id = f.film_id
join inventory i on f.film_id = i.film_id
join rental r on i.inventory_id = r.inventory_id
join customer cus on r.customer_id = cus.customer_id
join address a on cus.address_id = a.address_id
join city ci on a.city_id = ci.city_id
group by c.name, ci.city)
(select 'starts_with_a' as city_type, category_name,
ROUND(SUM(total_rental_hours))::int as total_hours from category_city_hours
where city ILIKE 'a%'
group by category_name
order by total_hours desc
limit 1)

union all

(select 'has_dash' as city_type, category_name, total_hours
from (
select category_name,
ROUND(SUM(total_rental_hours))::int as total_hours,
DENSE_RANK() over (order by ROUND(SUM(total_rental_hours))::int DESC) as rnk
from category_city_hours
where city like '%-%'
group by category_name
) sub
where rnk = 1
order by total_hours desc);