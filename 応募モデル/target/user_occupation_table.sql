SELECT
    mo.member_id,
    mo.occupation_id occupation_id1
FROM
    jstaff.members m
    INNER JOIN jstaff.member_occupations mo ON m.id = mo.member_id
WHERE
    m.last_logined BETWEEN CURRENT_DATE - INTERVAL '1 month' AND CURRENT_DATE
    AND m.magazine = 1
    AND m.state = 'active'
