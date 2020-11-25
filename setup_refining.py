from arkindustry.database import UniverseType, RefiningOutput

import json


with open('data/mine.json', 'r', encoding='utf8') as j:
    json_data = json.load(j)
    for data in json_data:
        name = data['矿石']
        item = UniverseType.objects(name=name).first()
        if item:
            item.refining_input_q = 100
            for k, v in data.items():
                if k not in ['矿石', '体积'] and int(v):
                    t = UniverseType.objects(name=k).first()
                    output = RefiningOutput(item_type=t, quantity=int(v))
                    item.refining_output.append(output)
                    print('    /', t.name, 'v', 'saved')
            item.save()
            print(item.name, 'refining data saved')


with open('data/ice.json', 'r', encoding='utf8') as j:
    json_data = json.load(j)
    for data in json_data:
        name = data['矿石']
        item = UniverseType.objects(name=name).first()
        if item:
            item.refining_input_q = 1
            for k, v in data.items():
                if k not in ['矿石', '体积'] and int(v):
                    t = UniverseType.objects(name=k).first()
                    output = RefiningOutput(item_type=t, quantity=int(v))
                    item.refining_output.append(output)
                    print('    /', t.name, 'v', 'saved')
            item.save()
            print(item.name, 'refining data saved')


with open('data/moon.json', 'r', encoding='utf8') as j:
    json_data = json.load(j)
    for data in json_data:
        name = data['月矿']
        item = UniverseType.objects(name=name).first()
        if item:
            item.refining_input_q = 100
            for k, v in data.items():
                if k not in ['月矿', '体积', '提炼所需'] and int(v):
                    t = UniverseType.objects(name=k).first()
                    output = RefiningOutput(item_type=t, quantity=int(v))
                    item.refining_output.append(output)
                    print('    /', t.name, 'v', 'saved')
            item.save()
            print(item.name, 'refining data saved')
