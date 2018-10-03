from dssgmkt.models.common import SocialCause, TaskType
from dssgmkt.models.proj import ProjectStatus
from dssgmkt.models.user import BadgeType

def get_field_value(object, path):
    if isinstance(path, str):
        return getattr(object, path)
    elif not path:
        return object
    else:
        first, *rest = path
        return get_field_value(getattr(object, first), rest)

def validate_consistent_keys(object, error_message='Detected primary key inconsistency', *items):
    for (field_path, field_value) in items:
        if not get_field_value(object, field_path) == field_value:
            raise KeyError(error_message)
    return True


social_cause_view_model_translation = {
                                        'education': SocialCause.EDUCATION,
                                        'health': SocialCause.HEALTH,
                                        'environment': SocialCause.ENVIRONMENT,
                                        'socialservices': SocialCause.SOCIAL_SERVICES,
                                        'transportation': SocialCause.TRANSPORTATION,
                                        'energy': SocialCause.ENERGY,
                                        'internationaldev': SocialCause.INTERNATIONAL_DEVELOPMENT,
                                        'publicsafety': SocialCause.PUBLIC_SAFETY,
                                        'economicdev': SocialCause.ECONOMIC_DEVELOPMENT,
                                        'other': SocialCause.OTHER,
                                       }







project_status_view_model_translation = {
                                            'new': [ProjectStatus.NEW],
                                            'in_progress': [ProjectStatus.DESIGN,
                                                            ProjectStatus.WAITING_DESIGN_APPROVAL,
                                                            ProjectStatus.WAITING_STAFF,
                                                            ProjectStatus.IN_PROGRESS,
                                                            ProjectStatus.WAITING_REVIEW,
                                                            ],
                                            'completed': [ProjectStatus.COMPLETED],
                                        }

award_view_model_translation = {
                                             'review_score': BadgeType.REVIEW_SCORE,
                                             'number_of_projects': BadgeType.NUMBER_OF_PROJECTS,
                                             'fast_work': BadgeType.WORK_SPEED,
                                             'early_user': BadgeType.EARLY_USER,
                                         }


task_preferences_model_translation = {
     'scoping': TaskType.SCOPING_TASK,
     'management': TaskType.PROJECT_MANAGEMENT_TASK,
     'domainwork': TaskType.DOMAIN_WORK_TASK,
     'qa': TaskType.QA_TASK,
 }

def get_social_causes():
    return SocialCause.get_choices()
