import os

import pandas as pd
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Text, create_engine
from sqlalchemy.orm import declarative_base

### these are the database tables
Base = declarative_base()


class Patients(Base):
    __tablename__ = "patients"
    id = Column(String, primary_key=True, index=True)


class Visits(Base):
    __tablename__ = "visits"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    sex = Column(String)
    patient_id = Column(ForeignKey("patients.id"), index=True)
    arrival_date = Column(Date)
    chief_complaint = Column(String)
    diagnosis = Column(String)
    disposition = Column(String)
    referral_order = Column(String)


class Problems(Base):
    __tablename__ = "problems"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    visit_id = Column(ForeignKey("visits.id"))
    problem = Column(String)


class Notes(Base):
    __tablename__ = "notes"
    id = Column(Integer, autoincrement=True, primary_key=True, index=True)
    visit_id = Column(ForeignKey("visits.id"))
    note_type = Column(String)
    author_type = Column(String)
    author_service = Column(String)
    note_text = Column(Text)


# create the database this can be made into a different database/name engine if needed
database = "sqlite:///{}".format("notes.db")
conn = create_engine(database)

Base.metadata.create_all(conn)

# parse processed files and add to database
# I have a decent amount of ram on this computer so I can load the whole thing in one go

all_notes = []
files = os.listdir("processed")

for file in files:
    if file.endswith("tsv"):  # there is other junk like lock files from office
        filepath = os.path.join("processed", file)
        dat = pd.read_csv(filepath, header=0, sep="\t")
        all_notes.append(dat)
    else:
        continue

all_notes = pd.concat(all_notes).drop_duplicates()  # just in case

# change column names so there are no special characters spaces etc and matches the names above
all_notes.columns = ["sex", "age", "arrival_date", "chief_complaint", "note_type", "author_type",
                     "author_service", "diagnosis", "problem_list", "disposition", "referral_order", "note_text", "id"]

# this one is straight forward just one column of unique values
patients = all_notes[["id"]].drop_duplicates()
patients.to_sql(con=conn, if_exists="append", name="patients", index=False)

# keeping patient id because that is a foreign key
visits = all_notes[["sex", "id", "arrival_date", "chief_complaint", "diagnosis", "disposition",
                    "referral_order", "problem_list"]].drop_duplicates()

visits = visits.rename(columns={"id": "patient_id"})
visits[["sex", "patient_id", "arrival_date", "chief_complaint",
        "diagnosis", "disposition", "referral_order"]].to_sql(con=conn, if_exists="append", name="visits", index=False)

# there is an autoincrement column on the visits, since this is the first time we are appending
# to the database it's just 1 throught the num rows of the visits table, if we were to append at a
# later stage we need to get the last id and go from there, some database engines support returning
# command sqlite does not, it is unlikey that we are going to be using some sort of relational database but
# doing GET calls from epic so I'm leaving this here

visits["id"] = list(range(1, visits.shape[0] + 1))
problems = visits[["id", "problem_list"]].drop_duplicates().dropna()

# create a new row for each problem split by ","
problems["problem_list"] = problems["problem_list"].str.split(",")
problems = problems.explode("problem_list")
problems["problem_list"] = problems["problem_list"].str.strip()
# drop empty strings, this keeps whitespace before or after the comma I'm not sure if this is an issue
problems = problems.rename(columns={"problem_list": "problem", "id": "visit_id"})

problems = problems.loc[problems["problem"] != ""]
problems = problems.loc[problems["problem"] != " "]
problems = problems.drop_duplicates()

problems.to_sql(con=conn, if_exists="append", name="problems", index=False)

# need to map notes to visit id
notes = all_notes[["arrival_date", "id", "note_text", "author_type", "author_service", "author_type", "note_type"]]
notes = notes.rename(columns={"id": "patient_id"})
notes = notes.merge(visits[["patient_id", "arrival_date", "id"]], how="left", on=["arrival_date", "patient_id"])

notes = notes[["id", "note_text", "author_type", "author_service", "author_type", "note_type"]]
notes = notes.rename(columns={"id": "visit_id"})

# again just in case
notes = notes.drop_duplicates()
notes.to_sql(con=conn, name="notes", index=False, if_exists="append")
