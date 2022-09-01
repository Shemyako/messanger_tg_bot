from sqlalchemy.orm import Session
from sqlalchemy import create_engine, or_, and_, desc
from sqlalchemy.ext.automap import automap_base


class Connection: 
    def __init__(self, conf):
        Base = automap_base()
        engine = create_engine(conf)
        Base.prepare(engine, reflect=True)
        self.User = Base.classes.users
        self.Message = Base.classes.messages
        self.engine = engine
        
        # return [engine, User, Message]
    
    def get_ten_chats(self, login, offset = 0):
        session = Session(self.engine)
        answer = session.query(self.Message).filter(
            or_(
                self.Message.from_user == login,
                self.Message.to_user == login
            )).limit(9).offset(offset).all()
        # print(answer)
        session.close()
        return answer
    

    def message_sended(self, user_id, message_id):
        session = Session(self.engine)
        user = session.query(self.User).get(user_id)
        user.message_to_delete = message_id
        session.add(user)
        session.commit()
        session.close()


    def logout_user(self, tg_id = None, login = None):
        session = Session(self.engine)

        if (tg_id is not None):
            user = session.query(self.User).filter(self.User.tg_id == tg_id).first()
        else:
            user = session.query(self.User).filter(self.User.name == login).first()

        message_id = user.message_to_delete
        user.message_to_delete = None
        user_id = user.id

        tg_id = user.tg_id
        user.tg_id = None

        session.add(user)
        session.commit()
        session.close()
        return [tg_id, message_id, user_id]

    
    def login_user(self, user_id, tg_id):
        session = Session(self.engine)
        to_edit = session.query(self.User).get(user_id)
        to_edit.tg_id = tg_id
        session.add(to_edit)
        session.commit()
        session.close()


    def get_chat(self, my_id, user_id):
        session = Session(self.engine)
        ten_messages = session.query(self.Message).filter(
            or_(
                and_(
                    self.Message.from_user == my_id, 
                    self.Message.to_user == user_id
                ),
                and_(
                    self.Message.from_user == user_id, 
                    self.Message.to_user == my_id
                )
            )).order_by(
                desc(
                    self.Message.id
                )
            ).limit(10).all()

        # print(ten_messages)

        session.close()

        return ten_messages
    

    def send_message(self, tg_from, id_to, text):
        id_from = self.find_user(tg_from)

        session = Session(self.engine)
        session.add(self.Message(from_user=id_from[0], to_user=id_to, text = text, is_readed = False))
        session.commit()
        session.close()
        return id_from
        

    
    def find_user(self, tg_id):
        session = Session(self.engine)
        user = session.query(self.User).filter(self.User.tg_id == tg_id).first()
        session.close()
        return [user.id, user.message_to_delete]

