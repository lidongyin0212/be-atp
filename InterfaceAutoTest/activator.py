from django.http import JsonResponse


def process(request, **kwargs):
    app = kwargs.pop('app', None)
    fun = kwargs.pop('function', None)
    index = kwargs.pop('id', None)
    scoure = kwargs.pop('scoure', None)
    sub_index = kwargs.pop('sub_index', None)
    # if app == 'api':
    #     app = 'InterfaceTestManage'

    try:
        if app == 'api':
            app = 'InterfaceTestManage'
            app = __import__("%s.views" % app)
            view = getattr(app, 'views')
        if app == 'user':
            app = 'InterfaceTestManage'
            app = __import__("%s.user_views" % app)
            view = getattr(app, 'user_views')
        if app == 'ui':
            app = 'UITestManage'
            app = __import__("%s.views" % app)
            view = getattr(app, 'views')
        # elif app == 'app':
        #     app = 'AppTestManage'
        #     app = __import__("%s.views" % app)
        #     view = getattr(app, 'views')
        fun = getattr(view, fun)

        # 执行view.py中的函数，并获取其返回值
        # result = fun(request, index, scoure) if index else fun(request, scoure)
        if index and scoure and sub_index:
            result = fun(request, index, sub_index, scoure)
        elif index and scoure:
            result = fun(request, index, scoure)
        elif index:
            result = fun(request, index)
        else:
            result = fun(request)

    except Exception as e:
        # raise
        if 'has no attribute' in str(e):
            return JsonResponse({"message": "该URL不存在", 'code': 500})
        else:  # 'invalid' in e:
            return JsonResponse({"message": "服务器错误", 'code': 500})
    return result


def process_report(request, **kwargs):
    filename = kwargs.pop('filename', None)
    fun = kwargs.pop('function', None)
    try:
        app = __import__("InterfaceTestManage.views")
        view = getattr(app, 'views')
        fun = getattr(view, fun)
        result = fun(request, filename)
    except (ImportError, AttributeError):
        raise
    return result
