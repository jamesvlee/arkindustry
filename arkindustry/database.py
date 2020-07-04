from mongoengine import *
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash


connect('arkindustry')


class Member(Document):
    email = EmailField(required=True, unique=True)
    nickname = StringField(required=True, unique=True)
    password = StringField(required=True)
    joined= DateTimeField(default=datetime.now(), required=True)

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
    def get_member(email):
        member = Member.objects.get(email=email)
        return member if member else None


@login_manager.user_loader
def load_member(member_id):
    member = Member.object.get(id=ObjectId(member_id))
    return member if member else None


def create_member(email, nickname, password):
    member = Member(email=email, nickname=nickname, password=generate_password_hash(password))
    return member.save()


class Activity(Document):
    started = DateTimeField(default=datetime.now(), required=True)
    stopped = DateTimeField()

    meta = {'allow_inheritance': True}


class Mining(Activity):
    total_volume = DecimalField(min_value=0)
    production = EmbeddedDocumentListField('Production')


class Production(Document):
    member = ReferenceField('Member')
    volume = DecimalField(min_value=0)


class Fleet(Document):
    createdby = ReferenceField('Member', required=True)
    created = DateTimeField(default=datetime.now(), required=True)
    members = EmbeddedDocumentListField('Member')
    usage = ReferenceField('Activity')
