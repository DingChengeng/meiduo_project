from django.contrib.auth.backends import ModelBackend
import re
from users.models import User


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
