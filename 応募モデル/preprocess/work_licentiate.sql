SELECT wsp.work_id, wsp.licentiate_id work_licentiate_id
FROM jstaff.work_search_parameters wsp
WHERE wsp.licentiate_id<> '-1';
