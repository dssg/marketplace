--
-- Update references in meta tables
--
UPDATE django_content_type SET app_label='marketplace' WHERE app_label='dssgmkt';
UPDATE django_migrations SET app='marketplace' WHERE app='dssgmkt';

--
-- Rename deployed tables
--

--
-- Rename table for newspiece to marketplace_newspiece
--
ALTER TABLE "dssgmkt_newspiece" RENAME TO "marketplace_newspiece";
--
-- Rename table for organization to marketplace_organization
--
ALTER TABLE "dssgmkt_organization" RENAME TO "marketplace_organization";
--
-- Rename table for organizationmembershiprequest to marketplace_organizationmembershiprequest
--
ALTER TABLE "dssgmkt_organizationmembershiprequest" RENAME TO "marketplace_organizationmembershiprequest";
--
-- Rename table for organizationrole to marketplace_organizationrole
--
ALTER TABLE "dssgmkt_organizationrole" RENAME TO "marketplace_organizationrole";
--
-- Rename table for pinnedtaskreview to marketplace_pinnedtaskreview
--
ALTER TABLE "dssgmkt_pinnedtaskreview" RENAME TO "marketplace_pinnedtaskreview";
--
-- Rename table for project to marketplace_project
--
ALTER TABLE "dssgmkt_project" RENAME TO "marketplace_project";
--
-- Rename table for projectcomment to marketplace_projectcomment
--
ALTER TABLE "dssgmkt_projectcomment" RENAME TO "marketplace_projectcomment";
--
-- Rename table for projectdiscussionchannel to marketplace_projectdiscussionchannel
--
ALTER TABLE "dssgmkt_projectdiscussionchannel" RENAME TO "marketplace_projectdiscussionchannel";
--
-- Rename table for projectfollower to marketplace_projectfollower
--
ALTER TABLE "dssgmkt_projectfollower" RENAME TO "marketplace_projectfollower";
--
-- Rename table for projectlog to marketplace_projectlog
--
ALTER TABLE "dssgmkt_projectlog" RENAME TO "marketplace_projectlog";
--
-- Rename table for projectrole to marketplace_projectrole
--
ALTER TABLE "dssgmkt_projectrole" RENAME TO "marketplace_projectrole";
--
-- Rename table for projectscope to marketplace_projectscope
--
ALTER TABLE "dssgmkt_projectscope" RENAME TO "marketplace_projectscope";
--
-- Rename table for projecttask to marketplace_projecttask
--
ALTER TABLE "dssgmkt_projecttask" RENAME TO "marketplace_projecttask";
--
-- Rename table for projecttaskrequirement to marketplace_projecttaskrequirement
--
ALTER TABLE "dssgmkt_projecttaskrequirement" RENAME TO "marketplace_projecttaskrequirement";
--
-- Rename table for projecttaskreview to marketplace_projecttaskreview
--
ALTER TABLE "dssgmkt_projecttaskreview" RENAME TO "marketplace_projecttaskreview";
--
-- Rename table for projecttaskrole to marketplace_projecttaskrole
--
ALTER TABLE "dssgmkt_projecttaskrole" RENAME TO "marketplace_projecttaskrole";
--
-- Rename table for signupcode to marketplace_signupcode
--
ALTER TABLE "dssgmkt_signupcode" RENAME TO "marketplace_signupcode";
--
-- Rename table for skill to marketplace_skill
--
ALTER TABLE "dssgmkt_skill" RENAME TO "marketplace_skill";
--
-- Rename table for user to marketplace_user
--
ALTER TABLE "dssgmkt_user" RENAME TO "marketplace_user";
ALTER TABLE "dssgmkt_user_groups" RENAME TO "marketplace_user_groups";
ALTER TABLE "dssgmkt_user_user_permissions" RENAME TO "marketplace_user_user_permissions";
--
-- Rename table for userbadge to marketplace_userbadge
--
ALTER TABLE "dssgmkt_userbadge" RENAME TO "marketplace_userbadge";
--
-- Rename table for usernotification to marketplace_usernotification
--
ALTER TABLE "dssgmkt_usernotification" RENAME TO "marketplace_usernotification";
--
-- Rename table for volunteerapplication to marketplace_volunteerapplication
--
ALTER TABLE "dssgmkt_volunteerapplication" RENAME TO "marketplace_volunteerapplication";
--
-- Rename table for volunteerprofile to marketplace_volunteerprofile
--
ALTER TABLE "dssgmkt_volunteerprofile" RENAME TO "marketplace_volunteerprofile";
--
-- Rename table for volunteerskill to marketplace_volunteerskill
--
ALTER TABLE "dssgmkt_volunteerskill" RENAME TO "marketplace_volunteerskill";

