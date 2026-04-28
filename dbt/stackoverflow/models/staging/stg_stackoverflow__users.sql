{{
    config(
        partition_by={
            'field': 'creation_date',
            'data_type': 'timestamp',
            'granularity': 'month'
        },
        cluster_by=['id']
    )
}}

WITH source AS (
    SELECT * FROM {{ source('stackoverflow_raw', 'users') }}
),

renamed AS (
    SELECT
        id,
        display_name,
        about_me,
        age,
        creation_date,
        last_access_date,
        location,
        reputation,
        up_votes,
        down_votes,
        views,
        profile_image_url,
        website_url
    FROM source
)

SELECT *
FROM renamed