INQUIRY_TEMPLATE_MAPPING = {
    "ACCEPTED_INQUIRY": {
        "subject": "mailing/mails/inquiries/accepted_inquiry_subject.txt",
        "body": "mailing/mails/inquiries/accepted_inquiry.html",
    },
    "REJECTED_INQUIRY": {
        "subject": "mailing/mails/inquiries/rejected_inquiry_subject.txt",
        "body": "mailing/mails/inquiries/rejected_inquiry.html",
    },
    "OUTDATED_INQUIRY": {
        "subject": "mailing/mails/inquiries/outdated_inquiry_subject.txt",
        "body": "mailing/mails/inquiries/outdated_inquiry.html",
    },
    "NEW_INQUIRY": {
        "subject": "mailing/mails/inquiries/new_inquiry_subject.txt",
        "body": "mailing/mails/inquiries/new_inquiry.html",
    },
    "INQUIRY_LIMIT": {
        "subject": "mailing/mails/inquiries/inquiry_limit_subject.txt",
        "body": "mailing/mails/inquiries/inquiry_limit.html",
    },
    "OUTDATED_REMINDER": {
        "subject": "mailing/mails/inquiries/outdated_reminder_subject.txt",
        "body": "mailing/mails/inquiries/outdated_reminder.html",
    },
}

class EmailTemplates:
    INQUIRY_LIMIT = "INQUIRY_LIMIT"
    NEW_USER = "NEW_USER"
    PASSWORD_CHANGE = "PASSWORD_CHANGE"
    PREMIUM_EXPIRED = "PREMIUM_EXPIRED"
    REFERRAL_REWARD_REFERRER_1 = "REFERRAL_REWARD_REFERRER_1"
    REFERRAL_REWARD_REFERRER_3 = "REFERRAL_REWARD_REFERRER_3"
    REFERRAL_REWARD_REFERRER_5 = "REFERRAL_REWARD_REFERRER_5"
    REFERRAL_REWARD_REFERRER_15 = "REFERRAL_REWARD_REFERRER_15"
    REFERRAL_REWARD_REFERRED = "REFERRAL_REWARD_REFERRED"

class EmailTypes:
    INQUIRY_LIMIT = "inquiry_limit"
    NEW_USER = "new_user"
    PASSWORD_CHANGE = "password_change"
    PREMIUM_EXPIRED = "premium_expired"
    REFERRAL_REWARD = "referral_reward"
    SYSTEM = "system"