--
-- Rename undeployed tables if exist
--

--
-- Rename table for organizationsocialcause to marketplace_organizationsocialcause
--
ALTER TABLE IF EXISTS "dssgmkt_organizationsocialcause" RENAME TO "marketplace_organizationsocialcause";
--
-- Rename table for projectsocialcause to marketplace_projectsocialcause
--
ALTER TABLE IF EXISTS "dssgmkt_projectsocialcause" RENAME TO "marketplace_projectsocialcause";
--
-- Rename table for usertaskpreference to marketplace_usertaskpreference
--
ALTER TABLE IF EXISTS "dssgmkt_usertaskpreference" RENAME TO "marketplace_usertaskpreference";

--
-- Rename deployed sequences
--

ALTER SEQUENCE dssgmkt_newspiece_id_seq RENAME TO marketplace_newspiece_id_seq;
ALTER SEQUENCE dssgmkt_organization_id_seq RENAME TO marketplace_organization_id_seq;
ALTER SEQUENCE dssgmkt_organizationmembershiprequest_id_seq RENAME TO marketplace_organizationmembershiprequest_id_seq;
ALTER SEQUENCE dssgmkt_organizationrole_id_seq RENAME TO marketplace_organizationrole_id_seq;
ALTER SEQUENCE dssgmkt_pinnedtaskreview_id_seq RENAME TO marketplace_pinnedtaskreview_id_seq;
ALTER SEQUENCE dssgmkt_project_id_seq RENAME TO marketplace_project_id_seq;
ALTER SEQUENCE dssgmkt_projectcomment_id_seq RENAME TO marketplace_projectcomment_id_seq;
ALTER SEQUENCE dssgmkt_projectdiscussionchannel_id_seq RENAME TO marketplace_projectdiscussionchannel_id_seq;
ALTER SEQUENCE dssgmkt_projectfollower_id_seq RENAME TO marketplace_projectfollower_id_seq;
ALTER SEQUENCE dssgmkt_projectlog_id_seq RENAME TO marketplace_projectlog_id_seq;
ALTER SEQUENCE dssgmkt_projectrole_id_seq RENAME TO marketplace_projectrole_id_seq;
ALTER SEQUENCE dssgmkt_projectscope_id_seq RENAME TO marketplace_projectscope_id_seq;
ALTER SEQUENCE dssgmkt_projecttask_id_seq RENAME TO marketplace_projecttask_id_seq;
ALTER SEQUENCE dssgmkt_projecttaskrequirement_id_seq RENAME TO marketplace_projecttaskrequirement_id_seq;
ALTER SEQUENCE dssgmkt_projecttaskreview_id_seq RENAME TO marketplace_projecttaskreview_id_seq;
ALTER SEQUENCE dssgmkt_projecttaskrole_id_seq RENAME TO marketplace_projecttaskrole_id_seq;
ALTER SEQUENCE dssgmkt_signupcode_id_seq RENAME TO marketplace_signupcode_id_seq;
ALTER SEQUENCE dssgmkt_skill_id_seq RENAME TO marketplace_skill_id_seq;
ALTER SEQUENCE dssgmkt_user_groups_id_seq RENAME TO marketplace_user_groups_id_seq;
ALTER SEQUENCE dssgmkt_user_id_seq RENAME TO marketplace_user_id_seq;
ALTER SEQUENCE dssgmkt_user_user_permissions_id_seq RENAME TO marketplace_user_user_permissions_id_seq;
ALTER SEQUENCE dssgmkt_userbadge_id_seq RENAME TO marketplace_userbadge_id_seq;
ALTER SEQUENCE dssgmkt_usernotification_id_seq RENAME TO marketplace_usernotification_id_seq;
ALTER SEQUENCE dssgmkt_volunteerapplication_id_seq RENAME TO marketplace_volunteerapplication_id_seq;
ALTER SEQUENCE dssgmkt_volunteerdetails_id_seq RENAME TO marketplace_volunteerdetails_id_seq;
ALTER SEQUENCE dssgmkt_volunteerskill_id_seq RENAME TO marketplace_volunteerskill_id_seq;

