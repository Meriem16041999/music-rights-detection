CONDUCTOR_WEEKDAY = [
    {"title": "MDP 2025 GENERIQUE DEBUT", "kind": "fixed", "duration": 10},
    {"title": "MDP 2025 NAPPE DEBUT", "kind": "anchor"},
    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP NAPPE TALK", "kind": "anchor"},

    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 JEU REFLEXION", "kind": "dynamic", "expected_next": "MDP 2025 NAPPE CHRONO"},
    {"title": "MDP 2025 NAPPE CHRONO", "kind": "fixed", "duration": 31},

    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 JEU REFLEXION", "kind": "dynamic", "expected_next": "MDP 2025 NAPPE CHRONO"},
    {"title": "MDP 2025 NAPPE CHRONO", "kind": "fixed", "duration": 31},

    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 JEU REFLEXION", "kind": "dynamic", "expected_next": "MDP 2025 NAPPE CHRONO"},
    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 JEU REFLEXION", "kind": "dynamic", "expected_next": "MDP 2025 NAPPE CHRONO"},
    {"title": "MDP 2025 NAPPE CHRONO", "kind": "fixed", "duration": 31},

    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 JEU REFLEXION", "kind": "dynamic", "expected_next": "MDP 2025 NAPPE CHRONO"},
    
    {"title": "MDP 2025 NAPPE CHRONO", "kind": "fixed", "duration": 31},
    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 JEU REFLEXION", "kind": "dynamic", "expected_next": "MDP 2025 NAPPE CHRONO"},

   
 
    {"title": "MDP 2025 NAPPE FIN NEUTRE", "kind": "anchor"},
]


CONDUCTOR_FRIDAY = [
    {"title": "MDP 2025 GENERIQUE DEBUT", "kind": "fixed", "duration": 10},
    {"title": "MDP 2025 NAPPE DEBUT", "kind": "anchor"},
    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP NAPPE TALK", "kind": "anchor"},

    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 NAPPE FINALE REFLEXION", "kind": "dynamic", "expected_next": "MDP 2025 NAPPE CHRONO FINALE"},
    {"title": "MDP 2025 NAPPE CHRONO FINALE", "kind": "anchor"},
    
    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 NAPPE FINALE REFLEXION", "kind": "dynamic", "expected_next": "MDP 2025 NAPPE CHRONO FINALE"},
    {"title": "MDP 2025 NAPPE CHRONO FINALE", "kind": "anchor"},

    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 NAPPE FINALE REFLEXION", "kind": "dynamic", "expected_next": "MDP 2025 NAPPE CHRONO FINALE"},
    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 NAPPE CHRONO FINALE", "kind": "anchor"},

    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 NAPPE FINALE REFLEXION", "kind": "dynamic", "expected_next": "MDP 2025 NAPPE CHRONO FINALE"},
    {"title": "MDP 2025 NAPPE CHRONO FINALE", "kind": "anchor"},

    {"title": "MDP 2025 JINGLE NEUTRE", "kind": "fixed", "duration": 3},
    {"title": "MDP 2025 NAPPE FINALE REFLEXION", "kind": "anchor"},
    {"title": "MDP 2025 FIN GAGNANTE", "kind": "anchor"},
]


def get_mdp_conductor(conductor_type: str):
    if conductor_type == "Vendredi":
        return CONDUCTOR_FRIDAY
    return CONDUCTOR_WEEKDAY