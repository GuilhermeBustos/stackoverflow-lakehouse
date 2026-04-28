{{
    config(
        partition_by={
            'field': 'creation_date',
            'data_type': 'timestamp',
            'granularity': 'month'
        },
        cluster_by=['owner_user_id', 'id']
    )
}}

WITH source AS (
    SELECT * FROM {{ source('stackoverflow_raw', 'posts_questions') }}
),

renamed AS (
    SELECT
        id,
        title,
        body,
        accepted_answer_id,
        answer_count,
        comment_count,
        community_owned_date,
        creation_date,
        favorite_count,
        last_activity_date,
        last_edit_date,
        last_editor_display_name,
        last_editor_user_id,
        owner_display_name,
        owner_user_id,
        parent_id,
        post_type_id,
        score,
        tags,
        view_count
    FROM source
)

SELECT *
FROM renamed