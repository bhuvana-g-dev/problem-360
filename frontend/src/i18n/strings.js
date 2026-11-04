// UI strings. English is the source; Tamil was drafted by Kiro and NEEDS A FLUENT READER'S CHECK before real use
// (same rule as agent/safety.py). Values sent to the backend (categories, localities) stay in English: only labels change.
export const STRINGS = {
  en: {
    'lang.switch': 'தமிழ்', 'lang.switchLabel': 'Switch to Tamil',
    'report.title': 'Report a problem', 'report.what': 'What’s the problem?',
    'report.placeholder': 'What is wrong, and how long has it been like this?',
    'report.category': 'Category', 'report.locality': 'Locality', 'report.select': 'Select',
    'report.landmark': 'Landmark / street (optional)', 'report.landmarkPh': 'e.g. opposite the bus stop',
    'report.locate': 'Use my current location', 'report.post': 'Post',
    'geo.unavailable': 'Location isn’t available on this device.', 'geo.finding': 'Finding your location…',
    'geo.added': 'Location added.', 'geo.fail': 'Couldn’t get your location. You can still describe it in words.',
    'geo.coords': 'Location', 'geo.openMap': 'Open on map', 'geo.accuracy': 'accurate to about', 'geo.remove': 'Remove location',
    'geo.weak': 'This is only approximate (a laptop or a weak signal). Add a landmark or street name as well.',
    'geo.mapTitle': 'Map showing the reported location', 'geo.mapNote': 'The map is loaded from OpenStreetMap when it is shown.',
    'err.description': 'Describe the problem in at least 15 characters.', 'err.category': 'Choose a category.', 'err.locality': 'Choose a locality.',
    'voice.start': 'Speak instead of typing', 'voice.stop': 'Stop listening', 'voice.listening': 'Listening… speak now.',
    'voice.privacy': 'Your browser’s speech service turns your voice into text. Check the text before posting.',
    'voice.error': 'Couldn’t hear that. Check microphone permission, or type instead.',
    'dp.reviewing': 'Strands Decider is reviewing this report…', 'dp.failedTitle': 'Automatic review could not run',
    'dp.retry': 'Try the review again', 'dp.urgent': 'Treated as urgent. In an emergency call 112.', 'dp.similar': 'Similar to report',
    'dp.dept': 'Recommended department:', 'dp.deptNote': 'This is a recommendation; no department has been contacted.',
    'dp.events': 'Upcoming volunteer events nearby:', 'dp.human': 'Marked for human review.',
    'rv.checked': 'Checked by a person', 'rv.waiting': 'Waiting for a person to check',
    'rv.waitingText': 'A Problem 360 reviewer will look at this report. You will get a notification when they do.',
    'rv.ack': 'A reviewer acknowledged this report.', 'rv.ackResolved': 'A reviewer acknowledged this report and marked it resolved.',
    'rv.closed': 'A reviewer closed this report.', 'rv.note': 'Note:', 'nav.backToFeed': 'Back to feed',
  },
  ta: {
    'lang.switch': 'English', 'lang.switchLabel': 'ஆங்கிலத்திற்கு மாற்று',
    'report.title': 'ஒரு பிரச்சனையைத் தெரிவிக்கவும்', 'report.what': 'என்ன பிரச்சனை?',
    'report.placeholder': 'என்ன தவறு, எவ்வளவு நாளாக இப்படி இருக்கிறது?',
    'report.category': 'வகை', 'report.locality': 'பகுதி', 'report.select': 'தேர்ந்தெடுக்கவும்',
    'report.landmark': 'அடையாளம் / தெரு (விருப்பம்)', 'report.landmarkPh': 'எ.கா. பேருந்து நிறுத்தம் எதிரில்',
    'report.locate': 'என் தற்போதைய இடத்தைப் பயன்படுத்து', 'report.post': 'பதிவிடு',
    'geo.unavailable': 'இந்தச் சாதனத்தில் இட வசதி இல்லை.', 'geo.finding': 'உங்கள் இடத்தைக் கண்டறிகிறது…',
    'geo.added': 'இடம் சேர்க்கப்பட்டது.', 'geo.fail': 'உங்கள் இடத்தைப் பெற முடியவில்லை. இடத்தை வார்த்தைகளில் விவரிக்கலாம்.',
    'geo.coords': 'இடம்', 'geo.openMap': 'வரைபடத்தில் திற', 'geo.accuracy': 'துல்லியம் சுமார்', 'geo.remove': 'இடத்தை நீக்கு',
    'geo.weak': 'இது தோராயமானது மட்டுமே (மடிக்கணினி அல்லது பலவீனமான சிக்னல்). அடையாளம் அல்லது தெருப் பெயரையும் சேர்க்கவும்.',
    'geo.mapTitle': 'புகாரளிக்கப்பட்ட இடத்தைக் காட்டும் வரைபடம்', 'geo.mapNote': 'வரைபடம் காட்டப்படும்போது OpenStreetMap இலிருந்து ஏற்றப்படுகிறது.',
    'err.description': 'பிரச்சனையை குறைந்தது 15 எழுத்துகளில் விவரிக்கவும்.', 'err.category': 'ஒரு வகையைத் தேர்ந்தெடுக்கவும்.',
    'err.locality': 'ஒரு பகுதியைத் தேர்ந்தெடுக்கவும்.',
    'voice.start': 'தட்டச்சுக்குப் பதில் பேசுங்கள்', 'voice.stop': 'கேட்பதை நிறுத்து', 'voice.listening': 'கேட்கிறது… இப்போது பேசுங்கள்.',
    'voice.privacy': 'உங்கள் உலாவியின் பேச்சு சேவை உங்கள் குரலை எழுத்தாக மாற்றுகிறது. பதிவிடும் முன் எழுத்தைச் சரிபார்க்கவும்.',
    'voice.error': 'கேட்க முடியவில்லை. மைக்ரோஃபோன் அனுமதியைச் சரிபார்க்கவும், அல்லது தட்டச்சு செய்யவும்.',
    'dp.reviewing': 'Strands Decider இந்தப் புகாரை ஆய்வு செய்கிறது…', 'dp.failedTitle': 'தானியங்கி ஆய்வு இயங்கவில்லை',
    'dp.retry': 'மீண்டும் ஆய்வு செய்', 'dp.urgent': 'அவசரமாகக் கருதப்பட்டது. அவசர நிலையில் 112 அழையுங்கள்.', 'dp.similar': 'இதைப் போன்ற புகார்',
    'dp.dept': 'பரிந்துரைக்கப்பட்ட துறை:', 'dp.deptNote': 'இது பரிந்துரை மட்டுமே; எந்தத் துறையும் தொடர்பு கொள்ளப்படவில்லை.',
    'dp.events': 'அருகிலுள்ள வரவிருக்கும் தன்னார்வ நிகழ்வுகள்:', 'dp.human': 'மனித ஆய்வுக்குக் குறிக்கப்பட்டது.',
    'rv.checked': 'ஒருவர் சரிபார்த்தார்', 'rv.waiting': 'ஒருவர் சரிபார்க்கக் காத்திருக்கிறது',
    'rv.waitingText': 'Problem 360 ஆய்வாளர் ஒருவர் இந்தப் புகாரைப் பார்வையிடுவார். அப்போது உங்களுக்கு அறிவிப்பு வரும்.',
    'rv.ack': 'ஆய்வாளர் இந்தப் புகாரை ஏற்றுக்கொண்டார்.', 'rv.ackResolved': 'ஆய்வாளர் இந்தப் புகாரை ஏற்று, தீர்க்கப்பட்டதாகக் குறித்தார்.',
    'rv.closed': 'ஆய்வாளர் இந்தப் புகாரை மூடினார்.', 'rv.note': 'குறிப்பு:', 'nav.backToFeed': 'செய்திகளுக்குத் திரும்பு',
  },
}

