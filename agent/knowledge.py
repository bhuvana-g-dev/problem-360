"""Facts owned by CODE, not by the model. The model reads them through tools and cannot change them.

REVIEW BEFORE PRODUCTION: department names are routing labels based on public knowledge of Madurai's civic
bodies. A local person must confirm them (and record who/when) before any real routing is relied upon."""
import re

DEPARTMENTS = {
    "roads": {"name": "Madurai City Municipal Corporation — Roads & Engineering", "categories": ["Roads & potholes"],
              "hint": "potholes, damaged roads, broken footpaths, road repair"},
    "sanitation": {"name": "Madurai City Municipal Corporation — Sanitation & Solid Waste", "categories": ["Waste & sanitation"],
                   "hint": "uncollected garbage, overflowing bins, dumping, dead animals, public toilets"},
    "water_drainage": {"name": "Madurai City Municipal Corporation — Water Supply & Drainage", "categories": ["Water supply", "Drainage & flooding"],
                       "hint": "no drinking water, leaking pipes, blocked drains, sewage overflow, waterlogging"},
    "street_lighting": {"name": "Madurai City Municipal Corporation — Street Lighting", "categories": ["Street lighting"],
                        "hint": "street lights not working or flickering"},
    "electricity": {"name": "Electricity distribution utility (TNEB)", "categories": ["Electricity"],
                    "hint": "power cuts, fallen or sparking electric lines, transformer faults"},
    "transport": {"name": "Public transport / Transport department", "categories": ["Public transport"],
                  "hint": "bus services, bus stops, traffic signals"},
    "parks": {"name": "Madurai City Municipal Corporation — Parks & Public Spaces", "categories": ["Parks & public spaces"],
              "hint": "parks, playgrounds, public ponds, encroachment on public land"},
    "police": {"name": "Madurai City Police", "categories": ["Public safety"],
               "hint": "crime, harassment, safety threats that need police"},
    "unclear": {"name": "Not clear — needs a person to decide", "categories": ["Other"], "hint": "does not fit any department above"},
}
CATEGORY_TO_DEPARTMENT = {c: d for d, v in DEPARTMENTS.items() for c in v["categories"]}

# Reports mentioning these are urgent regardless of any model. Word-boundary match for English; substring for
# Tamil phrases (Python's \w splits Tamil words, so we do not use \b there). Tamil entries need a fluent reader's check.
URGENT_EN = [r"live wires?", r"exposed wires?", r"electric shock", r"electrocut\w*", r"sparking", r"gas leak\w*",
             r"on fire", r"caught fire", r"fire(?! (?:station|brigade|engine|department|office|extinguisher|exit|safety))", r"burning", r"open manhole", r"manhole (is )?open", r"collaps\w*",
             r"drown\w*", r"trapped", r"unconscious", r"bleeding", r"explosion", r"wire (has )?fallen", r"snapped wire"]
URGENT_TA = ["தீப்பிடி", "எரிவாயு கசிவு", "கேஸ் கசிவு", "மின்கம்பி அறுந்து", "ஷாக் அடி", "மேன்ஹோல் திறந்து", "இடிந்து விழ"]
_URGENT_RE = re.compile(r"\b(?:" + "|".join(URGENT_EN) + r")\b", re.I)


def urgent_keyword_hits(text: str) -> list[str]:
    hits = [m.group(0).lower() for m in _URGENT_RE.finditer(text)]
    hits += [p for p in URGENT_TA if p in text]
    return sorted(set(hits))


# Community participation: only low-risk categories. Anything with electricity, water, traffic or crime is never suggested.
# Tamil text needs a fluent reader's check (record who and when in agent/data/guidance.json).
COMMUNITY_IDEAS = {
    "Waste & sanitation": "Neighbours could organise a short clean-up with gloves and bags. Do not touch sharp, medical, chemical or dead-animal waste; report that instead.",
    "Parks & public spaces": "Neighbours could organise a park clean-up or planting day in coordination with the park's caretaker.",
}
COMMUNITY_IDEAS_TA = {
    "Waste & sanitation": "அக்கம்பக்கத்தினர் கையுறை, பைகளுடன் ஒரு சிறிய சுத்தம் செய்யும் பணியை ஏற்பாடு செய்யலாம். கூர்மையான, மருத்துவ, "
                          "ரசாயனக் கழிவுகளையோ இறந்த விலங்குகளையோ தொட வேண்டாம்; அவற்றைப் புகாராகத் தெரிவியுங்கள்.",
    "Parks & public spaces": "பூங்கா பராமரிப்பாளருடன் இணைந்து அக்கம்பக்கத்தினர் பூங்கா சுத்தம் அல்லது மரம் நடும் நாளை ஏற்பாடு செய்யலாம்.",
}
COMMUNITY_CITE = {"Waste & sanitation": "G-COMMUNITY-WASTE", "Parks & public spaces": "G-COMMUNITY-PARKS"}

# Emergency numbers: only numbers with a source in agent/data/guidance.json (G-EMERGENCY-112, G-AMBULANCE-108).
EMERGENCY_NUMBERS = {"112", "108"}
EMERGENCY_NOTE = "If anyone is in immediate danger, call 112 now (police, fire, ambulance) or 108 for an ambulance."
