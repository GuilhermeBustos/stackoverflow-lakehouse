{{
    config(
        cluster_by=['user_id']
    )
}}

WITH source AS (
    SELECT * FROM {{ ref("stg_stackoverflow__users") }}
)

SELECT
    id AS user_id,
    display_name,
    creation_date,
    last_access_date,
    location,
    reputation,
    up_votes,
    down_votes
FROM source