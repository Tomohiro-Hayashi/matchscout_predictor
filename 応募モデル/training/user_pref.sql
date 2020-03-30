SELECT
  m.id member_id,
  listagg(DISTINCT pref_id, ',') user_pref_id
FROM
  jstaff.members m
  LEFT JOIN jstaff.member_locations ml ON m.id = ml.member_id
  LEFT JOIN jstaff.prefs p ON ml.pref_id = p.id
WHERE
  m.last_logined BETWEEN CURRENT_DATE - INTERVAL '28 month' AND CURRENT_DATE - INTERVAL '4 month'
  AND m.magazine = 1
  AND m.state = 'active'
GROUP BY
  m.id
