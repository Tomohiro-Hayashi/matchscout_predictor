WITH
--対象ユーザー抽出
members AS (
	SELECT m.id member_id, CASE WHEN hope_cnt.cnt = 1 THEN 0 ELSE 1 END filter_case
--	ROUND(RANDOM(), 0) groups
	FROM jstaff.members m
	  INNER JOIN (
	    SELECT mo.member_id, COUNT(DISTINCT mo.occupation_id) cnt
	    FROM jstaff.member_occupations mo
	    GROUP BY mo.member_id
	  ) hope_cnt ON hope_cnt.member_id = m.id
	WHERE
	  -- m.last_logined BETWEEN '2019-12-06 00:00:00' AND '2020-01-06 00:00:00'
		m.last_logined BETWEEN CURRENT_DATE - INTERVAL '1 month' AND CURRENT_DATE
	  AND m.magazine = 1
	  AND m.state = 'active'
	  AND RIGHT(m.id, 1) in (1,3,5,7,9)
),
--対象求人抽出
works AS (
	SELECT wb.id work_id, wb.company_id--除外求人設定にcompany_idを使う
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
),
--除外する組み合わせ
exceptions AS (
	SELECT a.member_id, wb.company_id
	FROM jstaff.applications a
	  INNER JOIN jstaff.work_base wb ON a.work_id = wb.id
	WHERE a.member_id IS NOT NULL
	  AND wb.company_id IS NOT NULL
	UNION ALL
	SELECT s.member_id, s.company_id
	FROM jstaff.scout s
	WHERE s.member_id IS NOT NULL
	  AND s.company_id IS NOT NULL
	  AND ( s.created_at BETWEEN CURRENT_DATE - INTERVAL '1 month' AND CURRENT_DATE
			-- s.created_at BETWEEN '2019-12-06 00:00:00' AND '2020-01-06 00:00:00'
	    OR s.is_read = 1)
),
--組み合わせを都道府県マッチに限定する
pref_filter AS (
	SELECT m.member_id, w.work_id, m.filter_case
--	, m.groups
	FROM members m
	  INNER JOIN jstaff.member_locations ml ON m.member_id = ml.member_id
	  ,works w
	  INNER JOIN jstaff.work_branch_cities wbc ON w.work_id = wbc.work_id
	WHERE m.member_id ||'-'|| w.company_id NOT IN (SELECT ex.member_id||'-'||ex.company_id FROM exceptions ex)
	  AND ml.pref_id = wbc.pref_id
	GROUP BY m.member_id, w.work_id, m.filter_case
--	, m.groups
),

--以下、occupation_similarityテーブルを作る
member_list AS (
	SELECT member_id, COUNT(id) id_num
	FROM jstaff.member_occupations mo
	GROUP BY member_id
	HAVING id_num >= 2
),
member_hope_occupation AS (
	SELECT mo.member_id, oname.id, oname.name
	FROM jstaff.member_occupations mo
	  INNER JOIN jstaff.occupation_names oname ON mo.occupation_id = oname.id
	WHERE mo.member_id in (SELECT member_id FROM member_list)
	GROUP BY mo.member_id, oname.id, oname.name
),
member_hope_occupation_diag AS (
	SELECT a.id occupation_id, a.name occupation_name, COUNT(DISTINCT a.member_id) uu
	FROM member_hope_occupation a
	GROUP BY a.id, a.name
),
member_hope_occupation_cross AS (
	SELECT a.id occupation_id_a, b.id occupation_id_b, COUNT(DISTINCT a.member_id) uu
	FROM member_hope_occupation a
	  INNER JOIN member_hope_occupation b ON a.member_id = b.member_id
	GROUP BY a.id, b.id
),
occupation_similarities AS (
	SELECT ab.occupation_id_a, ab.occupation_id_b, ab.uu*1.0/least(a.uu, b.uu) similarity
	FROM member_hope_occupation_diag a
	  LEFT JOIN member_hope_occupation_cross ab ON a.occupation_id = ab.occupation_id_a
	  LEFT JOIN member_hope_occupation_diag b ON b.occupation_id = ab.occupation_id_b
),

