SELECT
	aer.member_id,
	listagg(aer.exp_id, ',') user_exp_id,
	listagg(aer.check_number, ',') user_exp_check_number
FROM
	jstaff.application_exp_relations aer
WHERE
	aer.exp_id <> -1
	AND member_id is not NULL
GROUP BY
	aer.member_id
;
