from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from django import http
from django.contrib.auth import login
from django.urls import reverse
from django_redis import get_redis_connection
import logging
import re

from meiduo_mall.utils.response_code import RETCODE
from QQLoginTool.QQtool import OAuthQQ
from oauth.models import OAuthQQUser
from users.models import User
from oauth.utils import generate_access_token, get_access_token
# Create your views here.

logger = logging.getLogger('django')


class QQAuthURLView(View):

    def get(self, request):

        state = request.GET.get('next')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI,
                        state=state)

        login_url = oauth.get_qq_url()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'login_url': login_url})


class QQAuthUserView(View):

    def get(self, request):

        code = request.GET.get('code')

        if not code:
            return http.HttpResponseForbidden('获取code失败')

        oauth = OAuthQQ(client_id=settings.QQ_CLIENT_ID,
                        client_secret=settings.QQ_CLIENT_SECRET,
                        redirect_uri=settings.QQ_REDIRECT_URI)

        try:
            access_token = oauth.get_access_token(code)
            openid = oauth.get_open_id(access_token)
        except Exception as e:
            logger.error(e)
            return http.HttpResponseServerError('oauth2.0认证失败')

        try:
            oauth_user = OAuthQQUser.objects.get(openid=openid)
        except OAuthQQUser.DoesNotExist:
            # 无绑定用户，需先绑定用户或创建新用户
            access_token_openid = generate_access_token(openid)
            context = {'access_token_openid': access_token_openid}
            return render(request, 'oauth_callback.html', context=context)
        else:
            login(request, oauth_user.user)
            response = redirect(reverse('contents:index'))
            response.set_cookie('username', oauth_user.user.username, max_age=3600)
            return response

    def post(self, request):

        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        sms_code = request.POST.get('sms_code')
        access_token_openid = request.POST.get('access_token_openid')

        if not all([mobile, password, sms_code, access_token_openid]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('手机号格式不正确')

        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')

        redis_con = get_redis_connection('verify_code')
        sms_code_server = redis_con.get("sms_%s" % mobile)
        if not sms_code_server:
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '验证码已失效'})
        if sms_code != sms_code_server.decode():
            return render(request, 'oauth_callback.html', {'sms_code_errmsg': '验证码不正确'})

        openid = get_access_token(access_token_openid)
        if not openid:
            return render(request, 'oauth_callback.html', {'openid_errmsg': 'openid已经失效'})

        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            user = User.objects.create_user(username=mobile, password=password, mobile=mobile)
        else:
            if not user.check_password(password):
                return render(request, 'oauth_callback.html', {'account_errmsg': '用户名或密码错误'})

        try:
            oauth_qq_user = OAuthQQUser.objects.create(user=user, openid=openid)
        except Exception as e:
            logger.error(e)
            return render(request, 'oauth_callback.html', {'qq_login_errmsg': 'QQ登录失败'})

        login(request, user)
        next = request.GET.get('state')

        response = redirect(next)
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        return response
