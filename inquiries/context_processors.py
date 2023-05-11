from .services import InquireService


def get_user_info(request):
    if request.user.is_authenticated:
        unseen_req = InquireService.unseen_user_requests(request.user)
        return {
            "requests_app": {
                "number": unseen_req.count(),
                "unseen": unseen_req.values_list("id", flat=True),
            }
            # 'observers': unseen_user_obeservers(self.request.user),
        }
    return {}
