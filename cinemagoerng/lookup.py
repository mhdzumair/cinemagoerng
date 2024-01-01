# Copyright 2023 H. Turgut Uyar <uyar@tekir.org>
#
# CinemagoerNG is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# CinemagoerNG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CinemagoerNG; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

COUNTRY_CODES = {
    "AD": "Andorra",
    "AE": "United Arab Emirates",
    "AF": "Afghanistan",
    "AG": "Antigua & Barbuda",
    "AI": "Anguilla",
    "AL": "Albania",
    "AM": "Armenia",
    "AN": "Netherlands Antilles",
    "AO": "Angola",
    "AQ": "Antarctica",
    "AR": "Argentina",
    "AS": "American Samoa",
    "AT": "Austria",
    "AU": "Australia",
    "AW": "Aruba",
    "AX": "Åland Islands",
    "AZ": "Azerbaijan",
    "BA": "Bosnia & Herzegovina",
    "BB": "Barbados",
    "BD": "Bangladesh",
    "BE": "Belgium",
    "BF": "Burkina Faso",
    "BG": "Bulgaria",
    "BH": "Bahrain",
    "BI": "Burundi",
    "BJ": "Benin",
    "BL": "St. Barthélemy",
    "BM": "Bermuda",
    "BN": "Brunei",
    "BO": "Bolivia",
    "BQ": "Caribbean Netherlands",
    "BR": "Brazil",
    "BS": "Bahamas",
    "BT": "Bhutan",
    "BUMM": "Burma",
    "BV": "Bouvet Island",
    "BW": "Botswana",
    "BY": "Belarus",
    "BZ": "Belize",
    "CA": "Canada",
    "CC": "Cocos (Keeling) Islands",
    "CD": "Congo - Kinshasa",
    "CF": "Central African Republic",
    "CG": "Congo - Brazzaville",
    "CH": "Switzerland",
    "CI": "Côte d’Ivoire",
    "CK": "Cook Islands",
    "CL": "Chile",
    "CM": "Cameroon",
    "CN": "China",
    "CO": "Colombia",
    "CR": "Costa Rica",
    "CSHH": "Czechoslovakia",
    "CSXX": "Serbia and Montenegro",
    "CU": "Cuba",
    "CV": "Cape Verde",
    "CW": "Curaçao",
    "CX": "Christmas Island",
    "CY": "Cyprus",
    "CZ": "Czechia",
    "DDDE": "East Germany",
    "DE": "Germany",
    "DJ": "Djibouti",
    "DK": "Denmark",
    "DM": "Dominica",
    "DO": "Dominican Republic",
    "DZ": "Algeria",
    "EC": "Ecuador",
    "EE": "Estonia",
    "EG": "Egypt",
    "EH": "Western Sahara",
    "ER": "Eritrea",
    "ES": "Spain",
    "ET": "Ethiopia",
    "FI": "Finland",
    "FJ": "Fiji",
    "FK": "Falkland Islands",
    "FM": "Micronesia",
    "FO": "Faroe Islands",
    "FR": "France",
    "GA": "Gabon",
    "GB": "United Kingdom",
    "GD": "Grenada",
    "GE": "Georgia",
    "GF": "French Guiana",
    "GG": "Guernsey",
    "GH": "Ghana",
    "GI": "Gibraltar",
    "GL": "Greenland",
    "GM": "Gambia",
    "GN": "Guinea",
    "GP": "Guadeloupe",
    "GQ": "Equatorial Guinea",
    "GR": "Greece",
    "GS": "South Georgia & South Sandwich Islands",
    "GT": "Guatemala",
    "GU": "Guam",
    "GW": "Guinea-Bissau",
    "GY": "Guyana",
    "HK": "Hong Kong SAR China",
    "HM": "Heard & McDonald Islands",
    "HN": "Honduras",
    "HR": "Croatia",
    "HT": "Haiti",
    "HU": "Hungary",
    "ID": "Indonesia",
    "IE": "Ireland",
    "IL": "Israel",
    "IM": "Isle of Man",
    "IN": "India",
    "IO": "British Indian Ocean Territory",
    "IQ": "Iraq",
    "IR": "Iran",
    "IS": "Iceland",
    "IT": "Italy",
    "JE": "Jersey",
    "JM": "Jamaica",
    "JO": "Jordan",
    "JP": "Japan",
    "KE": "Kenya",
    "KG": "Kyrgyzstan",
    "KH": "Cambodia",
    "KI": "Kiribati",
    "KM": "Comoros",
    "KN": "St. Kitts & Nevis",
    "KP": "North Korea",
    "KR": "South Korea",
    "KW": "Kuwait",
    "KY": "Cayman Islands",
    "KZ": "Kazakhstan",
    "LA": "Laos",
    "LB": "Lebanon",
    "LC": "St. Lucia",
    "LI": "Liechtenstein",
    "LK": "Sri Lanka",
    "LR": "Liberia",
    "LS": "Lesotho",
    "LT": "Lithuania",
    "LU": "Luxembourg",
    "LV": "Latvia",
    "LY": "Libya",
    "MA": "Morocco",
    "MC": "Monaco",
    "MD": "Moldova",
    "ME": "Montenegro",
    "MF": "St. Martin",
    "MG": "Madagascar",
    "MH": "Marshall Islands",
    "MK": "North Macedonia",
    "ML": "Mali",
    "MM": "Myanmar (Burma)",
    "MN": "Mongolia",
    "MO": "Macao SAR China",
    "MP": "Northern Mariana Islands",
    "MQ": "Martinique",
    "MR": "Mauritania",
    "MS": "Montserrat",
    "MT": "Malta",
    "MU": "Mauritius",
    "MV": "Maldives",
    "MW": "Malawi",
    "MX": "Mexico",
    "MY": "Malaysia",
    "MZ": "Mozambique",
    "NA": "Namibia",
    "NC": "New Caledonia",
    "NE": "Niger",
    "NF": "Norfolk Island",
    "NG": "Nigeria",
    "NI": "Nicaragua",
    "NL": "Netherlands",
    "NO": "Norway",
    "NP": "Nepal",
    "NR": "Nauru",
    "NU": "Niue",
    "NZ": "New Zealand",
    "OM": "Oman",
    "PA": "Panama",
    "PE": "Peru",
    "PF": "French Polynesia",
    "PG": "Papua New Guinea",
    "PH": "Philippines",
    "PK": "Pakistan",
    "PL": "Poland",
    "PM": "St. Pierre & Miquelon",
    "PN": "Pitcairn Islands",
    "PR": "Puerto Rico",
    "PS": "Palestinian Territories",
    "PT": "Portugal",
    "PW": "Palau",
    "PY": "Paraguay",
    "QA": "Qatar",
    "RE": "Réunion",
    "RO": "Romania",
    "RS": "Serbia",
    "RU": "Russia",
    "RW": "Rwanda",
    "SA": "Saudi Arabia",
    "SB": "Solomon Islands",
    "SC": "Seychelles",
    "SD": "Sudan",
    "SE": "Sweden",
    "SG": "Singapore",
    "SH": "St. Helena",
    "SI": "Slovenia",
    "SJ": "Svalbard & Jan Mayen",
    "SK": "Slovakia",
    "SL": "Sierra Leone",
    "SM": "San Marino",
    "SN": "Senegal",
    "SO": "Somalia",
    "SR": "Suriname",
    "ST": "São Tomé & Príncipe",
    "SUHH": "Soviet Union",
    "SV": "El Salvador",
    "SY": "Syria",
    "SZ": "Eswatini",
    "TC": "Turks & Caicos Islands",
    "TD": "Chad",
    "TF": "French Southern Territories",
    "TG": "Togo",
    "TH": "Thailand",
    "TJ": "Tajikistan",
    "TK": "Tokelau",
    "TL": "Timor-Leste",
    "TM": "Turkmenistan",
    "TN": "Tunisia",
    "TO": "Tonga",
    "TR": "Turkey",
    "TT": "Trinidad & Tobago",
    "TV": "Tuvalu",
    "TW": "Taiwan",
    "TZ": "Tanzania",
    "UA": "Ukraine",
    "UG": "Uganda",
    "UM": "U.S. Outlying Islands",
    "US": "United States",
    "UY": "Uruguay",
    "UZ": "Uzbekistan",
    "VA": "Vatican City",
    "VC": "St. Vincent & Grenadines",
    "VDVN": "North Vietnam",
    "VE": "Venezuela",
    "VG": "British Virgin Islands",
    "VI": "U.S. Virgin Islands",
    "VN": "Vietnam",
    "VU": "Vanuatu",
    "WF": "Wallis & Futuna",
    "WS": "Samoa",
    "XKO": "Korea",
    "XKV": "Kosovo",
    "XPI": "Palestine",
    "XSI": "Siam",
    "XWG": "West Germany",
    "XYU": "Yugoslavia",
    "YE": "Yemen",
    "YT": "Mayotte",
    "YUCS": "Federal Republic of Yugoslavia",
    "ZA": "South Africa",
    "ZM": "Zambia",
    "ZRCD": "Zaire",
    "ZW": "Zimbabwe",
}

