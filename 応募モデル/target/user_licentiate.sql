SELECT
    alr.member_id,
    listagg(alr.licentiate_id, ',') user_licentiate_id
FROM
    jstaff.application_licentiate_relations alr
    INNER JOIN jstaff.members m ON alr.member_id = m.id
    LEFT JOIN jl_ad.hellowork_members hm ON m.id = hm.member_id
    LEFT JOIN jstaff.applications a ON m.id = a.member_id
WHERE
    m.last_logined BETWEEN CURRENT_DATE - INTERVAL '1 month' AND CURRENT_DATE
    AND m.magazine = 1
    AND m.state = 'active'
    AND hm.member_id IS NULL
    AND a.member_id IS NULL
GROUP BY
    alr.member_id;
