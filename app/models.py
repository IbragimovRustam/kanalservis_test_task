from app import db


class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    num = db.Column(db.Integer)
    order_num = db.Column(db.Integer)
    cost_usd = db.Column(db.Integer)
    cost_rub = db.Column(db.Integer)
    deliver_date = db.Column(db.Date)
    def __repr__(self):
        return 'Orders'