from django.contrib.auth.backends import ModelBackend
import re
from django.conf import settings
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import BadData

from users.models import User
from . import constants


def generate_verify_email_url(user):

    s = Serializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    data = {'username': user.username, 'email': user.email}

    token = s.dumps(data).decode()
    url = settings.EMAIL_VERIFY_URL + '?token=' + token

    return url


def check_verify_email_token(token):

    s = Serializer(settings.SECRET_KEY, expires_in=constants.VERIFY_EMAIL_TOKEN_EXPIRES)
    try:
        data = s.loads(token)
    except BadData:
        return None
    else:
        username = data.get('username')
        email = data.get('email')
        try:
            user = User.objects.get(username=username, email=email)
        except user.DoesNotExist:
            return None
        else:
            return user




def get_user_by_account(account):
    """
    :param account: 用户名或者手机号码
    :return:
    """
    try:
        if re.match(r'^1[3-9]\d{9}$', account):

            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except User.DoesNotExist:
        return None
    else:
        return user


class UsernameMobileBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        重写用户认证方法
        :param username: 用户名或手机号码
        :param password: 密码明文
        :param kwargs: 额外参数
        :return: user
        """
        user = get_user_by_account(username)
        if user and user.check_password(password):
            return user
        else:
            return None
