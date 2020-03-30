SELECT wsp.work_id, wsp.exp_id, wsp.exp_check_number
FROM jstaff.work_search_parameters wsp
WHERE wsp.exp_id <> -1;