export const ACTION_LABELS_I18N = {
  en: {
    CREATE_REPORT: 'Report recorded', CHECK_DUPLICATE: 'Possible duplicate', FLAG_URGENT: 'Flagged as urgent',
    REQUEST_MORE_INFORMATION: 'More information needed', ROUTE_TO_DEPARTMENT: 'Department recommended',
    SUGGEST_COMMUNITY_ACTION: 'Community action suggested', ESCALATE_FOR_HUMAN_REVIEW: 'Sent for human review',
  },
  ta: {
    CREATE_REPORT: 'புகார் பதிவு செய்யப்பட்டது', CHECK_DUPLICATE: 'ஒத்த புகார் இருக்கலாம்', FLAG_URGENT: 'அவசரமாகக் குறிக்கப்பட்டது',
    REQUEST_MORE_INFORMATION: 'கூடுதல் விவரம் தேவை', ROUTE_TO_DEPARTMENT: 'துறை பரிந்துரைக்கப்பட்டது',
    SUGGEST_COMMUNITY_ACTION: 'சமூக உதவி பரிந்துரைக்கப்பட்டது', ESCALATE_FOR_HUMAN_REVIEW: 'மனித ஆய்வுக்கு அனுப்பப்பட்டது',
  },
}

export const CATEGORY_TA = {
  'Roads & potholes': 'சாலைகள் & பள்ளங்கள்', 'Waste & sanitation': 'குப்பை & சுகாதாரம்', 'Water supply': 'குடிநீர் விநியோகம்',
  'Drainage & flooding': 'வடிகால் & வெள்ளம்', 'Street lighting': 'தெருவிளக்கு', Electricity: 'மின்சாரம்',
  'Public transport': 'பொதுப் போக்குவரத்து', 'Parks & public spaces': 'பூங்காக்கள் & பொது இடங்கள்', 'Public safety': 'பொதுப் பாதுகாப்பு', Other: 'மற்றவை',
}
