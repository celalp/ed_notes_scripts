import os
import re
import uuid

import Levenshtein as ls
import pandas as pd
import spacy

from utils import split


class MultipleNamesError(Exception):
    pass


spacy.prefer_gpu()
nlp = spacy.load("en_core_web_trf")

# this is assuming that the structure of the notes (as presented to me in the excel files do not change"
cols_to_keep = ["CSN", "MRN", "Patient Name", "Sex", "Age (Years)", "Arrival Date", "Chief Complaint",
                "Note Type", "Author Type", "Author's Service", "Diagnosis",
                "Problem List", "Disposition", "Referral Order", "Note Text"]


def deidentify(df, name_col="Patient Name", text_col="Note Text", language=nlp):
    """
    2 downsides to this method
    + its slow
    + if there is another person that shares a name or a last name they will be
    removed as well
    :param df: a pandas dataframe
    :param name_col: name of the column that contains the id, cannot remove name without having the name in the first place
    :param text_col: name of the column that contains the note text
    """
    name = df[name_col].drop_duplicates().to_list()
    if len(name) > 1:
        raise MultipleNamesError("There are multiple patients by that CSN")
    else:
        name = name[0]
        name = name.lower()
        name = name.replace(",", " ").split(" ")
        note_list = df.to_dict(orient="records")
        for i in range(len(note_list)):
            note_text = note_list[i][text_col]
            if pd.isna(note_text):
                continue
            else:
                note_text = str(note_text)
                note_text = note_text.lower()
                note_text = re.sub(" +", " ", note_text)
                split_note = note_text.split(" ")
                note_len = len(split_note)
                docs = []
                if note_len > 512:  # if the note is really long unlikely but possible > 512 words
                    split_notes = split(split_note, 512, combine=True, join_w=" ")
                    for note in split_notes:
                        docs.append(language(note))
                else:
                    docs.append(language(note_text))
                people = []
                for doc in docs:
                    people = people + [ent for ent in doc.ents if ent.label_ == "PERSON"]

                for word in name:
                    for person in people:
                        person = str(person)
                        person_split = person.split(" ")
                        for person_word in person_split:
                            dist = ls.distance(word, str(person_word))
                            if len(word) < 4:  # no typos
                                if dist == 0:
                                    note_text = note_text.replace(person, "[redacted]")
                            elif len(word) < 6:
                                if dist <= 1:
                                    note_text = note_text.replace(person, "[redacted]")
                            else:
                                if dist <= 2:
                                    note_text = note_text.replace(person, "[redacted]")
                # removing these because they do not contain any important information contain patient info
                note_text = re.sub("mrn(:| )*[0-9]+", "[redacted]", note_text)
                note_text = re.sub(" dob(:| )*[0-9]+/[0-9]+/[0-9]+", "[redacted]", note_text)

            note_list[i]["Note Text"] = note_text
        note_df = pd.DataFrame(note_list)
        # note_df=note_df.drop(columns=["Patient Name", "CSN"])
        return note_df


# below chunk is how I processed the notes, this may or may not be the case going forward, if we are going to
# conntect to epic api directly I would need to re-write this with resquest or urllib with http get commands and
# json parsing, I'm keeping this code here for transparency

if __name__ == "__main__":

    root_files = os.listdir()

    xls = []
    for root, subdir, files in os.walk("."):
        for file in files:
            if file.endswith(("xlsx", "xls")):
                path = os.path.join(root, file)
                xls.append(path)

    if "uuids.tsv" not in root_files:
        names = []
        for file in xls:
            dat = pd.read_excel(file, header=0, sheet_name=0, skiprows=1, usecols="B:C").drop_duplicates()
            names.append(dat)

        names = pd.concat(names)
        names = names.drop_duplicates()

        ids = [uuid.uuid4() for _ in range(names.shape[0])]
        names["id"] = ids

        names.to_csv("uuids.tsv", index=False, sep="\t")
    else:
        names = pd.read_csv("uuids.tsv", header=0, sep="\t")

    for file in xls:
        processed_name = re.sub(".*/", "", file)
        processed_name = processed_name.replace("xlsx", "tsv")
        # because some are older versions for some reason
        processed_name = processed_name.replace("xls", "tsv")
        already_done = os.listdir("processed")
        if processed_name in already_done:
            print("Already Processed {}. Skipping".format(file))
            continue
        else:
            print("Processing {}".format(file))
            notes = pd.read_excel(file, sheet_name=0, header=0, skiprows=1).drop_duplicates()
            notes = notes[cols_to_keep].copy()

            # this one is a nigthmare of identifiable information with no set structure
            # since this is a summary I'm going to ignore these, not every patient has this
            # note so it's even less useful
            notes = notes[~notes["Note Text"]. \
                str.contains("The Hospital for Sick Children Inpatient Discharge Summary").fillna(False)]

            # this is per visit de-identification
            patient_dfs = [df for _, df in notes.groupby("CSN")]

            df_list = []
            for df in patient_dfs:
                df_list.append(deidentify(df))

            df_concat = pd.concat(df_list)
            df_concat = df_concat.merge(names, on=["MRN", "Patient Name"], how="left")
            df_concat = df_concat.drop(columns=["CSN", "MRN", "Patient Name"])
            df_concat.to_csv("processed/{}".format(processed_name), index=False, sep="\t")
