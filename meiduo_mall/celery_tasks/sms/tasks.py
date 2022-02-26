from celery_tasks.sms.yuntongxun.ccp_sms import CCP
from celery_tasks.sms import constants as con
from celery_tasks.main import celery_app
# 定义任务


@celery_app.task(name='send_sms_code')
def send_sms_code(mobile, sms_code):
    """
    发送短信验证码异步任务
    :param mobile:手机号
    :param sms_code:验证码6位数字
    :return: 成功0 失败1
    """
    send_ret = CCP().send_template_sms(mobile, [sms_code, con.SMS_CODE_REDIS_EXPIRES // 60], con.SEND_SMS_TEMPLATE_ID)
    return send_ret
