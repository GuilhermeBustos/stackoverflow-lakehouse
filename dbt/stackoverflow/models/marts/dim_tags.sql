{{
    config(
        cluster_by=['tag_id']
    )
}}

WITH source AS (
    SELECT * FROM {{ ref("stg_stackoverflow__tags") }}
)

SELECT
    id AS tag_id,
    tag_name,
    count AS tag_count
FROM source