SELECT s.member_id,
    s.company_id
FROM jstaff.scout s
WHERE s.member_id IS NOT NULL
  AND s.company_id IS NOT NULL
  AND s.is_read = 1
UNION ALL
SELECT a.member_id,
    wb.company_id
FROM jstaff.applications a
  INNER JOIN jstaff.work_base wb ON a.work_id = wb.id
WHERE a.member_id IS NOT NULL
  AND wb.company_id IS NOT NULL
