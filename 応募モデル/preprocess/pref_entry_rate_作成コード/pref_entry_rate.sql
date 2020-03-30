WITH

visit_list AS (
	SELECT al.media_user_id member_id, al.media_item_id work_id, al.hit_time,
	    MAX(CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END) entry_flg
	FROM jl.access_logs al
    	LEFT JOIN jstaff.applications a ON al.media_user_id = a.member_id AND al.media_item_id = a.work_id
    	LEFT JOIN jstaff.application_event_log ael ON a.id = ael.application_id
    		AND ael.event = 'application'
    		AND ael.created_at >= al.hit_time
	WHERE
		al.page_type = 'detail'
		AND al.media_user_id NOT IN  ('', 'undefined')
		AND al.media_item_id <> ''
    GROUP BY al.media_user_id, al.media_item_id, al.hit_time
)
    SELECT ml.pref_id user_pref_id, wbc.pref_id work_area_id,
        COUNT(DISTINCT CASE WHEN vl.entry_flg = 1 THEN vl.member_id || '-' || vl.work_id ELSE NULL END) *1.0 /COUNT(DISTINCT vl.member_id || '-' || vl.work_id) entry_rate
    FROM visit_list vl
        INNER JOIN jstaff.member_locations ml ON vl.member_id = ml.member_id
        INNER JOIN jstaff.work_branch_cities wbc ON vl.work_id = wbc.work_id
    GROUP BY ml.pref_id, wbc.pref_id
    HAVING COUNT(DISTINCT CASE WHEN vl.entry_flg = 1 THEN vl.member_id || '-' || vl.work_id ELSE NULL END) >= 10
;
