from medspacy.context import ConTextRule
from medspacy.ner import TargetRule

context_rules = context_rules = [
    ConTextRule(literal="?",
                category="POSSIBLE_EXISTENCE",
                direction="BIDIRECTIONAL",
                max_scope=1),
    ConTextRule(literal='not', category='NEGATED_EXISTENCE',
                pattern=[{'LOWER': {'IN': ["haven't", "didn't", "have", "did"]}},
                         {'LOWER': {'IN': ["not"]}},
                         {'LOWER': {'IN': ['appear', 'exihibit', 'demonstrate'
                                                                 'feel', 'reveal']}},
                         {"OP": "?"}], direction='FORWARD', max_scope=1),
    ConTextRule("DETECTED", category="POSSIBLE_EXISTENCE",
                direction="BACKWARD",
                max_scope=1),
    ConTextRule("NOT DETECTED", category="NEGATED_EXISTENCE",
                direction="BACKWARD",
                max_scope=1),
    ConTextRule(literal="not able", category="NEGATED_EXISTENCE",
                pattern=[{"LOWER": {"IN": ['not', "n't"]}},
                         {"LOWER": {"IN": ["can", "will", "could", "would", "won"]}}],
                direction="FORWARD", max_scope=2),
    ConTextRule(literal="x times", category="POSITIVE_EXISTENCE",
                pattern=[{'LOWER': {'IN': ["x"]}},
                         {'LOWER': {'IN': [str(x) for x in range(10)]}}],
                direction="BACKWARD", max_scope=3),
    ConTextRule(literal="times x", pattern=[{"LOWER": {"IN": [str(x) for x in range(10)]}},
                                            {"LOWER": {"IN": ["x"]}}],
                direction="BACKWARD", max_scope=2, category="POSITIVE_EXISTENCE", ),
    ConTextRule(literal="x times", pattern=[{'LOWER': {'IN': [str(x) for x in range(10)]}},
                                            {"LOWER": {"IN": ["times"]}}],
                category="POSITIVE_EXISTENCE", direction="BACKWARD", max_scope=3),
    ConTextRule(literal="x regex", pattern=[{'LOWER': {'REGEX': "[0-9]x"}}],
                category="POSITIVE_EXISTENCE", direction="BIDIRECTIONAL", max_scope=3),
    ConTextRule(literal="regex x", pattern=[{'LOWER': {'REGEX': "x[0-9]"}}],
                category="POSITIVE_EXISTENCE", direction="BIDIRECTIONAL", max_scope=3),
    ConTextRule(literal="fh", category="FAMILY", direction="FORWARD"),
    ConTextRule(literal="episodes", category="POSITIVE_EXISTENCE", direction="FORWARD", max_scope=4,
                pattern=[{"LOWER": {'IN': ["episodes", "episodes of", "continued", "episode"]}}]),
    ConTextRule(literal="reported", category="POSITIVE_EXISTENCE", direction="FORWARD"),
    ConTextRule(literal="feels", category="POSSIBLE_EXISTENCE", direction="FORWARD",
                pattern=[{"LOWER": {"IN": ["feels"]}},
                         {"LOWER": {"IN": ["like"]}}]),
    ConTextRule(literal="past", category="HISTORICAL", direction="FORWARD", max_scope=2),
    ConTextRule(literal="presenting", category="POSITIVE_EXISTENCE", direction="FORWARD", max_scope=10),
    # arbitrary, don't wanna over/under do
    ConTextRule(literal="some", category="POSITIVE_EXISTENCE", direction="FORWARD", max_scope=1),
    # arbitrary, don't wanna over/under do
    ConTextRule(literal="here with", category="POSITIVE_EXISTENCE", direction="FORWARD"),
    # ConTextRule(literal="complains", category="POSITIVE_EXISTENCE", direction="FORWARD", pattern=[{"LOWER":{"IN":["complains", "complained"]}}]),
    ConTextRule(literal="diagnosis", category="POSITIVE_EXISTENCE",
                pattern=[{'LOWER': {'IN': ["diagnosed", "diagnosed with", "dx", "diagnosis"]}}],
                direction="FORWARD"),
    ConTextRule(literal="positive for", category="POSITIVE_EXISTENCE", direction="forward",
                pattern=[{"LOWER": {"IN": ["positivie"]}},
                         {"LOWER": {"IN": ["for"]}}]),
    ConTextRule(literal="parent says", category="POSITIVE_EXISTENCE",
                pattern=[{"LOWER": {"IN": ["parent", "parents", "mom", "dad", "father", "mother", "family"]}},
                         {"LOWER": {"IN": ["says", "states", "reports", "report", "say", "state", "is aware"]}}],
                direction="FORWARD", max_scope=10),
    ConTextRule(" - ", "CONJ", direction="TERMINATE", pattern=[{"LOWER": {"IN": [" - ", " -", "- "]}}]),
    ConTextRule(";", "CONJ", direction="TERMINATE"),
    ConTextRule("(", "CONJ", direction="TERMINATE"),
    ConTextRule(")", "CONJ", direction="TERMINATE"),
    # ConTextRule("no", direction="FORWARD", category="NEGATED_EXISTENCE", max_scope=5),

    # ConTextRule(". ", "CONJ", direction="TERMINATE"),
    # ConTextRule(literal="parent states", category="POSITIVE_EXISTENCE",
    #           direction="FORWARD")
]

target_rules = [
    TargetRule(literal="vomit",
               category="PROBLEM",
               pattern=[{"TEXT": {"REGEX": "vomit|barf|puk(e|ing)|emesis|vx"}}]),

    TargetRule(literal="headache",
               category="PROBLEM",
               pattern=[{"LOWER": {"IN": ["headache", "migraine", "head pain", "headaches", "migraines"]}},
                        {"LOWER": {"NOT_IN": ["abdominal", "abdo"]}}  # abdominal migraines
                        ]),
]

to_rem = ["history of presenting illness", "my summary of the history"]
