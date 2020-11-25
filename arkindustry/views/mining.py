from flask import Blueprint, request, render_template, redirect, url_for, abort, jsonify
from arkindustry.database import Member, Channel, MiningChannel, MiningFleet, Mining, Production, MiningQuantity, find_member, get_fleet_by_fleet_id, create_mining_channel, create_mining_fleet, UPLOADING, SETTLING, CLOSED, join_channel, UniverseType, Activity, MINERAL, ORE, PriceNow, Fleet
from arkindustry.forms import MiningChannelForm, MiningFleetForm, JoiningMiningChannelForm, MineralSettlementForm, OreSettlementForm 
from mongoengine import *
from bson.objectid import ObjectId
from flask_login import current_user, login_required


import urllib3
import json


http = urllib3.PoolManager()


mod = Blueprint('mining', __name__, url_prefix='/mining')


@mod.route('/channels', methods=['GET', 'POST'])
@login_required
def mining_channels():
    if request.method == 'POST':
        member = Member.get_member(current_user.email)
        channel_short = request.form.get('channel_short')
        channel = MiningChannel.objects.get(short=channel_short)
        Member.objects(id=member.id).update_one(pull__mining_channels=channel)
        MiningChannel.objects(short=channel_short).update_one(pull__captains=member)
        MiningChannel.objects(short=channel_short).update_one(pull__members=member)
    member = Member.get_member(current_user.email)
    channels = member.mining_channels
    return render_template('mining/mining_channels.html', member=member, channels=channels)


@mod.route('/create_channel', methods=['GET', 'POST'])
@login_required
def create_m_channel():
    form = MiningChannelForm(request.form)
    error_msg = None
    if request.method == 'POST' and form.validate():
        try:
            member = Member.get_member(current_user.email)
            name = form.name.data
            if MiningChannel.objects(name=name).first():
                raise
            channel = create_mining_channel(name, member)
            if not channel:
                return abort(400)
            join_channel(member, channel)
            return redirect(url_for('mining.mining_channels'))
        except:
            error_msg = '该频道名已存在'
    return render_template('mining/create_mining_channel.html', form=form, error_msg=error_msg)


@mod.route('/join_channel', methods=['GET', 'POST'])
@login_required
def join_m_channel():
    form = JoiningMiningChannelForm(request.form)
    error_msg = None
    if request.method == 'POST' and form.validate():
        name = form.name.data
        code = form.code.data
        channel = Channel.get_channel(name)
        if not channel:
            error_msg = '频道名或PIN码输入有误'
        else:
            if channel.verify_code(code):
                member = Member.get_member(current_user.email)
                join_channel(member, channel)
                return redirect(url_for('mining.mining_channels'))
            else:
                error_msg = '频道名或PIN码输入有误'
    return render_template('mining/join_mining_channel.html', form=form, error_msg=error_msg)


@mod.route('/channel/<string:channel_short>/mgmt', methods=['GET', 'POST'])
@login_required
def manage_channel(channel_short):
    if request.method == 'POST':
        channel_short = request.form.get('channel_short')
        func = request.form.get('func')
        if func == 'del_member':
            channel_member = Member.objects.get(id=request.form.get('member_id'))
            MiningChannel.objects(short=channel_short).update_one(pull__members=channel_member)
            MiningChannel.objects(short=channel_short).update_one(pull__captains=channel_member)
            channel = MiningChannel.objects.get(short=channel_short)
            Member.objects(id=request.form.get('member_id')).update_one(pull__mining_channels=channel)
        elif func == 'set_capt':
            channel_member = Member.objects.get(id=request.form.get('member_id'))
            MiningChannel.objects(short=channel_short).update_one(push__captains=channel_member)
        elif func == 'rm_capt':
            channel_member = Member.objects.get(id=request.form.get('member_id'))
            resp = MiningChannel.objects(short=channel_short).update_one(pull__captains=channel_member)
        elif func == 'del_channel': 
            MiningChannel.objects(short=channel_short).delete()
            return redirect(url_for('mining.mining_channels'))
    member = Member.get_member(current_user.email)
    channel = MiningChannel.objects.get(short=channel_short)
    is_creator = True if member == channel.createdby else False
    if not is_creator:
        abort(403)
    return render_template('mining/manage_channel.html', channel=channel)


@mod.route('/channel/<string:channel_short>/pin', methods=['GET'])
@login_required
def channel_code(channel_short):
    member = Member.get_member(current_user.email)
    channel = MiningChannel.objects.get(short=channel_short)
    is_creator = True if member == channel.createdby else False
    if not is_creator:
        abort(403)
    return render_template('mining/channel_code.html', channel=channel, opt='check', prompt_msg=None)


@mod.route('/channel/<string:channel_short>/refresh_pin', methods=['GET'])
@login_required
def refresh_code(channel_short):
    prompt_msg = None
    member = Member.get_member(current_user.email)
    channel = MiningChannel.objects.get(short=channel_short)
    is_creator = True if member == channel.createdby else False
    if not is_creator:
        abort(403)
    channel.refresh_code()
    prompt_msg = '已更新频道PIN码'
    channel = MiningChannel.objects.get(short=channel_short)
    return render_template('mining/channel_code.html', channel=channel, opt='refresh', channel_short=channel_short, prompt_msg=prompt_msg)


