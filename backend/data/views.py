from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
from .models import Item, KlineData
from .serializers import ItemSerializer, KlineDataSerializer

class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class KlineDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = KlineData.objects.all().order_by('-timestamp')[:100]  # 最近100条
    serializer_class = KlineDataSerializer

@api_view(['GET'])
def overall_stats(request):
    # 总体数据：总物品数、平均价格等
    try:
        with connection.cursor() as cursor:
            # 从items表获取总物品数
            cursor.execute("SELECT COUNT(*) FROM items WHERE BUFF IS NOT NULL AND BUFF != ''")
            total_items = cursor.fetchone()[0]

            # 从kline_data获取平均收盘价
            cursor.execute("SELECT AVG(close_price) FROM kline_data")
            avg_price_row = cursor.fetchone()
            avg_price = avg_price_row[0] or 0

        return Response({
            'total_items': total_items,
            'average_price': round(float(avg_price), 2),
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
