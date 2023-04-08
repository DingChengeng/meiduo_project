from django.shortcuts import render
from django.views import View
from django import http
from django.core.cache import cache
import logging

from .models import Area
from meiduo_mall.utils.response_code import RETCODE
# Create your views here.

logger = logging.getLogger('django')


class AreasView(View):

    def get(self, request):

        area_id = request.GET.get('area_id')
        if not area_id:
            province_list = cache.get('province_list')
            if not province_list:
                try:
                    province_model_list = Area.objects.filter(parent__isnull=True)
                    province_list = [{'id': province.id, 'name': province.name} for province in province_model_list]
                    cache.set('province_list', province_list, 3600)
                except Exception as e:
                    logger.error(e)
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '查询省份数据错误'})
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'province_list': province_list})
        else:
            sub_data = cache.get('sub_area_' + area_id)
            if not sub_data:
                try:
                    parent_model = Area.objects.get(id=area_id)
                    sub_model = Area.objects.filter(parent=area_id)
                    subs = [{'id': sub.id, 'name': sub.name} for sub in sub_model]
                    sub_data = {'id': parent_model.id, 'name': parent_model.name, 'subs': subs}
                    cache.set('sub_area_' + area_id, sub_data, 3600)
                except Exception as e:
                    logger.error(e)
                    return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '查询城市或区县数据错误'})
            return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'sub_data': sub_data})
