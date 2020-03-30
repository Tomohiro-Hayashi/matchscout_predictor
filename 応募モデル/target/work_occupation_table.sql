SELECT
    wo.work_id,
    wo.occupation_id occupation_id2
FROM
    jstaff.work_occupation wo
WHERE
    wo.occupation_id IS NOT NULL
;
