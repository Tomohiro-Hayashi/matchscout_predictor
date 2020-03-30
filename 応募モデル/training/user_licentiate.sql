SELECT alr.member_id, listagg(alr.licentiate_id, ',') user_licentiate_id
FROM jstaff.application_licentiate_relations alr
WHERE alr.member_id is not null
GROUP BY alr.member_id;
