SELECT
  wb.id work_id,
  wb.occupation_id occupation_id2
FROM
  jstaff.work_base wb
  INNER JOIN jstaff.occupation_names oc ON wb.occupation_id = oc.id
;
