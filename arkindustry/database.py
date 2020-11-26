from mongoengine import *
from datetime import datetime
from arkindustry import app, login_manager
from bson.objectid import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash

import random
import string


connect(app.config['DB_NAME'],
    username=app.config['DB_USER'],
    password=app.config['DB_PWD'],
    authentication_source=app.config['DB_AUTHSRC']
)


class RefiningOutput(EmbeddedDocument):
    item_type = ReferenceField('UniverseType')
    quantity = IntField(min_value=0)


class UniverseType(Document):
    type_id = IntField(unique=True)
    name = StringField()
    graphic_id = IntField()
    market_group_id = IntField()
    volume = DecimalField(min_value=0)
    published = BooleanField()
    is_region = BooleanField(default=False)
    is_system = BooleanField(default=False)
    is_ore = BooleanField(default=False)
    refining_input_q = IntField()
    refining_output = EmbeddedDocumentListField('RefiningOutput')


def find_item(name):
    item = UniverseType.object.get(name=name)
    return item if item else None


class UniverseGroup(Document):
    group_id = IntField(unique=True)
    types = ListField(ReferenceField('UniverseType'))
    name = StringField()
    published = BooleanField()


class UniverseCategory(Document):
    category_id = IntField(unique=True)
    groups = ListField(ReferenceField('UniverseGroup'))
    name = StringField()
    published = BooleanField()


class MiningQuantity(EmbeddedDocument):
    item_type = ReferenceField('UniverseType')
    quantity = IntField(min_value=0)
    volume = FloatField(min_value=0)


class Production(Document):
    member = ReferenceField('Member')
    quantity = EmbeddedDocumentListField('MiningQuantity')
    total_volume = FloatField(min_value=0)
    value = FloatField(min_value=0)
    

UPLOADING = 0
SETTLING = 1
CLOSED = 2

class Activity(Document):
    created = DateTimeField(default=datetime.now(), required=True)
    status = IntField(default=UPLOADING, required=True)

    meta = {'allow_inheritance': True}


class PriceNow(EmbeddedDocument):
    item_type = ReferenceField('UniverseType')
    price = FloatField(min_value=0)


MINERAL = 0
ORE = 1

class Mining(Activity):
    productions = ListField(ReferenceField('Production', reverse_delete_rule=PULL))
    prices_now = ListField(EmbeddedDocumentField('PriceNow'))
    settlement = IntField()
    refining_ratio = FloatField()
    ratio = FloatField()


class Fleet(Document):
    createdby = ReferenceField('Member', required=True)
    created = DateTimeField(default=datetime.now(), required=True)
    short = StringField(required=True)
    members = ListField(ReferenceField('Member'))

    meta = {
        'ordering': ['-created'],
        'allow_inheritance': True
    }


class MiningFleet(Fleet):
    systems = ListField(ReferenceField('UniverseType', unique=True, required=True))
    usage = ReferenceField('Mining')


def get_fleet_by_fleet_id(fleet_id):
    return Fleet.objects.get(id=ObjectId(fleet_id))


def create_mining_fleet(createdby, systems):
    mining = Mining(created=datetime.now(), productions=[], prices_now=[]).save()
    short = ''.join(random.sample(string.ascii_letters + string.digits, 7))
    mining_fleet = MiningFleet(created=datetime.now(), createdby=createdby, short=short, systems=systems, members=[], usage=mining)
    return mining_fleet.save()


class Channel(Document):
    name = StringField(unique=True, required=True)
    code = StringField(required=True)
    short = StringField(required=True)
    created = DateTimeField(default=datetime.now(), required=True)
    createdby = ReferenceField('Member', required=True)
    members = ListField(ReferenceField('Member'))

    meta = {
        'allow_inheritance': True
    }
    
    def verify_code(self, code):
        return self.code == code

    def refresh_code(self):
        code = '{0:04d}'.format(random.randint(0, 9999))
        Channel.objects(id=self.id).update_one(set__code=code)

    @staticmethod
    def get_channel(name):
        channel = Channel.objects(name=name).first()
        return channel if channel else None


class MiningChannel(Channel):
    fleets = ListField(ReferenceField('MiningFleet', reverse_delete_rule=PULL))
    captains = ListField(ReferenceField('Member'))


def create_mining_channel(name, member):
    code = '{0:04d}'.format(random.randint(0, 9999))
    short = ''.join(random.sample(string.ascii_letters + string.digits, 7))
    channel = MiningChannel(created=datetime.now(), name=name, code=code, short=short, createdby=member, members=[], fleets=[], captains=[member])
    return channel.save()


class ContractDetail(EmbeddedDocument):
    type_id = IntField()
    name = StringField()
    count = IntField()
    buy = FloatField(min_value=0)
    sell = FloatField(min_value=0)


class Contract(Document):
    short = StringField(required=True)
    total_buy = FloatField(min_value=0)
    total_sell = FloatField(min_value=0)
    details = EmbeddedDocumentListField('ContractDetail')


def contract_make_short():
    short = ''.join(random.sample(string.ascii_letters + string.digits, 7))
    return short


class Member(Document):
    email = EmailField(required=True, unique=True)
    nickname = StringField(required=True, unique=True)
    password = StringField(required=True)
    joined= DateTimeField(default=datetime.now(), required=True)
    mining_channels = ListField(ReferenceField('MiningChannel', reverse_delete_rule=PULL))
    last_mining_channel = ReferenceField('MiningChannel', reverse_delete_rule=NULLIFY)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def verify_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def nick_exist(nickname):
        if Member.objects(nickname=nickname).first():
            return True
        return False

    @staticmethod
    def get_member(email):
        member = Member.objects(email=email).first()
        return member if member else None


@login_manager.user_loader
def load_member(member_id):
    member = Member.objects.get(id=ObjectId(member_id))
    return member if member else None


def create_member(email, nickname, password):
    member = Member(email=email, nickname=nickname, password=generate_password_hash(password), joined=datetime.now(), mining_channels=[])
    return member.save()


def find_member(nickname):
    member = Member.objects.get(nickname=nickname)
    return member if member else None


def join_channel(member, channel):
    if channel not in member.mining_channels:
        MiningChannel.objects(id=channel.id).update_one(push__members=member)
        return Member.objects(id=member.id).update_one(push__mining_channels=channel)
    else:
        return True
