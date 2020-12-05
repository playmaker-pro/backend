

class ViewModalLoadingMixin:

    def modal_activity(self, user, register_auto=None, verification_auto=None):
        modals = {
            'action_limit_exceeded': {
                'name': 'actionLimitExceedModal',
                'template': 'profiles/modals/_limit_exceeded_modal.html',
                'auto': False,
                'load': False,
                'async': False,
            },
            'register': {
                'name': 'registerModal',
                'template': 'profiles/modals/_register_modal.html',
                'auto': False,
                'load': False,
                'async': False
            },
            'verification': {
                'name': 'verificationModal',
                'template': 'profiles/modals/_verification_modal.html',
                'auto': False,
                'load': False,
                'async': 'get_verification_form',
            },
            'need_role': {
                'name': 'missingBasicAccountModal',
                'template': 'profiles/modals/_new_account_role_modal.html',
                'auto': False,
                'load': False,
                'async': False
            },
            'need_verification': {
                'name': 'verificationNeededModal',
                'template': 'profiles/modals/_need_verification.html',
                'auto': False,
                'load': False,
                'async': False
            },
            'inquiry': {
                'name': 'inquiryModal',
                'template': 'profiles/modals/_inquiry_modal.html',
                'auto': False,
                'load': False,
                'async': False
            }
        }
        # Loading account specific modals (mandatory)
        if not user.is_authenticated:
            modals['register']['load'] = True
            modals['register']['auto'] = register_auto or True

        elif user.is_missing_verification_data:
            modals['verification']['load'] = True
            # When user is pending role change

            if user.is_pending_role_change and verification_auto is None:
                modals['verification']['auto'] = False
            else:
                modals['verification']['auto'] = verification_auto if verification_auto is not None else True

        elif user.is_roleless:
            modals['need_role']['load'] = True
            modals['need_role']['auto'] = True

        elif user.is_waiting_for_verification:
            modals['need_verification']['load'] = True

        # Loading action specific modals
        # here is case when we can perfom action, so here are the action that we can perform
        else:
            modals['inquiry']['load'] = True

            if user.userinquiry.counter == user.userinquiry.limit:
                modals['action_limit_exceeded']['load'] = True

        return modals
