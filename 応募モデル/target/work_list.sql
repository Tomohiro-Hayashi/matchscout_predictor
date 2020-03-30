SELECT wb.id work_id,
    wb.company_id,--除外求人設定にcompany_idを使う
    wb.age_upper,
    wb.gender work_gender,
    wb.salary,
    wb.salary_system,
    wb.salary_options
FROM jstaff.work_base wb
    --掲載中の企業のみ抽出
INNER JOIN jstaff.companies c
  ON wb.company_id = c.id
INNER JOIN jstaff.company_scores cs
  ON wb.company_id = cs.company_id
  AND wb.state LIKE '%jstaff_run%'
  AND wb.state NOT LIKE '%unchecked%'
  AND wb.state NOT LIKE '%deleted%'
  AND c.state NOT LIKE '%deleted%'
  AND (cs.term_compliance IS NULL OR cs.term_compliance IN ('important', 'default'))
--不正企業へのレコメンド防止
INNER JOIN margaret.companies mc
  ON wb.company_id = mc.jstaff_company_id
  AND mc.company_type_id <> 6
