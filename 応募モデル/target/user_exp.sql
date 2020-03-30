SELECT
	aer.member_id,
	listagg(aer.exp_id, ',') user_exp_id,
	listagg(aer.check_number, ',') user_exp_check_number
FROM
	jstaff.application_exp_relations aer
	INNER JOIN jstaff.members m ON aer.member_id = m.id
	LEFT JOIN jl_ad.hellowork_members hm ON m.id = hm.member_id
	LEFT JOIN jstaff.applications a ON m.id = a.member_id
WHERE
	m.last_logined BETWEEN CURRENT_DATE - INTERVAL '1 month' AND CURRENT_DATE
	AND m.magazine = 1
	AND m.state = 'active'
	AND hm.member_id IS NULL
	AND a.member_id IS NULL
GROUP BY
	aer.member_id
;
