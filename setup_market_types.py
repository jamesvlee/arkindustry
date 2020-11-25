from arkindustry.database import UniverseType

import pandas as pd


df = pd.read_excel('data/market-goods&systems.xls', sheet_name='物品列表')
df = df[df['typeID'].notnull()]
for row in df.itertuples():
    market_4th_type = getattr(row, '第四市场分类')
    if market_4th_type in ['冰矿', '卫星矿石', '标准矿石']:
        type_id = getattr(row, 'typeID')
        name = getattr(row, '物品名称')
        UniverseType(type_id=type_id, name=name, is_ore=True, published=True).save()
        print(market_4th_type, type_id, ':', name, 'saved')
    else:
        type_id = getattr(row, 'typeID')
        name = getattr(row, '物品名称')
        UniverseType(type_id=type_id, name=name, published=True).save()
        print(type_id, ':', name, 'saved')