--
-- Rename deployed indexes
--

ALTER INDEX dssgmkt_newspiece_pkey RENAME TO marketplace_newspiece_pkey;
ALTER INDEX dssgmkt_organization_pkey RENAME TO marketplace_organization_pkey;
ALTER INDEX dssgmkt_organizationmembershiprequest_pkey RENAME TO marketplace_organizationmembershiprequest_pkey;
ALTER INDEX dssgmkt_organizationrole_pkey RENAME TO marketplace_organizationrole_pkey;
ALTER INDEX dssgmkt_organizationrole_user_id_organization_id_566bba71_uniq RENAME TO marketplace_organizationrole_user_id_organization_id_566bba71_uniq;
ALTER INDEX dssgmkt_pinnedtaskreview_pkey RENAME TO marketplace_pinnedtaskreview_pkey;
ALTER INDEX dssgmkt_pinnedtaskreview_task_review_id_user_id_0a1a6a52_uniq RENAME TO marketplace_pinnedtaskreview_task_review_id_user_id_0a1a6a52_uniq;
ALTER INDEX dssgmkt_project_pkey RENAME TO marketplace_project_pkey;
ALTER INDEX dssgmkt_projectcomment_pkey RENAME TO marketplace_projectcomment_pkey;
ALTER INDEX dssgmkt_projectdiscussionchannel_pkey RENAME TO marketplace_projectdiscussionchannel_pkey;
ALTER INDEX dssgmkt_projectdiscussionchannel_related_task_id_key RENAME TO marketplace_projectdiscussionchannel_related_task_id_key;
ALTER INDEX dssgmkt_projectfollower_pkey RENAME TO marketplace_projectfollower_pkey;
ALTER INDEX dssgmkt_projectfollower_user_id_project_id_99b84c4f_uniq RENAME TO marketplace_projectfollower_user_id_project_id_99b84c4f_uniq;
ALTER INDEX dssgmkt_projectlog_pkey RENAME TO marketplace_projectlog_pkey;
ALTER INDEX dssgmkt_projectrole_pkey RENAME TO marketplace_projectrole_pkey;
ALTER INDEX dssgmkt_projectrole_user_id_project_id_b594a8de_uniq RENAME TO marketplace_projectrole_user_id_project_id_b594a8de_uniq;
ALTER INDEX dssgmkt_projectscope_pkey RENAME TO marketplace_projectscope_pkey;
ALTER INDEX dssgmkt_projecttask_pkey RENAME TO marketplace_projecttask_pkey;
ALTER INDEX dssgmkt_projecttaskrequirement_pkey RENAME TO marketplace_projecttaskrequirement_pkey;
ALTER INDEX dssgmkt_projecttaskrequirement_skill_id_task_id_e27658b3_uniq RENAME TO marketplace_projecttaskrequirement_skill_id_task_id_e27658b3_uniq;
ALTER INDEX dssgmkt_projecttaskreview_pkey RENAME TO marketplace_projecttaskreview_pkey;
ALTER INDEX dssgmkt_projecttaskrole_pkey RENAME TO marketplace_projecttaskrole_pkey;
ALTER INDEX dssgmkt_projecttaskrole_user_id_task_id_role_f40c7ae5_uniq RENAME TO marketplace_projecttaskrole_user_id_task_id_role_f40c7ae5_uniq;
ALTER INDEX dssgmkt_signupcode_pkey RENAME TO marketplace_signupcode_pkey;
ALTER INDEX dssgmkt_skill_area_name_2fbaad83_uniq RENAME TO marketplace_skill_area_name_2fbaad83_uniq;
ALTER INDEX dssgmkt_skill_pkey RENAME TO marketplace_skill_pkey;
ALTER INDEX dssgmkt_user_groups_pkey RENAME TO marketplace_user_groups_pkey;
ALTER INDEX dssgmkt_user_groups_user_id_group_id_c8dc0e3d_uniq RENAME TO marketplace_user_groups_user_id_group_id_c8dc0e3d_uniq;
ALTER INDEX dssgmkt_user_pkey RENAME TO marketplace_user_pkey;
ALTER INDEX dssgmkt_user_user_permis_user_id_permission_id_4649881a_uniq RENAME TO marketplace_user_user_permis_user_id_permission_id_4649881a_uniq;
ALTER INDEX dssgmkt_user_user_permissions_pkey RENAME TO marketplace_user_user_permissions_pkey;
ALTER INDEX dssgmkt_user_username_key RENAME TO marketplace_user_username_key;
ALTER INDEX dssgmkt_userbadge_pkey RENAME TO marketplace_userbadge_pkey;
ALTER INDEX dssgmkt_userbadge_user_id_type_8a6fc84d_uniq RENAME TO marketplace_userbadge_user_id_type_8a6fc84d_uniq;
ALTER INDEX dssgmkt_usernotification_pkey RENAME TO marketplace_usernotification_pkey;
ALTER INDEX dssgmkt_volunteerapplication_pkey RENAME TO marketplace_volunteerapplication_pkey;
ALTER INDEX dssgmkt_volunteerdetails_pkey RENAME TO marketplace_volunteerdetails_pkey;
ALTER INDEX dssgmkt_volunteerdetails_user_id_key RENAME TO marketplace_volunteerdetails_user_id_key;
ALTER INDEX dssgmkt_volunteerskill_pkey RENAME TO marketplace_volunteerskill_pkey;
ALTER INDEX dssgmkt_volunteerskill_user_id_skill_id_df21ffee_uniq RENAME TO marketplace_volunteerskill_user_id_skill_id_df21ffee_uniq;
ALTER INDEX dssgmkt_organizationmembershiprequest_organization_id_730ec8c7 RENAME TO marketplace_organizationmembershiprequest_organization_id_730ec8c7;
ALTER INDEX dssgmkt_organizationmembershiprequest_reviewer_id_408a9775 RENAME TO marketplace_organizationmembershiprequest_reviewer_id_408a9775;
ALTER INDEX dssgmkt_organizationmembershiprequest_user_id_2423d619 RENAME TO marketplace_organizationmembershiprequest_user_id_2423d619;
ALTER INDEX dssgmkt_organizationrole_organization_id_c1edcd42 RENAME TO marketplace_organizationrole_organization_id_c1edcd42;
ALTER INDEX dssgmkt_organizationrole_user_id_c8404340 RENAME TO marketplace_organizationrole_user_id_c8404340;
ALTER INDEX dssgmkt_pinnedtaskreview_task_review_id_eb9be817 RENAME TO marketplace_pinnedtaskreview_task_review_id_eb9be817;
ALTER INDEX dssgmkt_pinnedtaskreview_user_id_5d969f84 RENAME TO marketplace_pinnedtaskreview_user_id_5d969f84;
ALTER INDEX dssgmkt_project_organization_id_48f3ed4e RENAME TO marketplace_project_organization_id_48f3ed4e;
ALTER INDEX dssgmkt_projectcomment_author_id_e3dbf925 RENAME TO marketplace_projectcomment_author_id_e3dbf925;
ALTER INDEX dssgmkt_projectcomment_channel_id_09853c01 RENAME TO marketplace_projectcomment_channel_id_09853c01;
ALTER INDEX dssgmkt_projectdiscussionchannel_project_id_eba5e8d0 RENAME TO marketplace_projectdiscussionchannel_project_id_eba5e8d0;
ALTER INDEX dssgmkt_projectfollower_project_id_592e58f0 RENAME TO marketplace_projectfollower_project_id_592e58f0;
ALTER INDEX dssgmkt_projectfollower_user_id_07294ee2 RENAME TO marketplace_projectfollower_user_id_07294ee2;
ALTER INDEX dssgmkt_projectlog_author_id_21172dfc RENAME TO marketplace_projectlog_author_id_21172dfc;
ALTER INDEX dssgmkt_projectlog_project_id_ae94fc3b RENAME TO marketplace_projectlog_project_id_ae94fc3b;
ALTER INDEX dssgmkt_projectrole_project_id_91a37344 RENAME TO marketplace_projectrole_project_id_91a37344;
ALTER INDEX dssgmkt_projectrole_user_id_2b0f1741 RENAME TO marketplace_projectrole_user_id_2b0f1741;
ALTER INDEX dssgmkt_projectscope_author_id_d0769f3c RENAME TO marketplace_projectscope_author_id_d0769f3c;
ALTER INDEX dssgmkt_projectscope_project_id_ff953e1c RENAME TO marketplace_projectscope_project_id_ff953e1c;
ALTER INDEX dssgmkt_projecttask_project_id_dd846c67 RENAME TO marketplace_projecttask_project_id_dd846c67;
ALTER INDEX dssgmkt_projecttaskrequirement_skill_id_cc451ce2 RENAME TO marketplace_projecttaskrequirement_skill_id_cc451ce2;
ALTER INDEX dssgmkt_projecttaskrequirement_task_id_5b3be620 RENAME TO marketplace_projecttaskrequirement_task_id_5b3be620;
ALTER INDEX dssgmkt_projecttaskreview_reviewer_id_ac70bbe0 RENAME TO marketplace_projecttaskreview_reviewer_id_ac70bbe0;
ALTER INDEX dssgmkt_projecttaskreview_task_id_418c1c16 RENAME TO marketplace_projecttaskreview_task_id_418c1c16;
ALTER INDEX dssgmkt_projecttaskreview_volunteer_id_4248c587 RENAME TO marketplace_projecttaskreview_volunteer_id_4248c587;
ALTER INDEX dssgmkt_projecttaskrole_task_id_cc48e8a6 RENAME TO marketplace_projecttaskrole_task_id_cc48e8a6;
ALTER INDEX dssgmkt_projecttaskrole_user_id_91f46514 RENAME TO marketplace_projecttaskrole_user_id_91f46514;
ALTER INDEX dssgmkt_user_groups_group_id_2d76a8be RENAME TO marketplace_user_groups_group_id_2d76a8be;
ALTER INDEX dssgmkt_user_groups_user_id_9adc7e98 RENAME TO marketplace_user_groups_user_id_9adc7e98;
ALTER INDEX dssgmkt_user_user_permissions_permission_id_4f8d6260 RENAME TO marketplace_user_user_permissions_permission_id_4f8d6260;
ALTER INDEX dssgmkt_user_user_permissions_user_id_0be344c4 RENAME TO marketplace_user_user_permissions_user_id_0be344c4;
ALTER INDEX dssgmkt_user_username_d63c8841_like RENAME TO marketplace_user_username_d63c8841_like;
ALTER INDEX dssgmkt_userbadge_user_id_78f96c79 RENAME TO marketplace_userbadge_user_id_78f96c79;
ALTER INDEX dssgmkt_usernotification_user_id_a913f2a1 RENAME TO marketplace_usernotification_user_id_a913f2a1;
ALTER INDEX dssgmkt_volunteerapplication_reviewer_id_b46ff2e5 RENAME TO marketplace_volunteerapplication_reviewer_id_b46ff2e5;
ALTER INDEX dssgmkt_volunteerapplication_task_id_4c587176 RENAME TO marketplace_volunteerapplication_task_id_4c587176;
ALTER INDEX dssgmkt_volunteerapplication_volunteer_id_cb80f451 RENAME TO marketplace_volunteerapplication_volunteer_id_cb80f451;
ALTER INDEX dssgmkt_volunteerskill_skill_id_8e99a0a8 RENAME TO marketplace_volunteerskill_skill_id_8e99a0a8;
ALTER INDEX dssgmkt_volunteerskill_user_id_08f3dbbe RENAME TO marketplace_volunteerskill_user_id_08f3dbbe;
