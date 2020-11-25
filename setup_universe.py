from arkindustry.database import UniverseType

import pandas as pd


df = pd.read_excel('data/market-goods&systems.xls', sheet_name='星系列表')
df = df[df['星系ID'].notnull()]
for row in df.itertuples():
    type_id = getattr(row, '星系ID')
    name = getattr(row, '星系名稱')
    uni_type = UniverseType(type_id=type_id, name=name, is_system=True, published=True).save()
    print('system', type_id, ':', name, 'saved')

df = pd.read_excel('data/market-goods&systems.xls', sheet_name='星域列表')
df = df[df['星域ID'].notnull()]
for row in df.itertuples():
    type_id = getattr(row, '星域ID')
    name = getattr(row, '星域名字')
    uni_type = UniverseType(type_id=type_id, name=name, is_region=True, published=True).save()
    print('region', type_id, ':', name, 'saved')
