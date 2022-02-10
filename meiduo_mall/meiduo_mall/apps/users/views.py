import re

from django.shortcuts import render, redirect
from django.views import View
from django import http
from django.db import DatabaseError
from django.urls import reverse
from users.models import User


# Create your views here.


class RegisterView(View):

    def get(self, request):

        return render(request, 'register.html')

    def post(self, request):

        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        mobile = request.POST.get('mobile')
        allow = request.POST.get('allow')

        if not all([username, password, password2, mobile, allow]):
            return http.HttpResponseForbidden('缺少必传参数')

        if not re.match(r'^[0-9a-zA-Z_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')

        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')

        if password != password2:
            return http.HttpResponseForbidden('两次输入的密码不一致')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('您输入的手机号格式不正确')

        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        try:
            User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', context={'register_errmsg': '注册失败'})

        return redirect(reverse('contents:index'))



