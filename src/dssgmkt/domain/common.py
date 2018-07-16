from dssgmkt.models.common import SocialCause
from dssgmkt.models.proj import ProjectStatus

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
                                            'new': ProjectStatus.NEW,
                                            'in_progress': ProjectStatus.IN_PROGRESS,
                                            'completed': ProjectStatus.COMPLETED,
                                        }
