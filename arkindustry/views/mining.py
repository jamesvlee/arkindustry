from flask import Blueprint, request, render_template, redirect, url_for, abort, jsonify
from arkindustry.database import Member, Channel, MiningChannel, MiningFleet, Mining, Production, MiningQuantity, find_member, get_fleet_by_fleet_id, create_mining_channel, create_mining_fleet, UPLOADING, SETTLING, CLOSED, join_channel, UniverseType, Activity, MINERAL, ORE, PriceNow, CustomPrice, Fleet
from arkindustry.forms import MiningChannelForm, MiningFleetForm, JoiningMiningChannelForm, MineralSettlementForm, OreSettlementForm, DeductForm, ActualVolumeForm
from mongoengine import *
from bson.objectid import ObjectId
from flask_login import current_user, login_required


import urllib3
import json
import datetime


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
    for i, f in enumerate(fleets):
        fleets[i].created = f.created + datetime.timedelta(hours=-8)
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
    if current_user.is_authenticated:
        member = Member.get_member(current_user.email)
    fleet = Fleet.objects.get(short=fleet_short)
    error_msg = None
    ac_error_msg = None
    if request.method == 'POST' and request.form['func'] == 'off':
        Activity.objects(id=fleet.usage.id).update_one(set__status=CLOSED)
    if request.method == 'POST' and request.form['func'] == 'cancel_deduct':
        Activity.objects(id=fleet.usage.id).update_one(set__transport_deduct=None, set__bonus_deduct=None, set__fleet_deduct=None)
    if request.method == 'POST' and request.form['func'] == 'cancel_actual':
        Activity.objects(id=fleet.usage.id).update_one(set__actual_volume=None, set__lossing_rate=None)
    if request.method == 'POST' and fleet.usage.status == UPLOADING and request.form['func'] == 'upload': 
        try:
            pur = request.form['pur']
            pur = pur.strip().replace(',', '').replace('m³', '').replace('星币', '')
            pur = pur.split('\r\n')
            if '时间点' in pur[0]:
                pur = pur[1:]
            total_volume = 0
            prod = Production(member=member)
            quans_vols = dict()
            for pu in pur:
                if pu:
                    p = pu.split()
                    time = p[0]
                    item_name = p[1]
                    quantity = int(p[2])
                    volume = float(p[3])
                    system_name = p[5]
                    system = UniverseType.objects.get(name=system_name)
                    if system in fleet.systems:
                        item_type = UniverseType.objects.get(name=item_name)
                        if item_type:
                            if item_name in quans_vols:
                                quan, vol = quans_vols[item_name]
                                quan += quantity
                                vol += volume
                                quans_vols[item_name] = (quan, vol)
                            else:
                                quans_vols[item_name] = (quantity, volume)
            for item_name, (quan, vol) in quans_vols.items():
                item_type = UniverseType.objects.get(name=item_name)
                quantity = MiningQuantity(item_type=item_type, quantity=quan, volume=round(vol, 2))
                prod.quantity.append(quantity)
                total_volume += vol
            total_volume = round(total_volume, 2)
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
        except ValueError as e:
            error_msg = '似乎没有有效数据'
        except Exception as e:
            error_msg = '上传失败，请复制正确的采矿明细'
        except Exception as e:
            pass

    fleet = Fleet.objects.get(short=fleet_short)
    msform = MineralSettlementForm(request.form, prefix='msform', refining_ratio=fleet.usage.refining_ratio if fleet.usage.refining_ratio else 79.8, ratio=fleet.usage.ratio if fleet.usage.ratio else 95.0)
    osform = OreSettlementForm(request.form, prefix='osform', ore_ratio=fleet.usage.ratio if fleet.usage.ratio else 95.0)
    deform = DeductForm(request.form, prefix='deform', transport=fleet.usage.transport_deduct if fleet.usage.transport_deduct else 0, bonus=fleet.usage.bonus_deduct if fleet.usage.bonus_deduct else 0, fleet=fleet.usage.fleet_deduct if fleet.usage.fleet_deduct else 0)
    acform = ActualVolumeForm(request.form, prefix='acform', actual_v=fleet.usage.actual_volume if fleet.usage.actual_volume else None)
    if request.method == 'POST' and request.form['func'] == 'set_deduct' and deform.validate_on_submit():
        trans_de = round(float(deform.transport.data), 2)
        bonus_de = round(float(deform.bonus.data), 2)
        fleet_de = round(float(deform.fleet.data), 2)
        if trans_de == 0:
            Activity.objects(id=fleet.usage.id).update_one(set__transport_deduct=None)
        else:
            Activity.objects(id=fleet.usage.id).update_one(set__transport_deduct=trans_de)
        if bonus_de == 0:
            Activity.objects(id=fleet.usage.id).update_one(set__bonus_deduct=None)
        else:
            Activity.objects(id=fleet.usage.id).update_one(set__bonus_deduct=bonus_de)
        if fleet_de == 0:
            Activity.objects(id=fleet.usage.id).update_one(set__fleet_deduct=None)
        else:
            Activity.objects(id=fleet.usage.id).update_one(set__fleet_deduct=fleet_de)
    elif request.method == 'POST' and request.form['func'] == 'set_actual' and acform.validate_on_submit():
        actual_v = round(float(acform.actual_v.data), 2)
        mining = Activity.objects.get(id=fleet.usage.id)
        if actual_v >= mining.upload_volume:
            ac_error_msg = '实际收矿不少于上传总量，设置无效'
        else:
            mining = Activity.objects.get(id=fleet.usage.id)
            lossing_rate = round((mining.upload_volume - actual_v) / mining.upload_volume * 100, 2)
            Activity.objects(id=fleet.usage.id).update_one(set__actual_volume=actual_v, set__lossing_rate=lossing_rate)
    elif request.method == 'POST' and request.form['func'] == 'refining_and_settle' and msform.validate_on_submit():
        item_prices = dict()
        ratio = round(float(msform.ratio.data), 2)
        refining_ratio = round(float(msform.refining_ratio.data), 2)
        Activity.objects(id=fleet.usage.id).update(set__prices_now=[], set__custom_prices=[])
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
        Activity.objects(id=fleet.usage.id).update(set__status=SETTLING, set__settlement=MINERAL, set__refining_ratio=refining_ratio, set__ratio=ratio) 
    elif request.method == 'POST' and request.form['func'] == 'ore_settle' and osform.validate_on_submit():
        item_prices = dict()
        ratio = round(float(osform.ore_ratio.data), 2)
        Activity.objects(id=fleet.usage.id).update(set__prices_now=[], set__custom_prices=[])
        ores = set()
        for p in fleet.usage.productions:
            for q in p.quantity:
                ores.add(q.item_type.type_id)
        for type_id in ores:
            price = get_item_highest_buy_price(type_id)
            item_prices[type_id] = price
        for k, v in item_prices.items():
            price_now = PriceNow(item_type=UniverseType.objects.get(type_id=k), price=v)
            Activity.objects(id=fleet.usage.id).update_one(push__prices_now=price_now)
        Activity.objects(id=fleet.usage.id).update(set__status=SETTLING, set__settlement=ORE, set__ratio=ratio)
    fleet = Fleet.objects.get(short=fleet_short)
    if fleet.usage.settlement == MINERAL:
        fleet_upload_volume = 0
        fleet_total_value = 0
        for p in fleet.usage.productions:
            total_value = 0;
            for q in p.quantity:
                coef = q.quantity // q.item_type.refining_input_q * fleet.usage.refining_ratio / 100
                mining = Activity.objects.get(id=fleet.usage.id)
                for output in q.item_type.refining_output:
                    prices = mining.prices_now
                    if mining.custom_prices:
                        prices = mining.custom_prices
                    for price in prices:
                        if price.item_type.type_id == output.item_type.type_id:
                            value = float(price.price) * output.quantity * coef
                            total_value += value
            fleet_upload_volume += p.total_volume
            total_value = round(total_value * fleet.usage.ratio / 100, 2)
            fleet_total_value += total_value
            Production.objects(id=p.id).update_one(set__value=total_value)
        fleet_total_value = round(fleet_total_value, 2)
        fleet_upload_volume = round(fleet_upload_volume, 2)
        Activity.objects(id=fleet.usage.id).update(set__upload_volume=fleet_upload_volume, set__total_value=fleet_total_value)
    elif fleet.usage.settlement == ORE:
        fleet_upload_volume = 0
        fleet_total_value = 0
        for p in fleet.usage.productions:
            total_value = 0;
            for q in p.quantity:
                mining = Activity.objects.get(id=fleet.usage.id)
                prices = mining.prices_now
                if mining.custom_prices:
                    prices = mining.custom_prices
                for price in prices:
                    if price.item_type.type_id == q.item_type.type_id:
                        value = float(price.price) * q.quantity
                        total_value += value
            fleet_upload_volume += p.total_volume
            total_value = round(total_value * fleet.usage.ratio / 100, 2)
            fleet_total_value += total_value
            Production.objects(id=p.id).update_one(set__value=total_value)
        fleet_total_value = round(fleet_total_value, 2)
        fleet_upload_volume = round(fleet_upload_volume, 2)
        Activity.objects(id=fleet.usage.id).update(set__upload_volume=fleet_upload_volume, set__total_value=fleet_total_value)

    is_channel_owner = False
    is_channel_member = False
    is_creator = False
    fleet = Fleet.objects.get(short=fleet_short)
    custom_count = 0
    for p in fleet.usage.prices_now:
        for cp in fleet.usage.custom_prices:
            if p.item_type.type_id == cp.item_type.type_id and p.price != cp.price:
                custom_count += 1
    if custom_count == len(fleet.usage.prices_now):
        custom_count = -1
    fleet.created = fleet.created + datetime.timedelta(hours=-8)
    if fleet.usage.upload_volume:
        fleet.usage.upload_volume = '{:,}'.format(fleet.usage.upload_volume)
    if fleet.usage.actual_volume:
        fleet.usage.actual_volume = '{:,}'.format(fleet.usage.actual_volume)
    for i, p in enumerate(fleet.usage.prices_now):
        fleet.usage.prices_now[i].price = '{:,}'.format(p.price)
    for i, p in enumerate(fleet.usage.custom_prices):
        fleet.usage.custom_prices[i].price = '{:,}'.format(p.price)
    reduced_fleet_total_value = 0
    for i, prod in enumerate(fleet.usage.productions):
        fleet.usage.productions[i].total_volume = '{:,}'.format(prod.total_volume)
        if prod.value:
            if fleet.usage.lossing_rate:
                prod.value = round(prod.value * (100 - fleet.usage.lossing_rate) / 100, 2)
                reduced_fleet_total_value += prod.value
            deduct_rate = 0
            if fleet.usage.transport_deduct:
                deduct_rate += fleet.usage.transport_deduct
            if fleet.usage.bonus_deduct:
                deduct_rate += fleet.usage.bonus_deduct
            if fleet.usage.fleet_deduct:
                deduct_rate += fleet.usage.fleet_deduct
            if deduct_rate:
                prod.value = prod.value * (100 - deduct_rate) / 100
            prod.value = round(prod.value, 2)
            fleet.usage.productions[i].value = '{:,}'.format(prod.value)
        for j, q in enumerate(prod.quantity):
            fleet.usage.productions[i].quantity[j].quantity = '{:,}'.format(q.quantity)
            fleet.usage.productions[i].quantity[j].volume = '{:,}'.format(q.volume)
    trans_v = 0
    bonus_v = 0
    fleet_v = 0
    if reduced_fleet_total_value:
        fleet.usage.total_value = reduced_fleet_total_value
    if fleet.usage.total_value:
        if fleet.usage.transport_deduct:
            trans_v = '{:,}'.format(round(fleet.usage.total_value * fleet.usage.transport_deduct / 100, 2))
        if fleet.usage.bonus_deduct:
            bonus_v = '{:,}'.format(round(fleet.usage.total_value * fleet.usage.bonus_deduct / 100, 2))
        if fleet.usage.fleet_deduct:
            fleet_v = '{:,}'.format(round(fleet.usage.total_value * fleet.usage.fleet_deduct / 100, 2))
        fleet.usage.total_value = round(fleet.usage.total_value, 2)
        fleet.usage.total_value = '{:,}'.format(fleet.usage.total_value)
    if current_user.is_authenticated:
        channel = MiningChannel.objects.get(short=channel_short)
        if member == channel.createdby:
            is_channel_owner = True
        if channel in member.mining_channels:
            is_channel_member = True
        if member == fleet.createdby:
            is_creator = True
    return render_template('mining/productions.html', fleet=fleet, trans_v=trans_v, bonus_v=bonus_v, fleet_v=fleet_v, custom_count=custom_count, channel_short=channel_short, is_channel_owner=is_channel_owner, is_channel_member=is_channel_member, is_creator=is_creator, error_msg=error_msg, msform=msform, osform=osform, deform=deform, acform=acform, ac_error_msg=ac_error_msg)


