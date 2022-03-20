import re, json, logging
from django.shortcuts import render, redirect
from django.views import View
from django import http
from django.db import DatabaseError
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django_redis import get_redis_connection
from django.contrib.auth.mixins import LoginRequiredMixin

from users.models import User
from meiduo_mall.utils.response_code import RETCODE
# Create your views here.

logger = logging.getLogger('django')


class UsernameCountView(View):

    def get(self, request, username):

        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class MobileCountView(View):

    def get(self, request, mobile):

        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class RegisterView(View):

    def get(self, request):

        return render(request, 'register.html')

    def post(self, request):

        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')
        sms_code = request.POST.get('sms_code')

        if not all([username, password, password2, mobile, sms_code, allow]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[0-9a-zA-Z_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')

        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')

        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('您输入的手机号格式不正确')

        redis_conn = get_redis_connection('verify_code')
        sms_code_server = redis_conn.get("sms_%s" % mobile)
        if not sms_code_server:
            return render(request, 'register.html', {'sms_code_errmsg': '短信验证码已失效'})
        sms_code_server = sms_code_server.decode()
        if not sms_code_server == sms_code:
            return render(request, 'register.html', {'sms_code_errmsg': '短信验证码有误'})

        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', context={'register_errmsg': '注册失败'})

        login(request, user)

        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=3600)

        return response


class LoginView(View):

    def get(self, request):

        return render(request, 'login.html')

    def post(self, request):

        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        if not all([username, password]):

            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[0-9a-zA-Z_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')

        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')

        user = authenticate(username=username, password=password)
        if not user:
            return render(request, 'login.html', context={'account_errmsg': '用户名或密码错误'})

        login(request, user)

        if remembered != 'on':
            request.session.set_expiry(0)
        else:
            # None 默认是两周
            request.session.set_expiry(None)

        next = request.GET.get('next')
        if next:
            response = redirect(next)
        else:
            response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=3600)

        return response


class LogoutView(View):

    def get(self, request):

        logout(request)
        response = redirect(reverse('contents:index'))
        response.delete_cookie('username')
        return response


class UserInfoView(LoginRequiredMixin, View):

    def get(self, request):

        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active,
        }

        return render(request, 'user_center_info.html', context=context)


class EmailView(View):

    def put(self, request):

        json_str = request.body.decode()
        json_dic = json.loads(json_str)
        email = json_dic.get('email')

        if not email:
            return http.HttpResponseForbidden('缺少email参数')

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email有误')

        try:
            request.user.email = email
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加email失败'})

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加email成功'})
