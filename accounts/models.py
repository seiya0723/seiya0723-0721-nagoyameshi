from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.core.validators import RegexValidator, MaxValueValidator

import uuid

class CustomUser(AbstractBaseUser, PermissionsMixin):

    username_validator = UnicodeUsernameValidator()

    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    username = models.CharField(
                                _('username'),
                                max_length=150,
                                unique=True,
                                help_text=('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
                                validators=[username_validator],
                                error_messages={
                                    'unique':_('A user with that username already exists.'),
                                },
                                )

    first_name  = models.CharField(_('first name'), max_length=150, blank=True, null=True)
    last_name   = models.CharField(_('last name'), max_length=150, blank=True, null=True)
    first_name_kana  = models.CharField(_('first name kana'), max_length=150, blank=True, null=True)
    last_name_kana   = models.CharField(_('last name kana'), max_length=150, blank=True, null=True)

    # メールアドレスは入力必須でユニークとする
    email       = models.EmailField(_('email address'), unique=True, null=True)

    email_verified = models.BooleanField(_('email verified at'), default=False)

    phone_number_regex = RegexValidator(regex=r'^[0-9]{10,11}$')
    phone_number = models.CharField(_('phone number'), max_length=11, blank=True, null=True, validators=[phone_number_regex])

    age = models.PositiveIntegerField(_('age'), blank=True, null=True, validators=[MaxValueValidator(110)])

    customer_id = models.CharField(_('customer id'), max_length=150, blank=True, null=True)


    is_staff    = models.BooleanField(
                    _('staff status'),
                    default=False,
                    help_text=_('Designates whether the user can log into this admin site.'),
                )

    is_active   = models.BooleanField(
                    _('active'),
                    default=True,
                    help_text=_(
                        'Designates whether this user should be treated as active. '
                        'Unselect this instead of deleting accounts.'
                    ),
                )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects     = UserManager()

    EMAIL_FIELD = 'email'

    # メールアドレスを使ってログインさせる。(管理ユーザーも)
    #USERNAME_FIELD = 'username'
    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = [ "username" ]

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        #abstract = True #←このabstractをコメントアウトする

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)