--組み合わせを職種でフィルタする
filtered_list AS (
	SELECT p.member_id, p.work_id, MAX(os.similarity) max_similarity
--	, p.groups
	FROM pref_filter p
	  INNER JOIN jstaff.member_occupations mo ON p.member_id = mo.member_id
	  INNER JOIN jstaff.work_base wb ON p.work_id = wb.id
	  INNER JOIN jstaff.work_occupation wo ON wb.id = wo.work_id
	  INNER JOIN occupation_similarities os ON mo.occupation_id = os.occupation_id_a AND wo.occupation_id = os.occupation_id_b
	  INNER JOIN jstaff.estimated_application_unit_price eaup ON wb.id = eaup.work_id
	WHERE (p.filter_case = 0 AND mo.occupation_id = wo.occupation_id)
	  OR p.filter_case = 1
	GROUP BY p.member_id, p.work_id, p.filter_case
--	, p.groups
	, eaup.estimated_mean_application_unit_price
	HAVING max_similarity >= 0.20
	  AND eaup.estimated_mean_application_unit_price >= 4000
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
	  m.id IN (SELECT member_id FROM members)
	  AND m.magazine = 1
	  AND m.state = 'active'
),

user_pref AS (
	SELECT
	  m.id member_id,
	  listagg(DISTINCT pref_id, ',') user_pref_id
	FROM
	  jstaff.members m
	  LEFT JOIN jstaff.member_locations ml ON m.id = ml.member_id
	  LEFT JOIN jstaff.prefs p ON ml.pref_id = p.id
	WHERE
	  m.id IN (SELECT member_id FROM members)
	  AND m.magazine = 1
	  AND m.state = 'active'
	GROUP BY
	  m.id
),

user_occupation AS (
	SELECT
	  m.id member_id,
	  listagg(mo.occupation_id, ',') user_occupation_id,
	  hope_oc_count.hope_oc_count
	FROM
	  jstaff.members m
	  LEFT JOIN jstaff.member_occupations mo ON m.id = mo.member_id
	  LEFT JOIN (
	  	SELECT mo.member_id, COUNT(DISTINCT mo.id) hope_oc_count
	  	FROM jstaff.member_occupations mo
	  	GROUP BY mo.member_id
	  ) hope_oc_count ON hope_oc_count.member_id = mo.member_id
	WHERE
	  m.id IN (SELECT member_id FROM members)
	  AND m.magazine = 1
	  AND m.state = 'active'
	GROUP BY
	  m.id,
	  hope_oc_count
),

user_exp AS (
	SELECT
	  m.id member_id,
	  listagg(aer.exp_id, ',') user_exp_id,
	  listagg(aer.check_number, ',') user_exp_id_check_number
	FROM
	  jstaff.members m
	  LEFT JOIN jstaff.application_exp_relations aer ON m.id = aer.member_id
	WHERE
	  m.id IN (SELECT member_id FROM members)
	  AND m.magazine = 1
	  AND m.state = 'active'
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
	  m.id IN (SELECT member_id FROM members)
	  AND m.magazine = 1
	  AND m.state = 'active'
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
)

SELECT
  fl.member_id,
  fl.work_id,
--  fl.groups,
  list.age,
  list.gender,
  list.wanted_annualpay,
  list.education_type,
  pref.user_pref_id,
  occupation.user_occupation_id,
  occupation.hope_oc_count,
  exp.user_exp_id,
  exp.user_exp_id_check_number,
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
  filtered_list fl
  LEFT JOIN user_list list ON fl.member_id = list.member_id
  LEFT JOIN user_pref pref ON fl.member_id = pref.member_id
  LEFT JOIN user_occupation occupation ON fl.member_id = occupation.member_id
  LEFT JOIN user_exp exp ON fl.member_id = exp.member_id
  LEFT JOIN user_licentiate licentiate ON fl.member_id = licentiate.member_id
  LEFT JOIN work_base wb ON wb.work_id = fl.work_id
;
