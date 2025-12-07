import requests

# 测试 news API
r = requests.get('http://localhost:8000/api/news', params={'page': 1, 'size': 20, 'summary_id': 1})
data = r.json()

highlighted = [item for item in data['items'] if item.get('highlighted')]

print(f'总新闻数: {len(data["items"])}')
print(f'高亮新闻数: {len(highlighted)}')
print('高亮新闻ID:', [item['id'] for item in highlighted])
print('\n前3条新闻的highlighted状态:')
for item in data['items'][:3]:
    print(f"  ID {item['id']}: highlighted={item.get('highlighted', False)}")
