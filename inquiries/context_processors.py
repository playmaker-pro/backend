from .services import unseen_user_requests


def get_user_info(request):
    unseen_req = unseen_user_requests(request.user)
    return {
        'requests_app': {
            'number': unseen_req.count(),
            'unseen': unseen_req.values_list('id', flat=True)
        }
            # 'observers': unseen_user_obeservers(self.request.user),
    }