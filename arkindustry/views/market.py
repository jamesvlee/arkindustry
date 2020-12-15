from flask import Blueprint, request, render_template, redirect, url_for
from arkindustry.database import UniverseType
from arkindustry.forms import ItemTypeForm
from mongoengine import *

import urllib3
import xmltodict
import datetime


http = urllib3.PoolManager()


mod = Blueprint('market', __name__, url_prefix='/market')


@mod.route('', methods=['GET', 'POST'])
def type_search():
    form = ItemTypeForm(request.form)
    error_msg = None
    if form.validate_on_submit():
        item = UniverseType.objects(name=form.item_name.data).first()
        if item:
            return redirect(url_for('market.market', type_id=item.type_id))
        else:
            error_msg = '请输入正确的物品名'
    return render_template('market/type_search.html', form=form, error_msg=error_msg)


@mod.route('/type/<int:type_id>', methods=['GET', 'POST'])
def market(type_id):
    form = ItemTypeForm(request.form)
    error_msg = None
    if request.method == 'POST':
        name = request.form.get('item_name')
        if name:
            item = UniverseType.objects(name=name).first()
            if item:
                return redirect(url_for('market.market', type_id=item.type_id))
            else:
                error_msg = '请输入正确的物品名'
        else:
            error_msg = '需要输入物品名'
        return render_template('market/type_search.html', form=form, error_msg=error_msg)
    item = UniverseType.objects(type_id=type_id).first()
    url = 'https://www.ceve-market.org/api/quicklook?typeid={}'.format(type_id)
    resp = http.request('GET', url)
    xml_data = resp.data.decode('utf-8')
    dict_data = xmltodict.parse(xml_data)
    sell_orders = []
    buy_orders = []
    sell_orders_data = dict_data['evec_api']['quicklook']['sell_orders']
    if len(sell_orders_data) > 0:
        if not isinstance(sell_orders_data['order'], list):
            o = sell_orders_data['order']
            order = {}
            region = UniverseType.objects(type_id=o['region']).first()
            order['region'] = region.name
            order['quantity'] = int(o['vol_remain'])
            order['price'] = float(o['price'])
            sec = float('%.1f' % float(o['security']))
            sec = 0.0 if sec == 0 else sec
            order['security'] = sec
            order['station'] = o['station_name']
            order['expires_in'] = datetime.datetime.strptime(o['expries'], '%Y-%m-%d %H:%M:%S')
            order['received_at'] = datetime.datetime.strptime(o['reported_time'], '%Y-%m-%d %H:%M:%S')
            sell_orders.append(order)
        else:
            for o in sell_orders_data['order']:
                order = {}
                region = UniverseType.objects(type_id=o['region']).first()
                order['region'] = region.name
                order['quantity'] = int(o['vol_remain'])
                order['price'] = float(o['price'])
                sec = float('%.1f' % float(o['security']))
                sec = 0.0 if sec == 0 else sec
                order['security'] = sec
                order['station'] = o['station_name']
                order['expires_in'] = datetime.datetime.strptime(o['expries'], '%Y-%m-%d %H:%M:%S')
                order['received_at'] = datetime.datetime.strptime(o['reported_time'], '%Y-%m-%d %H:%M:%S')
                sell_orders.append(order)
    buy_orders_data = dict_data['evec_api']['quicklook']['buy_orders']
    if len(buy_orders_data) > 0:
        if not isinstance(buy_orders_data['order'], list):
            o = buy_orders_data['order']
            order = {}
            region = UniverseType.objects(type_id=o['region']).first()
            order['region'] = region.name
            order['quantity'] = int(o['vol_remain'])
            order['price'] = float(o['price'])
            sec = float('%.1f' % float(o['security']))
            sec = 0.0 if sec == 0 else sec
            order['security'] = sec
            order['station'] = o['station_name']
            order['range'] = int(o['range'])
            order['min_volume'] = int(o['min_volume'])
            order['expires_in'] = datetime.datetime.strptime(o['expries'], '%Y-%m-%d %H:%M:%S')
            order['received_at'] = datetime.datetime.strptime(o['reported_time'], '%Y-%m-%d %H:%M:%S')
            buy_orders.append(order)
        else:
            for o in buy_orders_data['order']:
                order = {}
                region = UniverseType.objects(type_id=o['region']).first()
                order['region'] = region.name
                order['quantity'] = int(o['vol_remain'])
                order['price'] = float(o['price'])
                sec = float('%.1f' % float(o['security']))
                sec = 0.0 if sec == 0 else sec
                order['security'] = sec
                order['station'] = o['station_name']
                order['range'] = int(o['range'])
                order['min_volume'] = int(o['min_volume'])
                order['expires_in'] = datetime.datetime.strptime(o['expries'], '%Y-%m-%d %H:%M:%S')
                order['received_at'] = datetime.datetime.strptime(o['reported_time'], '%Y-%m-%d %H:%M:%S')
                buy_orders.append(order)
    market = {}
    sell_orders.sort(key=lambda o:o['price'])
    buy_orders.sort(key=lambda o:o['price'], reverse=True)
    market['sell_orders'] = sell_orders
    market['buy_orders'] = buy_orders
    return render_template('market/market_data.html', form=form, item=item, market=market)
