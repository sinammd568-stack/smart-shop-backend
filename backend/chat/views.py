from django.http import JsonResponse

from . import catalog


def health(request):
    return JsonResponse({"status": "ok"})


def products(request):
    category = request.GET.get("category")
    items = [
        {k: v for k, v in p.items() if k != "keyword"}
        for p in catalog.PRODUCTS
        if not category or p["category"] == category
    ]
    return JsonResponse(
        {"count": len(items), "results": items},
        json_dumps_params={"ensure_ascii": False},
    )
