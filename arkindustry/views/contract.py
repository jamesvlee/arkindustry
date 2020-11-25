from flask import Blueprint, request, render_template, redirect, url_for, abort
from arkindustry.database import UniverseType, Contract, ContractDetail, contract_make_short
from mongoengine import *

import urllib3
import json


http = urllib3.PoolManager()


mod = Blueprint('contract', __name__, url_prefix='/contract')


@mod.route('', methods=['GET', 'POST'])
def value_calculate():
    if request.method == 'POST':
        order = make_contract(request.form['cu'])
        if order:
            short = contract_make_short()
            contract = Contract(short=short, total_buy=order['total_buy'], total_sell=order['total_sell'], details=[])
            contract.save()
            for d in order['details']:
                cd = ContractDetail(type_id=d['type_id'], name=d['name'], count=d['count'], buy=d['buy'], sell=d['sell'])
                Contract.objects(short=short).update_one(push__details=cd)
            return redirect(url_for('contract.look', short=short))
        else:
            error_msg = '似乎没有有效数据'
        return render_template('contract/value_calculate.html', error_msg=error_msg)
    return render_template('contract/value_calculate.html')


@mod.route('/<string:short>', methods=['GET', 'POST'])
def look(short):
    if request.method == 'POST':
        order = make_contract(request.form['cu'])
        if order:
            short = contract_make_short()
            contract = Contract(short=short, total_buy=order['total_buy'], total_sell=order['total_sell'], details=[])
            contract.save()
            for d in order['details']:
                cd = ContractDetail(type_id=d['type_id'], name=d['name'], count=d['count'], buy=d['buy'], sell=d['sell'])
                Contract.objects(short=short).update_one(push__details=cd)
            return redirect(url_for('contract.look', short=short))
        else:
            error_msg = '似乎没有有效数据'
            return render_template('contract/value_calculate.html', error_msg=error_msg)
    c = Contract.objects(short=short).first()
    if not c:
        abort(404)
    for i, d in enumerate(c.details):
        c.details[i].count = '{:,}'.format(d.count)
        c.details[i].buy = '{:,}'.format(d.buy)
        c.details[i].sell = '{:,}'.format(d.sell)
    c.total_buy = '{:,}'.format(c.total_buy)
    c.total_sell = '{:,}'.format(c.total_sell)
    return render_template('contract/value_calculate.html', order=c, redirect=True)


def make_contract(cu):
    data_list = cu.split('\n')
    total_buy = 0
    total_sell = 0
    order = dict()
    details = list()
    try:
        for data in data_list:
            s = data.replace(',', '').split()
            item = s[0]
            num = s[1]
            try:
                float(s[2])
                item = s[0] + ' ' + s[1]
                num = s[2]
            except:
                pass
            item = UniverseType.objects(name=item).first()
            count = int(num)
            buy, sell = get_item_price(item.type_id)
            buy = float(buy)
            sell = float(sell)
            buy_price = buy * count
            sell_price = sell * count
            price = dict()
            price['type_id'] = item.type_id
            price['name'] = item.name
            price['count'] = count
            price['buy'] = buy_price
            price['sell'] = sell_price
            details.append(price)
            total_buy += buy_price
            total_sell += sell_price
        if details:
            order['total_buy'] = total_buy
            order['total_sell'] = total_sell
            order['details'] = details
    except:
        order = None
    return order


def get_item_price(type_id):
    url = 'https://www.ceve-market.org/api/market/region/10000002/type/{}.json'.format(type_id)
    r = http.request('GET', url)
    json_data = json.loads(r.data)
    return json_data['buy']['max'], json_data['sell']['min']
