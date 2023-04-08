from django.shortcuts import render
from django.views import View
from contents.models import ContentCategory
from contents.utils import get_categories


# Create your views here.


class IndexView(View):

    def get(self, request):

        categories = get_categories()
        contents = {}
        content_categories = ContentCategory.objects.all()
        for cat in content_categories:
            contents[cat.key] = cat.content_set.filter(status=True).order_by('sequence')
        # 渲染模板的上下文
        context = {
            'categories': categories,
            'contents': contents,
        }

        return render(request, 'index.html', context)


