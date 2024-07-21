from .models import Category

def categories_list(request):
    context = {}
    context["CATEGORIES_LIST"] = Category.objects.all()
    return context