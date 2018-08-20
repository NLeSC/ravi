from sqlalchemy import Column, Integer, Unicode, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Engineer(Base):
    """
    Table of engineers
    """
    __tablename__ = 'engineers'
    eid = Column(Unicode, primary_key = True)
    exact_id = Column(Unicode)
    fte = Column(Float)
    start = Column(Integer)
    end = Column(Integer)
    coordinator = Column(Unicode, ForeignKey('engineers.eid'))
    comments = Column(Unicode)
    active = Column(Boolean)
    
    def __iter__(self):
        for k,v in self.__dict__.items():
            if k[:1] != '_':
                yield k,v

class Project(Base):
    """
    Table of projects
    """
    __tablename__ = 'projects'
    pid = Column(Unicode, primary_key = True)
    exact_code = Column(Unicode)
    fte = Column(Float)
    start = Column(Integer)
    end = Column(Integer)
    coordinator = Column(Unicode, ForeignKey('engineers.eid'))
    comments = Column(Unicode)
    active = Column(Boolean)
    
    def __iter__(self):
        for k,v in self.__dict__.items():
            if k[:1] != '_':
                yield k,v

class Assignment(Base):
    """
    Table of assignments
    """
    __tablename__ = 'assignments'
    aid = Column(Integer, primary_key = True, autoincrement=True)
    fte = Column(Float)
    eid = Column(Unicode, ForeignKey('engineers.eid'))
    pid = Column(Unicode, ForeignKey('projects.pid'))
    start = Column(Integer)
    end = Column(Integer)

    def __iter__(self):
        for k,v in self.__dict__.items():
            if k[:1] != '_':
                yield k,v

class Usersetting(Base):
    """
    Table of usersettings
    """
    __tablename__ = 'usersetting'
    setting = Column(Unicode, primary_key = True)
    value = Column(Unicode)
    
    def __iter__(self):
        for k,v in self.__dict__.items():
            if k[:1] != '_':
                yield k,v