@mod.route('/channel/<string:channel_short>/delete_confirm', methods=['GET', 'POST'])
@login_required
def delete_channel(channel_short):
    member = Member.get_member(current_user.email)
    channel = MiningChannel.objects.get(short=channel_short)
    is_creator = True if member == channel.createdby else False
    if not is_creator:
        abort(403)
    if request.method == 'POST':
        for f in channel.fleets:
            for p in f.usage.productions:
                Production.objects(id=p.id).delete()
            Activity.objects(id=f.usage.id).delete()
            Fleet.objects(id=f.id).delete()
        MiningChannel.objects(short=channel.short).delete()
        member = Member.get_member(current_user.email)
        channels = member.mining_channels
        return redirect(url_for('mining.mining_channels', member=member, channels=channels))
    return render_template('mining/delete_channel.html', channel=channel, channel_short=channel_short)


@mod.route('/channel/<string:channel_short>/fleets', methods=['GET'])
@login_required
def mining_fleets(channel_short):
    member = Member.get_member(current_user.email)
    channel = MiningChannel.objects.get(short=channel_short)
    is_creator = True if member == channel.createdby else False
    is_captain = True if member in channel.captains else False
    fleets = MiningChannel.objects.get(short=channel_short).fleets
    return render_template('mining/mining_fleets.html', fleets=fleets[::-1], channel_short=channel_short, is_creator=is_creator, is_captain=is_captain)


@mod.route('/channel/<string:channel_short>/create_fleet', methods=['GET', 'POST'])
@login_required
def create_m_fleet(channel_short):
    member = Member.get_member(current_user.email)
    channel = MiningChannel.objects.get(short=channel_short)
    if member != channel.createdby and member not in channel.captains:
        abort(403)
    form = MiningFleetForm(request.form)
    error_msg = None
    if request.method == 'POST' and form.validate():
        locations = form.locations.data.split()
        loc_set = set()
        for loc in locations:
            loc_set.add(loc)
        systems = list()
        for loc in loc_set:
            system = UniverseType.objects(name=loc, is_system=True).first()
            if not system:
                error_msg = '请填写正确的星系名'
                break;
            else:
                systems.append(system)
        if not error_msg:
            member = Member.get_member(current_user.email)
            fleet = create_mining_fleet(member, systems)
            if not fleet:
                return abort(400)
            MiningChannel.objects(short=channel_short).update_one(push__fleets=fleet)
            return redirect(url_for('mining.mining_fleets', channel_short=channel_short))
    return render_template('mining/create_mining_fleet.html', channel_short=channel_short, form=form, error_msg=error_msg)


@mod.route('/channel/<string:channel_short>/fleet/<string:fleet_short>/delete_comfirm', methods=['GET', 'POST'])
@login_required
def delete_fleet(channel_short, fleet_short):
    member = Member.get_member(current_user.email)
    channel = MiningChannel.objects.get(short=channel_short)
    fleet = MiningFleet.objects.get(short=fleet_short)
    if member != channel.createdby and member != fleet.createdby:
        abort(403)
    if request.method == 'POST':
        for p in fleet.usage.productions:
            Production.objects(id = p.id).delete()
        Mining.objects(id=fleet.usage.id).delete()
        MiningFleet.objects(short=fleet_short).delete()
        return redirect(url_for('mining.mining_fleets', channel_short=channel_short))
    return render_template('mining/delete_fleet.html', channel_short=channel_short, fleet_short=fleet_short)

    
