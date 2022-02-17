from django.shortcuts import render
from django.views import View
from verification.libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django import http
from . import constants
# Create your views here.


class ImageCodeView(View):

    def get(self, request, uuid):
        """
        :param uuid:通用唯一识别码，用于标识该图形码
        :return: image/jpg
        """
        text, image = captcha.generate_captcha()
        redis_conn = get_redis_connection('verify_code')
        redis_conn.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        return http.HttpResponse(image, content_type='image/jpg')
