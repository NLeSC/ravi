from sqlalchemy import Column, Integer, Unicode, Float, Boolean, ForeignKey, Date
# from sqlalchemy import Boolean, TypeDecorator
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Engineer(Base):
    """
    Table of engineers
    """
    __tablename__ = 'person'
    person_id = Column(Integer, primary_key = True)
    fname = Column(Unicode)
    sname = Column(Unicode)
    line_manager = Column(Integer)
    status = Column(Unicode)
    exact_id = Column(Unicode)
    contract_start = Column(Date)
    contract_end = Column(Date)
    fte = Column(Float)
    isCoordinator = Column(Unicode)
    isLine_manager = Column(Unicode)
    timestamp = Column(Date)
    comments = Column(Unicode)
    tag = Column(Unicode)
    
    def __iter__(self):
        for k,v in self.__dict__.items():
            if k[:1] != '_':
                yield k,v

class Project(Base):
    """
    Table of projects
    """
    __tablename__ = 'project'
    project_id = Column(Integer, primary_key = True)
    fname = Column(Unicode)
    sname = Column(Unicode)
    coordinator = Column(Integer)
    status = Column(Unicode)
    exact_id = Column(Unicode)
    project_start = Column(Date)
    project_end = Column(Date)
    budget = Column(Integer)
    spend = Column(Integer)
    timestamp = Column(Date)
    tag = Column(Unicode)
    comments = Column(Unicode)
    
    def __iter__(self):
        for k,v in self.__dict__.items():
            if k[:1] != '_':
                yield k,v

class Assignment(Base):
    """
    Table of assignments
    """
    __tablename__ = 'assignment'
    assignment_id = Column(Integer, primary_key = True, autoincrement=True)
    assignment_start = Column(Date)
    assignment_end = Column(Date)
    person_id = Column(Integer, ForeignKey('person.person_id'))
    project_id = Column(Integer, ForeignKey('project.project_id'))
    fte = Column(Float)
    timestamp = Column(Date)
    comments = Column(Unicode)
    branch_id = Column(Integer)

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

