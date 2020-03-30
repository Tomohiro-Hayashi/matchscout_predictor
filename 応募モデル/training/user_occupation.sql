
SELECT
  m.id member_id,
  listagg(mo.occupation_id, ',') user_occupation_id,
  hope_oc_count.hope_oc_count
FROM
  jstaff.members m
  LEFT JOIN jstaff.member_occupations mo ON m.id = mo.member_id
  LEFT JOIN (SELECT mo.member_id, COUNT(DISTINCT mo.id) hope_oc_count FROM jstaff.member_occupations mo GROUP BY mo.member_id) hope_oc_count
    ON hope_oc_count.member_id = mo.member_id
WHERE
  m.last_logined BETWEEN CURRENT_DATE - INTERVAL '28 month' AND CURRENT_DATE - INTERVAL '4 month'
  AND m.magazine = 1
  AND m.state = 'active'
GROUP BY
  m.id,
  hope_oc_count
