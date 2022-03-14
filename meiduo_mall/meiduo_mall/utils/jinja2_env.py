from jinja2 import Environment
from django.urls import reverse
from django.contrib.staticfiles.storage import staticfiles_storage


def jinja2_environment(**options):

    env = Environment(**options)
    # 自定义语法 {{ static('静态文件相对路径') }}、{{ url(‘路由的命名空间’) }}
    env.globals.update({
        'static': staticfiles_storage.url,
        'url': reverse,
    })
    return env
