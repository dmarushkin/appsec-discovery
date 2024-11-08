from mongoengine import Document, StringField, IntField

class MyModel(Document):
    field1 = StringField()
    field2 = IntField()