from django.shortcuts import render

# 将前端渲染到首页
def index(request):
    return render(request, 'index.html')