from sqlalchemy.orm import Session
from sqlalchemy import create_engine
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
