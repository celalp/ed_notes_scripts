import re
from math import ceil


def split(ls, max_size, combine=True, join_w=" "):
    """
    if the note lenght is too long split it down in the middle, this is for deidentification only it will not effect the
    document itself see deidenitfy below
    :param ls: note text as a list
    :param max_size: maximum size allowed
    :param combine: combine the individual tokens back together with
    :param join_w: the separator for the combination
    :return: another list but the note text is split into n pieces depending on the max_size
    """
    n = ceil(len(ls) / max_size)
    size = ceil(len(ls) / n)
    split_list = [ls[i * size:i * size + size] for i in range(n)]
    if combine:
        combined = []
        for ls in split_list:
            combined.append(join_w.join(ls))
        return combined
    else:
        return split_list


def parse_sentence(sentence, nlp, target, context, to_rem):
    """
    for each sentence in a pandas dataframe parse the sentence and if the problem(s) are in the sentence return the name
    of the problem
    nlp: spacy language model
    targets: target matcher
    context: context matcher
    """
    target_list = [x.literal for x in target.rules]
    try:  # there are some sentences that are not really sentences so spacy parser is having a hard time with them.
        for string in to_rem:
            sentence = re.sub(string, "", sentence)
        doc = nlp(sentence)
        tar = target(doc)
        con = context(tar)
        problems = []
        for ent in con.ents:
            if ent.label_ == "PROBLEM":
                if not ent._.is_family and not ent._.is_historical \
                        and not ent._.is_hypothetical and not ent._.is_negated \
                        and not ent._.is_uncertain:
                    if ent._.literal in target_list:  # to make sure that I get the correct ent
                        problems.append(ent._.literal)
                else:
                    for mod in ent._.modifiers:
                        if mod.category == "POSITIVE_EXISTENCE":
                            problems.append(ent._.literal)
        if len(problems) == 0:
            problems = ["none"]
        else:
            problems = list(set(problems))

    except Exception as e:
        # this is the part we quietly skip the sentence
        problems = ["parse error"]
        print(e)

    finally:
        return problems