@mod.route('/channel/<string:channel_short>/fleet/<string:fleet_short>/custom_price', methods=['GET', 'POST'])
@login_required
def custom_price(channel_short, fleet_short):
    member = Member.get_member(current_user.email)
    channel = MiningChannel.objects.get(short=channel_short)
    fleet = MiningFleet.objects.get(short=fleet_short)
    if member != channel.createdby and member != fleet.createdby:
        abort(403)
    error_msg = None
    if request.method == 'POST' and request.form['func'] == 'set_prices':
        for p in fleet.usage.prices_now:
            new_price = request.form[str(p.item_type.type_id)]
            try:
                float(new_price)
            except:
                error_msg = '请填写正确的价格'
                break
            if new_price == 0:
                error_msg = '价格必须大于0'
                break
        if not error_msg:
            Activity.objects(id=fleet.usage.id).update_one(set__custom_prices=[])
            for p in fleet.usage.prices_now:
                custom_price = CustomPrice(item_type=p.item_type, price=round(float(request.form[str(p.item_type.type_id)]), 2))
                Activity.objects(id=fleet.usage.id).update_one(push__custom_prices=custom_price)
            return redirect(url_for('mining.productions', channel_short=channel_short, fleet_short=fleet_short))
    if request.method == 'POST' and request.form['func'] == 'reset_prices':
        Activity.objects(id=fleet.usage.id).update_one(set__custom_prices=[])
    fleet = MiningFleet.objects.get(short=fleet_short)
    return render_template('mining/custom_price.html', fleet=fleet, channel_short=channel_short, error_msg=error_msg)
        

def get_item_highest_buy_price(type_id):
    url = 'https://www.ceve-market.org/api/market/region/10000002/type/{}.json'.format(type_id)
    r = http.request('GET', url)
    json_data = json.loads(r.data)
    buy = json_data['buy']['max']
    return round(buy, 2)
