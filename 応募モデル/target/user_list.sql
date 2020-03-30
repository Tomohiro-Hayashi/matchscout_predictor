SELECT m.id member_id,
    DATE_DIFF('YEAR', m.birthday, CURRENT_DATE) age,
    m.gender user_gender,
    m.wanted_annualpay
FROM jstaff.members m
    LEFT JOIN jl_ad.hellowork_members hm ON m.id = hm.member_id
    LEFT JOIN jstaff.applications a ON m.id = a.member_id
WHERE m.last_logined BETWEEN CURRENT_DATE - INTERVAL '1 month' AND CURRENT_DATE
    AND m.magazine = 1
    AND m.state = 'active'
    AND hm.member_id IS NULL
    AND a.member_id IS NULL
;
