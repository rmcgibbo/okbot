from sqlalchemy import Column, Integer, String, ForeignKey
from database import Base
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base


class Thread(Base):
    __tablename__ = 'threads'
    id = Column(Integer, primary_key=True)
    okc_id = Column(String, unique=True)
    
    def __repr__(self):
        return u'Thread %d, N=%d msgs>' % (self.id, len(self.messages))

class Message(Base):
    __tablename__ = 'messages'
    id = Column(Integer, primary_key=True)
    thread_id = Column(Integer, ForeignKey('threads.id'))
    thread = relationship("Thread", backref=backref('messages', order_by=id))

    okc_id = Column(String, unique=True)
    body = Column(String)
    sender = Column(String)
    fancydate = Column(String)

    def __repr__(self):
        use_unicode = False
        if use_unicode:
            '%s:  %s' % (self.sender, self.body)

        return ('%s:  %s' % (self.sender, self.body)).encode('utf-8')
        
    #def __str__(self):
    #    return self.__repr__().