--
-- Update references in meta tables
--
UPDATE django_content_type SET app_label='marketplace' WHERE app_label='dssgmkt';
UPDATE django_migrations SET app='marketplace' WHERE app='dssgmkt';
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
