WITH source AS (
    SELECT * FROM {{ source('stackoverflow_raw', 'tags') }}
),

renamed AS (
    SELECT
        id,
        tag_name,
        count,
        excerpt_post_id,
        wiki_post_id
    FROM source
)

SELECT *
FROM renamed