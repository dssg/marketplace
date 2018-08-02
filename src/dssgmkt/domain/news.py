import logging

from dssgmkt.models.news import NewsPiece


LOG = logging.getLogger(__name__)


class NewsService():

    @staticmethod
    def get_latest_news(request_user, story_count=2):
        return NewsPiece.objects.order_by('-creation_date')[:2]
