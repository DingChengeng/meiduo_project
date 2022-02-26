from django.views import View
from django_redis import get_redis_connection
from django import http
import random
import logging

from . import constants
from verification.libs.captcha.captcha import captcha
from utils.response_code import RETCODE
from celery_tasks.sms.tasks import send_sms_code
# from verification.libs.yuntongxun.ccp_sms import CCP
# # Create your views here.

logger = logging.getLogger('django')


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


class SMSCodeView(View):

    def get(self, request, mobile):

        # 接收参数
        image_code_client = request.GET.get('image_code')
        uuid = request.GET.get('uuid')

        # 校验参数
        if not all([image_code_client, uuid]):
            return http.JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必传参数'})

        # 校验图形验证码
        redis_conn = get_redis_connection('verify_code')

        sms_send_flag = redis_conn.get("flag_%s" % mobile)
        if sms_send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过于频繁'})

        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码已失效', })

        image_code_server = image_code_server.decode()

        if image_code_client.lower() != image_code_server.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '输入图形验证码有误'})
        # 删除图形验证码
        redis_conn.delete('img_%s' % uuid)

        # 生成随机验证码
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)

        # 存储验证码
        pl = redis_conn.pipeline()
        pl.setex("sms_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
        pl.setex("flag_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()

        # 发送验证码
        # ccp = CCP()
        # ccp.send_template_sms(mobile, [sms_code, constants.SMS_CODE_REDIS_EXPIRES//60], constants.SEND_SMS_TEMPLATE_ID)
        send_sms_code.delay(mobile, sms_code)

        # 响应结果
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信成功'})