@mod.route('/channel/<string:channel_short>/fleet/<string:fleet_short>/product', methods=['GET', 'POST'])
def productions(channel_short, fleet_short):
    error_msg = None
    msform = MineralSettlementForm(request.form, prefix="msform")
    osform = OreSettlementForm(request.form, prefix="osform")
    if current_user.is_authenticated:
        member = Member.get_member(current_user.email)
    fleet = Fleet.objects.get(short=fleet_short)
    if request.method == 'POST' and request.form['func'] == 'off':
        Activity.objects(id=fleet.usage.id).update_one(set__status=CLOSED)
    if request.method == 'POST' and fleet.usage.status == UPLOADING and request.form['func'] == 'upload':
        try:
            colume = 8
            pur = request.form['pur'].split()[colume:]
            total_volume = 0
            prod = Production(member=member)
            for i in range(int(len(pur)/colume)):
                line = pur[colume*i:colume*i+8]
                TYPE_ID = 6
                SYSTEM_ID = 7
                QUANTITY = 2
                VOLUME = 3
                type_id = int(line[TYPE_ID])
                system_id = int(line[SYSTEM_ID])
                quan = int(line[QUANTITY])
                volume = float(line[VOLUME])
                system = UniverseType.objects.get(type_id=system_id)
                if system in fleet.systems:
                    item_type = UniverseType.objects.get(type_id=type_id)
                    quantity = MiningQuantity(item_type=item_type, quantity=quan, volume=volume)
                    prod.quantity.append(quantity)
                    total_volume += volume
            prod.total_volume = total_volume
            if not prod.quantity:
                raise ValueError()
            for p in fleet.usage.productions:
                if p.member == member:
                    Production.objects(id=p.id).delete()
            prod.save()
            Activity.objects(id=fleet.usage.id).update_one(push__productions=prod.id)
            if member not in fleet.members:
                fleet.members.append(member)
            if fleet.save():
                error_msg = '上传成功'
        except ValueError:
            error_msg = '似乎没有有效数据'
        except Exception:
            error_msg = '上传失败，请复制正确的采矿明细'
    if msform.validate_on_submit():
        item_prices = dict()
        ratio = float(msform.ratio.data)
        refining_ratio = float(msform.refining_ratio.data)
        Activity.objects(id=fleet.usage.id).update_one(set__prices_now=[])
        minerals = set()
        for p in fleet.usage.productions:
            for q in p.quantity:
                for o in q.item_type.refining_output:
                    minerals.add(o.item_type.type_id)
        for type_id in minerals:
            price = get_item_highest_buy_price(type_id)
            item_prices[type_id] = price
        for k, v in item_prices.items():
            price_now = PriceNow(item_type=UniverseType.objects.get(type_id=k), price=v)
            Activity.objects(id=fleet.usage.id).update_one(push__prices_now=price_now)
        for p in fleet.usage.productions:
            total_value = 0;
            for q in p.quantity:
                coef = q.quantity // q.item_type.refining_input_q * refining_ratio / 100
                mining = Activity.objects.get(id=fleet.usage.id)
                for output in q.item_type.refining_output:
                    for price in mining.prices_now:
                        if price.item_type.type_id == output.item_type.type_id:
                            value = float(price.price) * output.quantity * coef
                            total_value += value
            total_value = round(total_value * ratio / 100, 2)
            Production.objects(id=p.id).update_one(set__value=total_value)
        Activity.objects(id=fleet.usage.id).update(set__status=SETTLING, set__settlement=MINERAL, set__refining_ratio=refining_ratio, set__ratio=ratio) 
    elif osform.validate_on_submit():
        item_prices = dict()
        ratio = float(osform.ore_ratio.data)
        Activity.objects(id=fleet.usage.id).update_one(set__prices_now=[])
        ores = set()
        for p in fleet.usage.productions:
            for q in p.quantity:
                ores.add(q.item_type.type_id)
        for type_id in ores:
            price = get_item_highest_buy_price(type_id)
            item_prices[type_id] = price
        print(ores)
        for k, v in item_prices.items():
            price_now = PriceNow(item_type=UniverseType.objects.get(type_id=k), price=v)
            Activity.objects(id=fleet.usage.id).update_one(push__prices_now=price_now)
        for p in fleet.usage.productions:
            total_value = 0;
            for q in p.quantity:
                mining = Activity.objects.get(id=fleet.usage.id)
                for price in mining.prices_now:
                    if price.item_type.type_id == q.item_type.type_id:
                        value = float(price.price) * q.quantity
                        total_value += value
            total_value = round(total_value * ratio / 100, 2)
            Production.objects(id=p.id).update_one(set__value=total_value)
        Activity.objects(id=fleet.usage.id).update(set__status=SETTLING, set__settlement=ORE, set__ratio=ratio)

    is_channel_owner = False
    is_channel_member = False
    is_creator = False
    fleet = Fleet.objects.get(short=fleet_short)
    for i, p in enumerate(fleet.usage.prices_now):
        fleet.usage.prices_now[i].price = '{:,}'.format(p.price)
    for i, prod in enumerate(fleet.usage.productions):
        fleet.usage.productions[i].total_volume = '{:,}'.format(prod.total_volume)
        if fleet.usage.productions[i].value:
            fleet.usage.productions[i].value = '{:,}'.format(prod.value)
        for j, q in enumerate(prod.quantity):
            fleet.usage.productions[i].quantity[j].quantity = '{:,}'.format(q.quantity)
            fleet.usage.productions[i].quantity[j].volume = '{:,}'.format(q.volume)
    if current_user.is_authenticated:
        channel = MiningChannel.objects.get(short=channel_short)
        if member == channel.createdby:
            is_channel_owner = True
        if channel in member.mining_channels:
            is_channel_member = True
        if member == fleet.createdby:
            is_creator = True
    return render_template('mining/productions.html', fleet=fleet, channel_short=channel_short, is_channel_owner=is_channel_owner, is_channel_member=is_channel_member, is_creator=is_creator, error_msg=error_msg, msform=msform, osform=osform)
        

def get_item_highest_buy_price(type_id):
    url = 'https://www.ceve-market.org/api/market/region/10000002/type/{}.json'.format(type_id)
    r = http.request('GET', url)
    json_data = json.loads(r.data)
    buy = json_data['buy']['max']
    sell = json_data['sell']['min']
    price = buy if buy else sell
    return price
