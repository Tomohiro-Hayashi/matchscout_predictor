WITH
--対象組抽出
entry_list AS (
    SELECT
      a.member_id,
      a.work_id,
      CASE WHEN ael.application_id IS NOT NULL THEN 1 ELSE 0 END hire_flg
    FROM
      --応募のあった求職者-求人の組に絞る
      jstaff.applications a
      --採用のあった求職者-求人
      LEFT JOIN jstaff.application_event_log ael ON ael.application_id = a.id
        AND DATE_DIFF('MONTH', a.created, ael.created_at) BETWEEN 0 AND 3--採用確認までの期間95日以内が全体の95%。
        AND ael.event = 'pre_hire_confirm'
    WHERE
      a.created BETWEEN CURRENT_DATE - INTERVAL '27 MONTH' AND CURRENT_DATE - INTERVAL '3 MONTH'
      --多重応募ユーザーを除外する
      AND a.member_id NOT IN (
        SELECT media_user_id
        FROM jl.access_logs
        WHERE hit_time BETWEEN CURRENT_DATE - INTERVAL '27 MONTH' AND CURRENT_DATE - INTERVAL '3 MONTH'
          AND page_type = 'finish'
        GROUP BY media_user_id
        HAVING COUNT(DISTINCT media_item_id) >= 20--2年間での応募数上位1%が20。外れ値として除外。
      )
    ORDER BY
      a.member_id
),

user_list AS (
	SELECT
	  m.id member_id,
	  DATEDIFF('YEAR', m.birthday, CURRENT_DATE) age,
	  m.gender,
	  m.wanted_annualpay,
	  m.education_type
	FROM
	  jstaff.members m
	WHERE
	  m.id IN (SELECT member_id FROM entry_list)
	  AND m.magazine = 1
	  AND m.id not in (SELECT member_id FROM jl_ad.hellowork_members)
	  AND m.media_id not in (4,50,81)
),

user_exp AS (
	SELECT
	  m.id member_id,
	  listagg(aer.exp_id, ',') user_exp_id,
	  listagg(aer.check_number, ',') user_exp_check_number
	FROM
	  jstaff.members m
	  LEFT JOIN jstaff.application_exp_relations aer ON m.id = aer.member_id
	WHERE
	  m.id IN (SELECT member_id FROM entry_list)
	  AND m.magazine = 1
	GROUP BY
	  m.id
),

user_licentiate AS (
	SELECT
	  m.id member_id,
	  listagg(licentiate_id, ',') user_licentiate_id
	FROM
	  jstaff.members m
	  LEFT JOIN jstaff.application_licentiate_relations alr
	    ON m.id = alr.member_id
	WHERE
	  m.id IN (SELECT member_id FROM entry_list)
	  AND m.magazine = 1
	GROUP BY
	  m.id
),

work_base AS (
	SELECT wb.id work_id,
	  wb.employment_system,
	  wb.salary,
	  wb.salary_system,
	  wb.salary_options,
	  wb.features,
	  wb.holidays,
	  wb.age_lower,
	  wb.age_upper,
	  wb.management_exp
	FROM jstaff.work_base wb
	WHERE wb.id IN (SELECT work_id FROM entry_list)
)

SELECT
  el.member_id,
  el.work_id,
  el.hire_flg,
  list.age,
  list.gender,
  list.wanted_annualpay,
  list.education_type,
  exp.user_exp_id,
  exp.user_exp_check_number,
  licentiate.user_licentiate_id,
  wb.employment_system,
  wb.salary,
  wb.salary_system,
  wb.salary_options,
  wb.features,
  wb.holidays,
  wb.age_lower,
  wb.age_upper
FROM
  entry_list el
  INNER JOIN user_list list ON el.member_id = list.member_id
  INNER JOIN user_exp exp ON el.member_id = exp.member_id
  INNER JOIN user_licentiate licentiate ON el.member_id = licentiate.member_id
  INNER JOIN work_base wb ON wb.work_id = el.work_id
;
