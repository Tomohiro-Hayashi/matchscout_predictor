WITH
entry_list AS (
    SELECT
        a.id application_id,
        a.member_id,
        a.work_id,
        CASE WHEN ael.application_id IS NOT NULL THEN 1 ELSE 0 END hire_flg
    FROM
        jstaff.applications a--応募のあった求職者-求人の組に絞る
        LEFT JOIN jstaff.application_event_log ael ON ael.application_id = a.id--採用のあった求職者-求人
            AND DATE_DIFF('MONTH', a.created, ael.created_at) BETWEEN 0 AND 3--採用確認までの期間95日以内が全体の95%。
            AND ael.event = 'pre_hire_confirm'
    WHERE
        a.member_id <> 0
        AND a.work_id <> 0
        AND a.member_id NOT IN (
        SELECT media_user_id
            FROM jl.access_logs
            WHERE page_type = 'finish'
            GROUP BY media_user_id
            HAVING COUNT(DISTINCT media_item_id) >= 20--2年間での応募数上位1%が20。外れ値として除外。
        )
        AND a.work_id IN (SELECT id FROM jstaff.work_base ORDER BY RANDOM() LIMIT 10000)
)

SELECT
    alr.licentiate_id,
    el.work_id,
    SUM(el.hire_flg) *1.0 /COUNT(DISTINCT el.work_id || '_' || el.member_id) hire_rate
FROM
    jstaff.application_licentiate_relations alr
    INNER JOIN entry_list el ON el.application_id = alr.application_id
GROUP BY
    el.work_id,
    alr.licentiate_id
ORDER BY
    el.work_id,
    alr.licentiate_id
;