LANGUAGE_CODES = {
    "AB": "Abkhazian",
    "AF": "Afrikaans",
    "AII": "Assyrian Neo-Aramaic",
    "AK": "Akan",
    "ALE": "Aleut",
    "ALG": "Algonquin",
    "AM": "Amharic",
    "AN": "Aragonese",
    "ANG": "Old English",
    "APA": "Apache languages",
    "AQC": "Archi",
    "AR": "Arabic",
    "ARC": "Aramaic",
    "ARN": "Mapudungun",
    "ARP": "Arapaho",
    "AS": "Assamese",
    "ASB": "Assiniboine",
    "ASE": "American Sign Language",
    "ASF": "Australian Sign Language",
    "AST": "Bable",
    "ATH": "Athapascan languages",
    "AWA": "Awadhi",
    "AY": "Aymara",
    "AZ": "Azerbaijani",
    "BA": "Bashkir",
    "BAN": "Balinese",
    "BE": "Belarusian",
    "BEM": "Bemba",
    "BER": "Berber languages",
    "BFI": "British Sign Language",
    "BFW": "Bonda",
    "BG": "Bulgarian",
    "BGC": "Haryanvi",
    "BHO": "Bhojpuri",
    "BM": "Bambara",
    "BN": "Bengali",
    "BO": "Tibetan",
    "BR": "Breton",
    "BS": "Bosnian",
    "BSC": "Bassari",
    "BSK": "Burushaski",
    "BZS": "Brazilian Sign Language",
    "CA": "Catalan",
    "CCP": "Chakma",
    "CE": "Chechen",
    "CHR": "Cherokee",
    "CHY": "Cheyenne",
    "CKT": "Chukchi",
    "CMN": "Mandarin",
    "CO": "Corsican",
    "CR": "Cree",
    "CRO": "Crow",
    "CS": "Czech",
    "CY": "Welsh",
    "DA": "Danish",
    "DE": "German",
    "DIN": "Dinka",
    "DOI": "Dogri",
    "DSO": "Desiya",
    "DYO": "Jola-Fonyi",
    "DYU": "Dyula",
    "DZ": "Dzongkha",
    "EE": "Ewe",
    "EGY": "Egyptian (Ancient)",
    "EL": "Greek",
    "EN": "English",
    "ENM": "Middle English",
    "EO": "Esperanto",
    "ES": "Spanish",
    "ET": "Estonian",
    "EU": "Basque",
    "FA": "Persian",
    "FF": "Fulah",
    "FI": "Finnish",
    "FIL": "Filipino",
    "FO": "Faroese",
    "FON": "Fon",
    "FR": "French",
    "FRS": "Eastern Frisian",
    "FSL": "French Sign Language",
    "FUF": "Pular",
    "FUR": "Friulian",
    "FVR": "Fur",
    "GA": "Irish Gaelic",
    "GBJ": "Gutob",
    "GD": "Gaelic",
    "GL": "Galician",
    "GN": "Guarani",
    "GNN": "Gumatj",
    "GRB": "Grebo",
    "GRC": "Greek, Ancient (to 1453)",
    "GSG": "German Sign Language",
    "GSW": "Swiss German",
    "GU": "Gujarati",
    "GUP": "Gunwinggu",
    "GUQ": "Aché",
    "HA": "Hausa",
    "HAI": "Haida",
    "HAK": "Hakka",
    "HAW": "Hawaiian",
    "HE": "Hebrew",
    "HI": "Hindi",
    "HMN": "Hmong",
    "HNE": "Chhattisgarhi",
    "HOC": "Ho",
    "HOP": "Hopi",
    "HR": "Croatian",
    "HT": "Haitian",
    "HU": "Hungarian",
    "HY": "Armenian",
    "IBA": "Iban",
    "ICL": "Icelandic Sign Language",
    "ID": "Indonesian",
    "IK": "Inupiaq",
    "INS": "Indian Sign Language",
    "IRU": "Irula",
    "IS": "Icelandic",
    "IT": "Italian",
    "IU": "Inuktitut",
    "JA": "Japanese",
    "JSL": "Japanese Sign Language",
    "KA": "Georgian",
    "KAB": "Kabyle",
    "KAR": "Karen",
    "KCA": "Khanty",
    "KEA": "Kabuverdianu",
    "KFA": "Kodava",
    "KGG": "Kusunda",
    "KHA": "Khasi",
    "KHE": "Korowai",
    "KI": "Kikuyu",
    "KK": "Kazakh",
    "KL": "Greenlandic",
    "KM": "Central Khmer",
    "KN": "Kannada",
    "KO": "Korean",
    "KOK": "Konkani",
    "KPJ": "Karajá",
    "KRO": "Kru",
    "KTZ": "Ju'hoan",
    "KU": "Kurdish",
    "KVK": "Korean Sign Language",
    "KW": "Cornish",
    "KWK": "Kwakiutl",
    "KY": "Kyrgyz",
    "KYW": "Kudmali",
    "LA": "Latin",
    "LAD": "Ladino",
    "LB": "Luxembourgish",
    "LBJ": "Ladakhi",
    "LIF": "Limbu",
    "LN": "Lingala",
    "LO": "Lao",
    "LT": "Lithuanian",
    "LUS": "Mizo",
    "LV": "Latvian",
    "MAG": "Magahi",
    "MAI": "Maithili",
    "MAN": "Mandingo",
    "MAS": "Masai",
    "MEN": "Mende",
    "MFE": "Morisyen",
    "MG": "Malagasy",
    "MH": "Marshallese",
    "MI": "Maori",
    "MIC": "Micmac",
    "MIN": "Minangkabau",
    "MJW": "Karbi",
    "MK": "Macedonian",
    "ML": "Malayalam",
    "MLS": "Masalit",
    "MN": "Mongolian",
    "MNC": "Manchu",
    "MNI": "Manipuri",
    "MOE": "Montagnais",
    "MOH": "Mohawk",
    "MR": "Marathi",
    "MS": "Malay",
    "MT": "Maltese",
    "MUS": "Creek",
    "MWL": "Mirandese",
    "MY": "Burmese",
    "MYN": "Maya",
    "MYP": "Pirahã",
    "NAH": "Nahuatl",
    "NAI": "North American Indian",
    "NAN": "Min Nan",
    "NAP": "Neapolitan",
    "NBF": "Naxi",
    "NCG": "Nisga'a",
    "ND": "Ndebele",
    "NDS": "Low German",
    "NE": "Nepali",
    "NL": "Dutch",
    "NMN": "Taa",
    "NO": "Norwegian",
    "NON": "Norse, Old",
    "NV": "Navajo",
    "NY": "Nyanja",
    "NYK": "Nyaneka",
    "OC": "Occitan",
    "OJ": "Ojibwa",
    "OR": "Oriya",
    "PA": "Punjabi",
    "PAP": "Papiamento",
    "PAW": "Pawnee",
    "PL": "Polish",
    "PQM": "Malecite-Passamaquoddy",
    "PRS": "Dari",
    "PS": "Pashtu",
    "PT": "Portuguese",
    "QAA": "Visayan",
    "QAB": "Hokkien",
    "QAC": "Aboriginal",
    "QAD": "Shanghainese",
    "QAE": "Saami",
    "QAF": "More",
    "QAG": "Ibo",
    "QAH": "Polynesian",
    "QAI": "Peul",
    "QAJ": "Parsee",
    "QAK": "Teochew",
    "QAM": "Acholi",
    "QAN": "Tigrigna",
    "QAO": "Ryukyuan",
    "QAP": "Malinka",
    "QAQ": "Kriolu",
    "QAR": "Kirundi",
    "QAS": "Aidoukrou",
    "QAT": "Ungwatsi",
    "QAU": "Shanxi",
    "QAV": "Hassanya",
    "QAW": "Djerma",
    "QAX": "Chaozhou",
    "QAY": "Scanian",
    "QAZ": "Ojihimba",
    "QBA": "Nama",
    "QBB": "Kuna",
    "QBC": "East-Greenlandic",
    "QBD": "Baka",
    "QBE": "Sousson",
    "QBF": "Kaado",
    "QBG": "Faliasch",
    "QBH": "Bodo",
    "QBI": "Bicolano",
    "QBJ": "Rawan",
    "QBK": "Nushi",
    "QBL": "Nagpuri",
    "QBM": "Macro-Jê",
    "QBN": "Flemish",
    "QBO": "Serbo-Croatian",
    "QMT": "Mixtec",
    "QSG": "Silbo Gomero",
    "QU": "Quechua",
    "QYA": "Quenya",
    "RAJ": "Rajasthani",
    "RM": "Romansh",
    "RO": "Romanian",
    "ROM": "Romany",
    "RSL": "Russian Sign Language",
    "RTM": "Rotuman",
    "RU": "Russian",
    "RW": "Kinyarwanda",
    "SA": "Sanskrit",
    "SAH": "Yakut",
    "SAT": "Santali",
    "SC": "Sardinian",
    "SCN": "Sicilian",
    "SD": "Sindhi",
    "SHH": "Shoshoni",
    "SHP": "Shipibo",
    "SI": "Sinhala",
    "SIO": "Sioux",
    "SJN": "Sindarin",
    "SK": "Slovak",
    "SL": "Slovenian",
    "SM": "Samoan",
    "SN": "Shona",
    "SNK": "Soninke",
    "SO": "Somali",
    "SON": "Songhay",
    "SQ": "Albanian",
    "SR": "Serbian",
    "SRN": "Sranan",
    "SRR": "Serer",
    "SSP": "Spanish Sign Language",
    "ST": "Sotho",
    "SV": "Swedish",
    "SW": "Swahili",
    "SYL": "Sylheti",
    "TA": "Tamil",
    "TAC": "Tarahumara",
    "TCY": "Tulu",
    "TE": "Telugu",
    "TG": "Tajik",
    "TH": "Thai",
    "TK": "Turkmen",
    "TL": "Tagalog",
    "TLH": "Klingon",
    "TLI": "Tlingit",
    "TMH": "Tamashek",
    "TN": "Tswana",
    "TO": "Tonga (Tonga Islands)",
    "TPI": "Tok Pisin",
    "TR": "Turkish",
    "TRP": "Kokborok",
    "TS": "Tsonga",
    "TSC": "Tswa",
    "TSZ": "Purepecha",
    "TT": "Tatar",
    "TUE": "Tuyuca",
    "TUP": "Tupi",
    "TYV": "Tuvinian",
    "TZO": "Tzotzil",
    "UK": "Ukrainian",
    "UKL": "Ukrainian Sign Language",
    "UR": "Urdu",
    "UZ": "Uzbek",
    "VI": "Vietnamese",
    "WAS": "Washoe",
    "WEN": "Sorbian languages",
    "WO": "Wolof",
    "XAL": "Kalmyk-Oirat",
    "XH": "Xhosa",
    "XRR": "Rhaetian",
    "YAP": "Yapese",
    "YI": "Yiddish",
    "YO": "Yoruba",
    "YPK": "Yupik",
    "YRK": "Nenets",
    "YUE": "Cantonese",
    "ZH": "Chinese",
    "ZU": "Zulu",
    "ZXX": "None",
}
