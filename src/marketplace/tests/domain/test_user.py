import datetime

from django.test import TestCase
from django.contrib.auth.models import AnonymousUser

from marketplace.domain import marketplace
from marketplace.domain.user import UserService

from marketplace.models.common import SkillLevel
from marketplace.models.user import (
    SignupCodeType, SignupCode, User, Skill, VolunteerSkill, )


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
        dssg_user.email = "dssg@email.com"
        marketplace.user.add_user(dssg_user, 'organization')
        self.dssg_staff_user = dssg_user

    def test_organization_user(self):
        organization_user = User(
            username="OrgUser",
            email='orguser@example.com',
            first_name="Organization",
            last_name="User",
        )
        marketplace.user.add_user(organization_user, 'organization')
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
        volunteer_user = User(
            username="VolUser",
            first_name="Volunteer",
            last_name="User",
            email="volunteer@email.com",
        )
        marketplace.user.add_user(volunteer_user, 'volunteer')

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

        self.assertSequenceEqual(
            marketplace.user.query_pending_volunteer_profiles(self.dssg_staff_user),
            [volunteer_user.volunteerprofile],
        )

        UserService.accept_volunteer_profile(self.dssg_staff_user, volunteer_user.volunteerprofile.id)
        self.assertTrue(volunteer_user.volunteerprofile.is_edited)
        self.assertTrue(UserService.user_has_approved_volunteer_profile(volunteer_user))

        volunteer_user2 = User()
        volunteer_user2.username = "VolUser2"
        volunteer_user2.first_name = "Volunteer2"
        volunteer_user2.last_name = "User2"
        volunteer_user2.email = "volunteer2@email.com"
        marketplace.user.add_user(volunteer_user2, 'volunteer')
        UserService.reject_volunteer_profile(self.dssg_staff_user, volunteer_user2.volunteerprofile.id)
        self.assertFalse(UserService.user_has_approved_volunteer_profile(volunteer_user2))

        volunteer_user3 = User()
        volunteer_user3.username = "VolUser3"
        volunteer_user3.first_name = "Volunteer3"
        volunteer_user3.last_name = "User3"
        volunteer_user3.email = "volunteer3@email.com"
        volunteer_user3.special_code = "AUTOMATICVOLUNTEER"
        marketplace.user.add_user(volunteer_user3, 'volunteer')
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
        marketplace.user.add_user(volunteer_user, 'volunteer')

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
        self.assertFalse(
            marketplace.user.is_valid_special_signup_code(
                'EXPIREDCODE',
                SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT,
            )
        )

        for special_code in (
            'SINGLEUSECODE',
            'singleusecode',
            'SingleUseCode',
        ):
            self.assertTrue(
                marketplace.user.is_valid_special_signup_code(
                    special_code,
                    SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT,
                )
            )

        marketplace.user.use_signup_code('SINGLEUSECODE')
        self.assertFalse(
            marketplace.user.is_valid_special_signup_code(
                'SingleUseCode',
                SignupCodeType.VOLUNTEER_AUTOMATIC_ACCEPT,
            )
        )

        self.assertSequenceEqual(
            marketplace.user.query_signup_codes_by_text("MULTIPLECODES").order_by('pk'),
            (self.code_repeated_1, self.code_repeated_2),
        )

# TODO test these methods:
# UserService.get_user_todos(request_user, user)
# UserService.get_volunteer_leaderboards(request_user)
# UserService.get_featured_volunteer()
# marketplace.user.verify_captcha(captcha_response)
