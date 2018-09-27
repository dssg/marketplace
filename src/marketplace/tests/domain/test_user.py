from django.test import TestCase
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser

from marketplace.models.common import ReviewStatus, SkillLevel
from marketplace.models.user import (
    SignupCodeType, SignupCode, User, UserType, Skill, VolunteerSkill, )
from marketplace.domain.user import UserService

from marketplace.tests.domain.common import (
    example_organization_user, example_staff_user, example_volunteer_user,
    example_organization, example_project,
    test_users_group_inclusion, test_permission_denied_operation,
)
import datetime

class UserTestCase(TestCase):
    dssg_staff_user = None
    volunteer_user = None

    code_repeated_1 = None
    code_repeated_2 = None

    def setUp(self):
        code_volunteer = SignupCode()
        code_volunteer.name = "AUTOMATICVOLUNTEER"
        code_volunteer.type = SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT
        code_volunteer.save()

        code_dssg = SignupCode()
        code_dssg.name = "MAKEDSSG"
        code_dssg.type = SignupCodeType.MAKE_DSSG_STAFF
        code_dssg.save()

        code_expiring = SignupCode()
        code_expiring.name = "EXPIREDCODE"
        code_expiring.type = SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT
        code_expiring.expiration_date = datetime.date(2000, 1, 1)
        code_expiring.save()

        code_restricted = SignupCode()
        code_restricted.name = "SINGLEUSECODE"
        code_restricted.type = SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT
        code_restricted.max_uses = 1
        code_restricted.save()

        self.code_repeated_1 = SignupCode()
        self.code_repeated_1.name = "MULTIPLECODES"
        self.code_repeated_1.type = SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT
        self.code_repeated_1.save()

        self.code_repeated_2 = SignupCode()
        self.code_repeated_2.name = "MULTIPLECODES"
        self.code_repeated_2.type = SignupCodeType.MAKE_DSSG_STAFF
        self.code_repeated_2.save()

        dssg_user = User()
        dssg_user.username = "DSSGUser"
        dssg_user.first_name = "DSSG"
        dssg_user.last_name = "Staff"
        dssg_user.special_code = "MAKEDSSG"
        UserService.create_user(None, dssg_user, 'organization', None, None)
        self.dssg_staff_user = dssg_user

    def test_organization_user(self):
        organization_user = User()
        organization_user.username = "OrgUser"
        organization_user.first_name = "Organization"
        organization_user.last_name = "User"
        UserService.create_user(None, organization_user, 'organization', None, None)
        self.assertEqual(UserService.get_user(organization_user, organization_user.id), organization_user)

        self.assertFalse(UserService.user_is_dssg_staff(organization_user, organization_user))
        self.assertTrue(UserService.user_is_organization_creator(organization_user))
        self.assertFalse(UserService.user_has_skills(organization_user))
        self.assertFalse(UserService.user_has_volunteer_profile(organization_user))
        self.assertFalse(UserService.user_has_approved_volunteer_profile(organization_user))

        organization_user.first_name = "Organization edited"
        UserService.save_user(organization_user, organization_user.id, organization_user)
        self.assertEqual(UserService.get_user(organization_user, organization_user.id), organization_user)

    def test_dssg_user(self):
        dssg_user = User()
        dssg_user.username = "DSSGUser"
        dssg_user.first_name = "DSSG"
        dssg_user.last_name = "Staff"
        dssg_user.special_code = "MAKEDSSG"
        UserService.create_user(None, dssg_user, 'organization', None, None)
        self.assertEqual(UserService.get_user(dssg_user, dssg_user.id), dssg_user)

        self.assertTrue(UserService.user_is_dssg_staff(dssg_user, dssg_user))
        self.assertFalse(UserService.user_is_organization_creator(dssg_user))
        self.assertFalse(UserService.user_has_skills(dssg_user))
        self.assertFalse(UserService.user_has_volunteer_profile(dssg_user))
        self.assertFalse(UserService.user_has_approved_volunteer_profile(dssg_user))

        UserService.create_volunteer_profile(dssg_user, volunteer_user.id)
        self.assertTrue(UserService.user_has_volunteer_profile(dssg_user))
        self.assertFalse(UserService.user_has_approved_volunteer_profile(dssg_user))

    def test_dssg_user(self):
        volunteer_user = User()
        volunteer_user.username = "VolUser"
        volunteer_user.first_name = "Volunteer"
        volunteer_user.last_name = "User"
        volunteer_user.email = "volunteer@email.com"
        UserService.create_user(None, volunteer_user, 'volunteer', None, None)

        self.assertFalse(UserService.user_is_dssg_staff(volunteer_user, volunteer_user))
        self.assertFalse(UserService.user_is_organization_creator(volunteer_user))
        self.assertFalse(UserService.user_has_skills(volunteer_user))
        self.assertTrue(UserService.user_has_volunteer_profile(volunteer_user))
        self.assertFalse(UserService.user_has_approved_volunteer_profile(volunteer_user))

        self.assertFalse(volunteer_user.volunteerprofile.is_edited)
        volunteer_user.volunteerprofile.cover_letter = "ABC"
        UserService.save_volunteer_profile(volunteer_user, volunteer_user.id, volunteer_user.volunteerprofile)
        self.assertTrue(volunteer_user.volunteerprofile.is_edited)
        self.assertFalse(UserService.user_has_approved_volunteer_profile(volunteer_user))

        self.assertEqual(set(UserService.get_pending_volunteer_profiles(self.dssg_staff_user)),
            set([volunteer_user.volunteerprofile]))


        UserService.accept_volunteer_profile(self.dssg_staff_user, volunteer_user.volunteerprofile.id)
        self.assertTrue(volunteer_user.volunteerprofile.is_edited)
        self.assertTrue(UserService.user_has_approved_volunteer_profile(volunteer_user))

        volunteer_user2 = User()
        volunteer_user2.username = "VolUser2"
        volunteer_user2.first_name = "Volunteer2"
        volunteer_user2.last_name = "User2"
        volunteer_user2.email = "volunteer2@email.com"
        UserService.create_user(None, volunteer_user2, 'volunteer', None, None)
        UserService.reject_volunteer_profile(self.dssg_staff_user, volunteer_user2.volunteerprofile.id)
        self.assertFalse(UserService.user_has_approved_volunteer_profile(volunteer_user2))

        volunteer_user3 = User()
        volunteer_user3.username = "VolUser3"
        volunteer_user3.first_name = "Volunteer3"
        volunteer_user3.last_name = "User3"
        volunteer_user3.email = "volunteer3@email.com"
        volunteer_user3.special_code = "AUTOMATICVOLUNTEER"
        UserService.create_user(None, volunteer_user3, 'volunteer', None, None)
        self.assertTrue(UserService.user_has_approved_volunteer_profile(volunteer_user3))

        self.assertEqual(set(UserService.get_all_approved_volunteer_profiles(AnonymousUser())),
            set([volunteer_user.volunteerprofile, volunteer_user3.volunteerprofile]))

    def test_skills(self):
        volunteer_user = User()
        volunteer_user.username = "VolUser3"
        volunteer_user.first_name = "Volunteer3"
        volunteer_user.last_name = "User3"
        volunteer_user.email = "volunteer3@email.com"
        volunteer_user.special_code = "AUTOMATICVOLUNTEER"
        UserService.create_user(None, volunteer_user, 'volunteer', None, None)

        skill1 = Skill()
        skill1.area = "Area 1"
        skill1.name = "Skill 1"
        skill1.save()
        skill2 = Skill()
        skill2.area = "Area 2"
        skill2.name = "Skill 2"
        skill2.save()
        self.assertEqual(UserService.get_volunteer_skills(volunteer_user, volunteer_user.id),
            {skill1.area: [{'system_skill': skill1, 'volunteer_skill': None}],
             skill2.area: [{'system_skill': skill2, 'volunteer_skill': None}]})
        for level1 in [-1, SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE, SkillLevel.EXPERT]:
            for level2 in [-1, SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE, SkillLevel.EXPERT]:
                with self.subTest(level1=level1, level2=level2):
                    post_object = {str(skill1.id): level1, str(skill2.id): level2}
                    UserService.set_volunteer_skills(volunteer_user, volunteer_user.id, post_object)
                    new_skills = UserService.get_volunteer_skills(volunteer_user, volunteer_user.id)
                    skill1_skill = VolunteerSkill.objects.filter(user=volunteer_user, skill=skill1).first()
                    skill2_skill = VolunteerSkill.objects.filter(user=volunteer_user, skill=skill2).first()
                    self.assertEqual(new_skills,
                        {skill1.area: [{'system_skill': skill1, 'volunteer_skill': skill1_skill}],
                         skill2.area: [{'system_skill': skill2, 'volunteer_skill': skill2_skill}]})

    def test_signup_codes(self):
        volunteer_user = User()
        volunteer_user.username = "VolUser3"
        volunteer_user.first_name = "Volunteer3"
        volunteer_user.last_name = "User3"
        volunteer_user.email = "volunteer3@email.com"
        volunteer_user.special_code = "EXPIREDCODE"

        self.assertFalse(UserService.has_valid_special_signup_code(volunteer_user, SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT))

        volunteer_user.special_code = "SINGLEUSECODE"
        self.assertTrue(UserService.has_valid_special_signup_code(volunteer_user, SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT))

        volunteer_user.special_code = "singleusecode"
        self.assertTrue(UserService.has_valid_special_signup_code(volunteer_user, SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT))

        volunteer_user.special_code = "SingleUseCode"
        self.assertTrue(UserService.has_valid_special_signup_code(volunteer_user, SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT))

        UserService.use_signup_code("SINGLEUSECODE", SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT)
        self.assertFalse(UserService.has_valid_special_signup_code(volunteer_user, SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT))

        self.assertEqual(set(UserService.get_signup_codes_by_text("MULTIPLECODES")),
            set([self.code_repeated_1, self.code_repeated_2]))

# TODO test these methods:
# UserService.get_user_todos(request_user, user)
# UserService.get_volunteer_leaderboards(request_user)
# UserService.get_featured_volunteer()
# UserService.verify_captcha(captcha_response)
