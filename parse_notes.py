# the goal of this scritp is to select notes that contain the key lemma we are interested in
# the action plan is as follows
import medspacy
import pandas as pd
import spacy
from medspacy.context import ConText
from sqlalchemy import create_engine, select, Table, MetaData, or_
from sqlalchemy.orm import Session

from rules import context_rules, target_rules, to_rem
from utils import parse_sentence

# search database for ed notes
# keep a record of each metadata especially visit id
# split note text into sentences
# for each sentence search for lemma in the lists below
# keep sentences containing the lemma in a list along with the metadata for each note
# create another table with symptom metadata for future analysis
# currently there are ~750K notes in ed_notes table I'm hoping this will drastically reduce the #
# of notes we need to parse
# There might be more than one instance of the symptom within the note I will keep all

db = create_engine("sqlite:///notes.db")  # should not hard code this
session = Session(db)
metadata = MetaData(db)
metadata.reflect(bind=db)

spacy.prefer_gpu()

# because we are interested in vomiitng and headache I will do a double filter
# the first filer looks for vommit and the using the selected notes we then look for
# headaches. Keep in mind this is only looking for words, the idea is to "enrich" our notes for
# what we are looking for so we don't have to parse all the notes.
# the selection is done only in the ED notes but changing the query and the table below we can search for any note

ed_types = ["ED Triage Notes", "ED Provider Notes", "ED Notes"]
vomit = ["%vomit%", "%barf%", "%puke%", "%puking%", "%emesis%", "%vx%"]
headache = ["%headache%", "%migraine%", "%head pain%"]

notes_table = Table("notes", metadata, autoload=True, autoload_with=db)
query = select(notes_table). \
    filter(or_(*[notes_table.c.note_type.like(item) for item in ed_types])). \
    filter(or_(*[notes_table.c.note_text.like(item) for item in vomit])). \
    filter(or_(*[notes_table.c.note_text.like(item) for item in headache]))

notes = session.execute(query).fetchall()

# I will be using this to search for lemmas in the note text
search_nlp = spacy.load("en_core_web_trf")

# I will be using these to figure out if the patient has the symptom we are looking for
parse_nlp = spacy.load('en_core_web_trf', disable=["ner"])
med_nlp = medspacy.load(medspacy_enable=['medspacy_sectionizer'])
target = med_nlp.add_pipe("medspacy_target_matcher")

# the context rules here is different from the one that comes w/ medspacy I've edited a number of them
context = ConText(med_nlp, rules="contex_rules.json")
context.add(context_rules)
target.add(target_rules)

lemmas = ["vomit", "barf", "puke", "vx", "emesis", "headache", "migraine", "head pain"]

# parse each sentence and return all the cols and sentences and problems per sentence and final problems in the note

i = 0
nnotes = len(notes)
parsed_notes = []
for note_id, visit_id, note_type, author_type, author_service, note_text in notes:
    parsed_note = {"note_id": note_id,
                   "visit_id": visit_id,
                   "note_type": note_type,
                   "author_type": author_type,
                   "author_service": author_service,
                   "note_text": note_text,
                   "note_problems": [],
                   "relevant_sentences": []}
    doc = search_nlp(note_text)
    note_problems = []
    for sent in doc.sents:
        sent_problems = []
        problem_sent = str(sent)
        for token in sent:
            if token.lemma_ in lemmas:
                probs = parse_sentence(problem_sent, parse_nlp, target, context, to_rem)
                sent_problems = sent_problems + probs
        if len(sent_problems) > 0:
            sent_dict = {"sentence": problem_sent, "problems": list(set(sent_problems))}
            parsed_note["relevant_sentences"].append(sent_dict)
    parsed_note["note_problems"] = list(set(note_problems))
    parsed_notes.append(parsed_note)

    i += 1
    if i % 100 == 0:
        print("{} out of {} notes processed".format(i, nnotes))

parsed_df = pd.DataFrame(parsed_notes)

parsed_df.to_json("parsed_ed_notes.json", orient="records")
