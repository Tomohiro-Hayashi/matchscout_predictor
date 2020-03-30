WITH
malti_entry_user AS (
	SELECT member_id
	FROM jstaff.application_event_log
	WHERE created_at BETWEEN CURRENT_DATE - INTERVAL '27 month' AND CURRENT_DATE - INTERVAL '3 month'
	    AND event = 'application'
	GROUP BY member_id
	HAVING COUNT(DISTINCT application_id) >= 20
),

visit_list AS (
	SELECT al.media_user_id member_id, al.media_item_id work_id, al.hit_time,
	    MAX(CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END) entry_flg
	FROM jl.access_logs al
    	LEFT JOIN jstaff.applications a ON al.media_user_id = a.member_id AND al.media_item_id = a.work_id
    	LEFT JOIN jstaff.application_event_log ael ON a.id = ael.application_id
    		AND ael.event = 'application'
    		AND ael.created_at >= al.hit_time
    		AND DATE_DIFF('day', ael.created_at, al.hit_time) BETWEEN 0 AND 14
	WHERE al.hit_time BETWEEN CURRENT_DATE - INTERVAL '27 month' AND CURRENT_DATE - INTERVAL '3 month'
		AND al.page_type = 'detail'
		AND al.ref_medium = 'organic'
		AND al.media_user_id NOT IN  ('', 'undefined')
		AND media_user_id NOT IN (SELECT member_id FROM malti_entry_user)
		AND al.media_item_id <> ''
    GROUP BY al.media_user_id, al.media_item_id, al.hit_time
),

member_list AS (
    SELECT m.id member_id,
        m.birthday,
        m.gender user_gender,
        m.wanted_annualpay
    FROM jstaff.members m
			LEFT JOIN jl_ad.hellowork_members hm ON m.id = hm.member_id
    WHERE m.magazine = 1
      AND hm.member_id IS NULL
),

work_list AS (
    SELECT wb.id work_id,
        wb.age_upper,
        wb.gender work_gender,
        wb.salary,
        wb.salary_system,
        wb.salary_options
    FROM jstaff.work_base wb
)

SELECT
    DATEDIFF('YEAR', m.birthday, vl.hit_time) age, vl.hit_time,
    m.*, w.*, vl.entry_flg
FROM visit_list vl
    INNER JOIN member_list m ON vl.member_id = m.member_id
    INNER JOIN work_list w ON vl.work_id = w.work_id
;
