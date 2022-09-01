import uuid
import hashlib
from sqlalchemy.orm import Session


class Auth_module:
    
    def __init__(self, connection):
        self.connection = connection

    def create_user(self, password, tg_id):
        salt = uuid.uuid4().hex
        password = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
        password = hashlib.sha256(salt.encode() + password.encode()).hexdigest()

        session = Session(self.connection.engine)
        session.add(self.connection.User(name=salt, password=password, tg_id=None, created_tg_id = tg_id))
        session.commit()
        session.close()

        return [salt, password]


    def check_hash(self, login, password):
        password = hashlib.sha256(login.encode() + password.encode()).hexdigest()
        password = hashlib.sha256(login.encode() + password.encode()).hexdigest()
        
        session = Session(self.connection.engine)
        answer = session.query(self.connection.User).filter(self.connection.User.password == password and self.connection.User.name == login).all()
        # print(answer)
        session.close()

        return(answer)


    def check_user(self, login, password):
        # print(User)
        checking = self.check_hash(login, password)

        if (len(checking) != 0):
            
            return checking[0].id
        else: 
            return False