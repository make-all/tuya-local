GPPH_HEATER_PAYLOAD = {
    "1": False,
    "2": 25,
    "3": 17,
    "4": "C",
    "6": True,
    "12": 0,
    "101": "5",
    "102": 0,
    "103": False,
    "104": True,
    "105": "auto",
    "106": 20,
}

GPCV_HEATER_PAYLOAD = {
    "1": True,
    "2": True,
    "3": 30,
    "4": 25,
    "5": 0,
    "6": 0,
    "7": "Low",
}

EUROM_600_HEATER_PAYLOAD = {"1": True, "2": 15, "5": 18, "6": 0}
EUROM_600v2_HEATER_PAYLOAD = {"1": True, "2": 15, "5": 18, "7": 0}

EUROM_601_HEATER_PAYLOAD = {"1": True, "2": 21, "3": 20, "6": False, "13": 0}

EUROM_WALLDESIGNHEAT2000_HEATER_PAYLOAD = {
    "1": True,
    "2": 21,
    "3": 19,
    "4": "off",
    "7": False,
}

EUROM_SANIWALLHEAT2000_HEATER_PAYLOAD = {
    "1": True,
    "2": 21,
    "3": 19,
    "4": "off",
    "7": False,
}

GECO_HEATER_PAYLOAD = {"1": True, "2": True, "3": 30, "4": 25, "5": 0, "6": 0}

JJPRO_JPD01_PAYLOAD = {
    "1": True,
    "2": "0",
    "4": 50,
    "5": True,
    "6": "1",
    "11": 0,
    "12": 0,
    "101": False,
    "102": False,
    "103": 20,
    "104": 62,
    "105": False,
}

KOGAN_HEATER_PAYLOAD = {"2": 30, "3": 25, "4": "Low", "6": True, "7": True, "8": 0}

KOGAN_KAWFHTP_HEATER_PAYLOAD = {
    "1": True,
    "2": True,
    "3": 30,
    "4": 25,
    "5": 0,
    "7": "Low",
}

KOGAN_KASHMFP20BA_HEATER_PAYLOAD = {
    "1": True,
    "2": "high",
    "3": 27,
    "4": 26,
    "5": "orange",
    "6": "white",
}

DEHUMIDIFIER_PAYLOAD = {
    "1": False,
    "2": "0",
    "4": 30,
    "5": False,
    "6": "1",
    "7": False,
    "11": 0,
    "12": "0",
    "101": False,
    "102": False,
    "103": 20,
    "104": 78,
    "105": False,
}

FAN_PAYLOAD = {"1": False, "2": "12", "3": "normal", "8": True, "11": "0", "101": False}

KOGAN_SOCKET_PAYLOAD = {
    "1": True,
    "2": 0,
    "4": 200,
    "5": 460,
    "6": 2300,
}

KOGAN_SOCKET_PAYLOAD2 = {
    "1": True,
    "9": 0,
    "18": 200,
    "19": 460,
    "20": 2300,
}

SMARTSWITCH_ENERGY_PAYLOAD = {
    "1": True,
    "9": 0,
    "17": 100,
    "18": 2368,
    "19": 4866,
    "20": 2148,
    "21": 1,
    "22": 628,
    "23": 30636,
    "24": 17426,
    "25": 2400,
    "26": 0,
    "38": "memory",
    "41": "",
    "42": "",
    "46": False,
}

KOGAN_SOCKET_CLEAR_PAYLOAD = {
    "2": None,
    "4": None,
    "5": None,
    "6": None,
    "9": None,
    "18": None,
    "19": None,
    "20": None,
}

GSH_HEATER_PAYLOAD = {
    "1": True,
    "2": 22,
    "3": 24,
    "4": "low",
    "12": 0,
}

GARDENPAC_HEATPUMP_PAYLOAD = {
    "1": True,
    "102": 28,
    "103": True,
    "104": 100,
    "105": "warm",
    "106": 30,
    "107": 18,
    "108": 45,
    "115": 0,
    "116": 0,
    "117": True,
}

IPS_HEATPUMP_PAYLOAD = {
    "1": True,
    "2": "silence",
    "102": 10,
    "103": True,
    "104": 100,
    "105": "warm",
    "106": 30,
    "107": 18,
    "108": 40,
    "115": 0,
    "116": 0,
}

MADIMACK_HEATPUMP_PAYLOAD = {
    "1": True,
    "102": 9,
    "103": True,
    "104": 0,
    "105": "warm",
    "106": 30,
    "107": 18,
    "108": 45,
    "115": 4,
    "116": 0,
    "117": True,
    "118": False,
    "120": 8,
    "122": 11,
    "124": 9,
    "125": 0,
    "126": 0,
    "127": 17,
    "128": 480,
    "129": 0,
    "130": False,
    "134": False,
    "135": False,
    "136": False,
    "139": False,
    "140": "LowSpeed",
}

MADIMACK_ELITEV3_HEATPUMP_PAYLOAD = {
    "1": True,
    "2": "heating",
    "4": 28,
    "5": "power",
    "6": "c",
    "15": 0,
    "20": 50,
    "21": 40,
    "22": 18,
    "23": 45,
    "24": 40,
    "25": 33,
    "26": 18,
    "101": 0,
    "102": 21,
    "103": 23,
    "104": 18,
    "105": 18,
    "106": 480,
    "107": False,
}

PURLINE_M100_HEATER_PAYLOAD = {
    "1": True,
    "2": 23,
    "3": 23,
    "5": "off",
    "10": True,
    "11": 0,
    "12": 0,
    "101": False,
    "102": False,
}

REMORA_HEATPUMP_PAYLOAD = {"1": True, "2": 30, "3": 28, "4": "heat", "9": 0}
BWT_HEATPUMP_PAYLOAD = {"1": True, "2": 30, "3": 28, "4": "auto", "9": 0}

EANONS_HUMIDIFIER_PAYLOAD = {
    "2": "middle",
    "3": "cancel",
    "4": 0,
    "9": 0,
    "10": True,
    "12": "humidity",
    "15": 65,
    "16": 65,
    "22": True,
}

INKBIRD_ITC306A_THERMOSTAT_PAYLOAD = {
    "12": 0,
    "101": "C",
    "102": 0,
    "103": "on",
    "104": 257,
    "106": 252,
    "108": 6,
    "109": 1000,
    "110": 0,
    "111": False,
    "112": False,
    "113": False,
    "114": 260,
    "115": True,
    "116": 783,
    "117": False,
    "118": False,
    "119": False,
    "120": False,
}

INKBIRD_ITC308_THERMOSTAT_PAYLOAD = {
    "12": 0,
    "101": "C",
    "102": 0,
    "104": 136,
    "106": 15,
    "108": 3,
    "109": 370,
    "110": 10,
    "111": False,
    "112": False,
    "113": False,
    "115": "1",
    "116": 565,
    "117": 10,
    "118": 5,
}

ANKO_FAN_PAYLOAD = {
    "1": True,
    "2": "normal",
    "3": "1",
    "4": "off",
    "6": "0",
}

DETA_FAN_PAYLOAD = {
    "1": True,
    "3": "1",
    "9": False,
    "101": True,
    "102": "0",
    "103": "0",
}

ELECTRIQ_DEHUMIDIFIER_PAYLOAD = {
    "1": True,
    "2": "auto",
    "3": 60,
    "4": 45,
    "7": False,
    "10": False,
    "102": "90",
    "103": 20,
    "104": False,
}

ELECTRIQ_CD20PRO_DEHUMIDIFIER_PAYLOAD = {
    "1": True,
    "2": "high",
    "3": 39,
    "4": 45,
    "5": False,
    "10": False,
    "101": False,
    "102": "0_90",
    "103": 30,
}

ELECTRIQ_CD12PW_DEHUMIDIFIER_PAYLOAD = {
    "1": True,
    "2": "high",
    "3": 39,
    "4": 45,
    "101": False,
    "103": 30,
}

ELECTRIQ_CD12PWV2_DEHUMIDIFIER_PAYLOAD = {
    "1": True,
    "2": 45,
    "5": "Smart",
    "6": 39,
    "19": 0,
    "101": True,
    "104": False,
}

ELECTRIQ_DESD9LW_DEHUMIDIFIER_PAYLOAD = {
    "1": True,
    "2": 50,
    "4": "Low",
    "5": "Dehumidity",
    "6": 55,
    "7": 18,
    "10": False,
    "12": False,
    "15": False,
    "101": 20,
}

POOLEX_SILVERLINE_HEATPUMP_PAYLOAD = {"1": True, "2": 30, "3": 28, "4": "Heat", "13": 0}
POOLEX_VERTIGO_HEATPUMP_PAYLOAD = {"1": True, "2": 30, "3": 28, "4": "heat", "9": 0}
POOLEX_QLINE_HEATPUMP_PAYLOAD = {"1": True, "2": "heating", "4": 30, "15": 0, "16": 28}

ELECTRIQ_12WMINV_HEATPUMP_PAYLOAD = {
    "1": True,
    "2": 20,
    "3": 18,
    "4": "auto",
    "5": "1",
    "8": False,
    "12": False,
    "101": True,
    "102": False,
    "103": False,
    "104": True,
    "106": False,
    "107": False,
    "108": 0,
    "109": 0,
    "110": 0,
}

KOGAN_DEHUMIDIFIER_PAYLOAD = {
    "1": True,
    "2": "low",
    "3": 70,
    "8": False,
    "11": 0,
    "12": 0,
    "13": 0,
    "101": 50,
}

HELLNAR_HEATPUMP_PAYLOAD = {
    "1": False,
    "2": 260,
    "3": 26,
    "4": "cold",
    "5": "low",
    "18": 0,
    "20": 0,
    "105": "off",
    "110": 131644,
    "113": "0",
    "114": "0",
    "119": "0",
    "120": "off",
    "123": "0010",
    "126": "0",
    "127": "0",
    "128": "0",
    "129": "1",
    "130": 26,
    "131": False,
    "132": False,
    "133": "0",
    "134": '{"t":1624086077,"s":false,"clr"true}',
}

TADIRAN_HEATPUMP_PAYLOAD = {
    "1": True,
    "2": 25,
    "3": 250,
    "4": "cooling",
    "5": "low",
    "101": 0,
    "102": 260,
    "103": 225,
    "104": "low",
    "105": "stop",
    "106": -300,
    "107": False,
    "108": False,
}

BECA_BHP6000_PAYLOAD = {
    "1": True,
    "2": 77,
    "3": 87,
    "4": "3",
    "5": "3",
    "6": False,
    "7": False,
}

BECA_BHT6000_PAYLOAD = {
    "1": False,
    "2": 40,
    "3": 42,
    "4": "0",
    "5": False,
    "6": False,
    "102": 0,
    "103": "1",
    "104": True,
}

BECA_BHT002_PAYLOAD = {
    "1": False,
    "2": 40,
    "3": 42,
    "4": "0",
    "5": False,
    "6": False,
    "102": 0,
    "104": True,
}

MOES_BHT002_PAYLOAD = {
    "1": False,
    "2": 40,
    "3": 42,
    "4": "0",
    "5": False,
    "6": False,
    "104": True,
}

BEOK_TR9B_PAYLOAD = {
    "1": True,
    "2": "manual",
    "10": True,
    "16": 590,
    "19": 990,
    "23": "f",
    "24": 666,
    "26": 410,
    "31": "5_2",
    "36": "close",
    "40": False,
    "45": 0,
    "101": 1313,
    "102": 10,
}

BECA_BAC002_PAYLOAD = {
    "1": True,
    "2": 39,
    "3": 45,
    "4": "1",
    "5": False,
    "6": False,
    "102": "1",
    "103": "2",
}

LEXY_F501_PAYLOAD = {
    "1": True,
    "2": "forestwindhigh",
    "4": "off",
    "6": 0,
    "9": False,
    "16": False,
    "17": False,
    "102": 8,
}

TH213_THERMOSTAT_PAYLOAD = {
    "1": True,
    "2": 18,
    "3": 20,
    "4": 1,
    "6": False,
    "12": 0,
    "101": 16,
    "102": 2,
    "103": 0,
    "104": 2,
    "105": True,
    "107": False,
    "108": False,
    "110": 0,
}

TH213V2_THERMOSTAT_PAYLOAD = {
    "1": True,
    "2": 16,
    "3": 21,
    "4": "3",
    "6": False,
    "12": 0,
    "101": 23,
    "102": "2",
    "103": 1,
    "104": 1,
    "105": False,
    "116": "1",
}

WETAIR_WCH750_HEATER_PAYLOAD = {
    "1": False,
    "2": 17,
    "4": "mod_free",
    "11": "heating",
    "19": "0h",
    "20": 0,
    "21": 0,
    "101": "level1",
}

WETAIR_WAWH1210_HUMIDIFIER_PAYLOAD = {
    "1": True,
    "5": True,
    "8": True,
    "13": 50,
    "14": 57,
    "22": 0,
    "24": "AUTO",
    "25": True,
    "29": False,
    "101": "Have_water",
}

SASWELL_T29UTK_THERMOSTAT_PAYLOAD = {
    "1": True,
    "2": 240,
    "3": 241,
    "4": "cold",
    "5": "auto",
    "19": "C",
    "101": False,
    "102": False,
    "103": "cold",
    "112": "3",
    "113": 0,
    "114": 24,
    "115": 24,
    "116": 75,
    "117": 81,
}

SASWELL_C16_THERMOSTAT_PAYLOAD = {
    "2": 220,
    "3": "Smart",
    "4": 0,
    "5": 217,
    "6": 350,
    "7": False,
    "8": 241,
    "9": False,
    "10": True,
    "11": False,
    "12": "7",
    "14": "0",
    "15": 0,
    "17": 0,
    "21": False,
    "22": 1500,
    "23": 12,
    "24": "Standby",
    "26": 50,
}

FERSK_VIND2_PAYLOAD = {
    "1": True,
    "2": 22,
    "3": 23,
    "4": "COOL",
    "5": 1,
    "19": "C",
    "101": False,
    "102": False,
    "103": 0,
    "104": False,
    "105": 0,
    "106": 0,
    "109": False,
    "110": 0,
}

KOGAN_GLASS_1_7L_KETTLE_PAYLOAD = {
    "1": False,
    "5": 99,
    #    "102": "90",
}

RENPHO_PURIFIER_PAYLOAD = {
    "1": True,
    "4": "low",
    "7": False,
    "8": False,
    "19": "0",
    "22": "0",
    "101": False,
    "102": 0,
    "103": 0,
    "104": 0,
    "105": 0,
}

ARLEC_FAN_PAYLOAD = {
    "1": True,
    "3": 1,
    "4": "forward",
    "102": "normal",
    "103": "off",
}

ARLEC_FAN_LIGHT_PAYLOAD = {
    "1": True,
    "3": "6",
    "4": "forward",
    "9": False,
    "10": 100,
    "11": 100,
    "102": "normal",
    "103": "off",
}

CARSON_CB_PAYLOAD = {
    "1": True,
    "2": 20,
    "3": 23,
    "4": "COOL",
    "5": 1,
    "19": "C",
    "102": False,
    "103": 0,
    "104": False,
    "105": 0,
    "106": 0,
    "110": 0,
}

KOGAN_KAWFPAC09YA_AIRCON_PAYLOAD = {
    "1": True,
    "2": 19,
    "3": 18,
    "4": "COOL",
    "5": "1",
    "19": "C",
    "105": 0,
    "106": 0,
    "107": False,
}

GRIDCONNECT_2SOCKET_PAYLOAD = {
    "1": True,
    "2": True,
    "9": 0,
    "10": 0,
    "17": 0,
    "18": 500,
    "19": 1200,
    "20": 240,
    "21": 0,
    "22": 0,
    "23": 0,
    "24": 0,
    "25": 0,
    "38": "0",
    "40": False,
    "101": True,
}

EBERG_QUBO_Q40HD_PAYLOAD = {
    "1": True,
    "2": 22,
    "3": 20,
    "4": "hot",
    "5": "middle",
    "19": "c",
    "22": 0,
    "25": False,
    "30": False,
    "101": "heat_s",
}

EBERG_COOLY_C35HD_PAYLOAD = {
    "1": True,
    "4": 0,
    "5": "4",
    "6": 25,
    "8": "1",
    "10": False,
    "13": 0,
    "14": 0,
    "15": 0,
    "16": False,
    "17": False,
    "18": 78,
    "19": False,
}

STIRLING_FS1_FAN_PAYLOAD = {
    "1": True,
    "2": "normal",
    "3": 9,
    "5": False,
    "22": "cancel",
}

QOTO_SPRINKLER_PAYLOAD = {
    "102": 100,
    "103": 100,
    "104": 10036,
    "105": 10800,
    "108": 0,
}

MINCO_MH1823D_THERMOSTAT_PAYLOAD = {
    "1": True,
    "2": "program",
    "3": "stop",
    "5": False,
    "9": True,
    "12": False,
    "18": "out",
    "19": "c",
    "22": 18,
    "23": 64,
    "32": 1,
    "33": 205,
    "35": 0,
    "37": 689,
    "39": "7",
    "45": 0,
    "101": 200,
    "102": 680,
    "103": 0,
    "104": 2,
    "105": "no_power",
    "106": 35,
    "107": 95,
}

SIMPLE_GARAGE_DOOR_PAYLOAD = {
    "1": True,
    "101": False,
}

NEDIS_HTPL20F_PAYLOAD = {
    "1": True,
    "2": 25,
    "3": 25,
    "4": "1",
    "7": False,
    "11": "0",
    "13": 0,
    "101": False,
}

ASPEN_ASP200_FAN_PAYLOAD = {
    "1": True,
    "2": "in",
    "3": 1,
    "8": 0,
    "18": 20,
    "19": 25,
    "101": True,
    "102": 3,
}

TMWF02_FAN_PAYLOAD = {
    "1": True,
    "2": 0,
    "3": "level_2",
    "4": 40,
}

TIMED_SOCKET_PAYLOAD = {
    "1": True,
    "11": 0,
}

TIMED_SOCKETV2_PAYLOAD = {
    "1": True,
    "9": 0,
}

DIGOO_DGSP202_SOCKET_PAYLOAD = {
    "1": True,
    "2": True,
    "9": 0,
    "10": 0,
    "18": 500,
    "19": 1200,
    "20": 240,
}

DIGOO_DGSP01_SOCKET_PAYLOAD = {
    "1": True,
    "27": True,
    "28": "colour",
    "29": 76,
    "31": "1c0d00001b640b",
    "32": "3855b40168ffff",
    "33": "ffff500100ff00",
    "34": "ffff8003ff000000ff000000ff000000000000000000",
    "35": "ffff5001ff0000",
    "36": "ffff0505ff000000ff00ffff00ff00ff0000ff000000",
}

WOOX_R4028_SOCKET_PAYLOAD = {
    "1": True,
    "2": True,
    "3": True,
    "7": True,
    "101": 0,
    "102": 0,
    "103": 0,
    "105": 0,
}

ES01_POWERSTRIP_PAYLOAD = {
    "1": True,
    "2": True,
    "3": True,
    "4": True,
    "5": 0,
    "6": 0,
    "7": 0,
    "8": 0,
}

OWON_PCT513_THERMOSTAT_PAYLOAD = {
    "2": "cool",
    "16": 2150,
    "17": 71,
    "23": "c",
    "24": 2950,
    "29": 85,
    "34": 52,
    "45": 0,
    "107": "0",
    "108": 2150,
    "109": 1650,
    "110": 71,
    "111": 62,
    "115": "auto",
    "116": "1",
    "119": True,
    "120": "permhold",
    "123": 25,
    "129": "coolfanon",
}

HYSEN_HY08WE2_THERMOSTAT_PAYLOAD = {
    "1": True,
    "2": 50,
    "3": 170,
    "4": "Manual",
    "6": False,
    "12": 0,
    "101": False,
    "102": False,
    "103": 170,
    "104": 4,
    "105": 15,
    "106": True,
    "107": True,
    "108": True,
    "109": -10,
    "110": 10,
    "111": 2,
    "112": 35,
    "113": 5,
    "114": 30,
    "115": 5,
    "116": "all",
    "117": "keep",
    "118": "2days",
}

POIEMA_ONE_PURIFIER_PAYLOAD = {
    "1": True,
    "2": 12,
    "3": "manual",
    "4": "mid",
    "7": False,
    "11": False,
    "18": "cancel",
    "19": 0,
}

ECOSTRAD_ACCENTIQ_HEATER_PAYLOAD = {
    "1": True,
    "2": 200,
    "3": 195,
    "10": 0,
    "101": True,
}

ECOSTRAD_IQCERAMIC_RADIATOR_PAYLOAD = {
    "1": True,
    "2": "hot",
    "16": 180,
    "24": 90,
    "27": 0,
    "40": False,
    "104": "15",
    "107": "1",
    "108": "0",
    "109": "0",
}

NASHONE_MTS700WB_THERMOSTAT_PAYLOAD = {
    "1": True,
    "2": "hot",
    "3": "manual",
    "16": 20,
    "17": 68,
    "23": "c",
    "24": 19,
    "27": 0,
    "29": 66,
    "39": False,
    "41": "cancel",
    "42": 0,
}

LEFANT_M213_VACUUM_PAYLOAD = {
    "1": True,
    "2": False,
    "3": "standby",
    "4": "forward",
    "5": "0",
    "6": 91,
    "13": False,
    "16": 0,
    "17": 0,
    "18": 0,
    "101": "nar",
    "102": -23,
    "103": 27,
    "104": 0,
    #   "106": "ChargeStage:DETSWITCGH",
    #    "108": "BatVol:13159",
}

KYVOL_E30_VACUUM_PAYLOAD = {
    "1": True,
    "2": False,
    "3": "standby",
    "4": "stop",
    "5": "Charging_Base",
    "6": 2,
    "7": 20,
    "8": 60,
    "9": 20,
    "10": False,
    "11": False,
    "12": False,
    "13": False,
    "14": "3",
    "16": 0,
    "17": 0,
    "18": 0,
    "101": "2",
    "102": "900234",
    "104": "standby",
    "107": 1,
}

HIMOX_H06_PURIFIER_PAYLOAD = {
    "1": True,
    "4": "low",
    "5": 50,
    "8": True,
    "11": False,
    "18": "cancel",
    "19": 0,
    "22": "medium",
    "101": "calcle",
}

HIMOX_H05_PURIFIER_PAYLOAD = {
    "1": True,
    "2": 21,
    "4": "auto",
    "5": 92,
    "7": False,
    "11": False,
    "18": "cancel",
    "21": "good",
}

VORK_VK6067_PURIFIER_PAYLOAD = {
    "1": True,
    "4": "auto",
    "5": 80,
    "8": True,
    "11": False,
    "18": "cancel",
    "19": 0,
    "21": "good",
    "22": 0,
}

KOGAN_GARAGE_DOOR_PAYLOAD = {
    "101": "fopen",
    "102": "opening",
    "104": 100,
    "105": True,
}

MOES_RGB_SOCKET_PAYLOAD = {
    "1": True,
    "2": "colour",
    "3": 255,
    "4": 14,
    "5": "ff99000024ffff",
    "6": "bd76000168ffff",
    "7": "ffff320100ff00",
    "8": "ffff3203ff000000ff000000ff",
    "9": "ffff3201ff0000",
    "10": "ffff3205ff000000ff00ffff00ff00ff0000ff",
    "101": True,
    "102": 0,
    "104": 0,
    "105": 0,
    "106": 2332,
}

LOGICOM_STRIPPY_PAYLOAD = {
    "1": False,
    "2": False,
    "3": False,
    "4": False,
    "5": False,
    "9": 0,
    "10": 0,
    "11": 0,
    "12": 0,
    "13": 0,
}

PARKSIDE_PLGS2012A1_PAYLOAD = {
    "1": True,
    "2": "test",
    "3": 1000,
    "4": 1320,
    "5": 80,
    "6": 25,
    "7": "standard",
    "8": False,
    "9": True,
    "10": 5,
    "11": 0,
    "101": 2500,
    "102": 11,
    "103": False,
    "104": False,
}

SD123_PRESENCE_PAYLOAD = {
    "1": "none",
    "101": "0_meters",
    "102": "6_meters",
    "103": "case_0",
    "104": "case_1",
    "105": "not_reset",
    "106": "normal",
    "107": 1200,
    "108": 1000,
    "109": 1,
    "110": 1,
    "111": 10,
    "112": 2,
    "113": 0,
    "114": True,
}

SIMPLE_BLINDS_PAYLOAD = {
    "1": "stop",
    "2": 0,
    "5": False,
    "7": "opening",
}

STARLIGHT_HEATPUMP_PAYLOAD = {
    "1": True,
    "2": 260,
    "3": 22,
    "4": "hot",
    "5": "auto",
    "18": 0,
    "20": 0,
    "105": "off",
    "110": 131644,
    "113": "0",
    "114": "0",
    "119": "0",
    "120": "off",
    "123": "0018",
    "126": "0",
    "127": "0",
    "128": "0",
    "129": "1",
    "130": 26,
    "131": False,
    "132": False,
    "133": "0",
    "134": '{"t":8601,"s":false,"clr":true}',
}

WILFA_HAZE_HUMIDIFIER_PAYLOAD = {
    "1": True,
    "5": False,
    "8": False,
    "10": 20,
    "13": 70,
    "14": 55,
    "16": False,
    "18": "c",
    "19": "cancel",
    "20": 0,
    "22": 0,
    "23": "level_3",
    "24": "humidity",
    "26": False,
    "35": False,
}

WEAU_POOL_HEATPUMP_PAYLOAD = {
    "1": True,
    "2": 33,
    "3": 195,
    "4": "auto",
    "6": 0,
}

WEAU_POOL_HEATPUMPV2_PAYLOAD = {
    "1": True,
    "2": "eheat",
    "9": 15,
    "10": 260,
    "20": 0,
    "101": 0,
    "102": 40,
    "103": 15,
    "104": True,
}

SMARTPLUG_ENCODED_PAYLOAD = {
    "1": True,
    "11": 0,
    "101": "QVA=",
    "102": "QVA=",
    "103": "QVA=",
}

DEVOLA_PATIO_HEATER_PAYLOAD = {
    "1": True,
    "2": 20,
    "3": 15,
    "4": "smart",
    "5": "4",
    "6": False,
    "7": False,
    "12": 0,
    "14": "heating",
    "19": "c",
    "20": 68,
    "21": 59,
}

QS_C01_CURTAIN_PAYLOAD = {
    "1": "stop",
    "2": 0,
    "8": "forward",
    "10": 20,
}

M027_CURTAIN_PAYLOAD = {
    "1": "close",
    "2": 0,
    "4": "morning",
    "7": "closing",
    "10": 0,
    "12": 0,
    "101": False,
}

JIAHONG_ET72W_PAYLOAD = {
    "101": True,
    "102": 220,
    "103": "Manual",
    "104": 0,
    "105": 205,
    "106": 240,
    "107": False,
    "108": False,
    "109": False,
    "110": 2,
    "111": "0",
    "112": 0,
    "113": 0,
    "116": 500,
    "117": 1234,
    "118": True,
    "121": 300,
}

BETTERLIFE_BL1500_PAYLOAD = {
    "1": True,
    "2": 20,
    "4": "0",
    "7": False,
    "11": "0",
    "12": 0,
}

EESEE_ADAM_PAYLOAD = {
    "1": True,
    "2": 50,
    "4": "manual",
    "5": "low",
    "14": False,
    "16": 72,
    "17": "cancel",
    "19": 0,
}

ALECOAIR_D14_PAYLOAD = {
    "1": True,
    "2": 50,
    "4": "manual",
    "5": "low",
    "10": False,
    "14": False,
    "16": 72,
    "17": "cancel",
    "19": 0,
}

HYUNDAI_SAHARA_PAYLOAD = {
    "1": True,
    "2": 50,
    "4": "high",
    "6": 73,
    "7": 25,
    "14": False,
    "16": False,
    "19": 0,
}

RGBCW_LIGHTBULB_PAYLOAD = {
    "20": True,
    "21": "white",
    "22": 1000,
    "23": 500,
    "24": "0000000003e8",
    "25": "000e0d0000000000000000c80000",
    "26": 0,
}

MOES_TEMP_HUMID_PAYLOAD = {
    "1": True,
    "2": False,
    "3": True,
    "4": "manual",
    "6": 374,
    "8": False,
    "9": 0,
    "11": False,
    "12": 0,
    "18": 0,
    "20": 0,
    "21": 0,
    "22": 0,
    "24": "",
    "101": "",
    "102": "",
    "103": 0,
    "104": 0,
    "105": "off",
    "106": "mix",
}

ORION_SMARTLOCK_PAYLOAD = {
    "1": 0,
    "2": 0,
    "3": 0,
    "4": 0,
    "5": 0,
    "8": 0,
    "9": 0,
    "10": False,
    "12": 100,
    "15": 0,
    "16": False,
}

ELECTRIQ_AIRFLEX15W_PAYLOAD = {
    "1": True,
    "2": 16,
    "3": 27,
    "17": 90,
    "20": 0,
    "101": "1",
    "103": False,
    "104": "1",
    "105": 0,
    "106": False,
    "109": False,
    "112": 42,
}

PC321TY_POWERCLAMP_PAYLOAD = {
    "101": 2284,
    "102": 1073,
    "103": 191,
    "104": 78,
    "106": 251,
    "111": 2354,
    "112": 748,
    "113": 47,
    "114": 100,
    "116": 267,
    "121": 2350,
    "122": 753,
    "123": 149,
    "124": 84,
    "126": 517,
    "131": 1036,
    "132": 2574,
    "133": 188,
    "135": 50,
    "136": 390,
}

ENERGY_POWERSTRIP_PAYLOAD = {
    "1": False,
    "2": False,
    "3": False,
    "4": False,
    "102": 0,
    "103": 0,
    "104": 2240,
    "105": 1,
    "106": 1709,
    "107": 34620,
    "108": 101000,
    "109": 205,
}

COMPTEUR_SMARTMETER_PAYLOAD = {
    "17": 12345,
    "18": 2000,
    "19": 4400,
    "20": 2200,
    "21": 0,
    "22": 0,
    "23": 0,
    "24": 0,
    "25": 0,
    "26": 0,
}

BECOOL_HEATPUMP_PAYLOAD = {
    "1": False,
    "4": 0,
    "5": "4",
    "6": 24,
    "8": "0",
    "10": False,
    "13": 0,
    "14": 0,
    "15": 0,
    "16": True,
    "17": False,
    "19": False,
}

ESSENTIALS_PURIFIER_PAYLOAD = {
    "1": True,
    "2": 12,
    "3": "auto",
    "5": 50,
    "7": False,
    "9": False,
    "11": False,
    "18": "cancel",
    "19": 0,
    "21": "good",
    "101": "Standard",
}

AVATTO_BLINDS_PAYLOAD = {
    "1": "close",
    "2": 0,
    "3": 0,
    "5": False,
    "7": "closing",
    "8": "cancel",
    "9": 0,
    "11": 0,
}

AVATTO_CURTAIN_PAYLOAD = {
    "1": "stop",
    "101": True,
}

ORION_SIREN_PAYLOAD = {
    "1": "normal",
    "5": "middle",
    "6": True,
    "7": 10,
    "15": 0,
    "20": True,
}

INKBIRD_SOUSVIDE_PAYLOAD = {
    "101": False,
    "102": "stop",
    "103": 0,
    "104": 297,
    "105": 0,
    "106": 0,
    "107": 3,
    "108": True,
    "109": 0,
    "110": 0,
}

HYDROTHERM_DYNAMICX8_PAYLOAD = {
    "1": True,
    "2": 65,
    "3": 60,
    "4": "STANDARD",
    "21": 0,
}

TREATLIFE_DS02F_PAYLOAD = {
    "1": True,
    "2": 0,
    "3": "level_2",
}

MOTION_LIGHT_PAYLOAD = {
    "101": "mode_auto",
    "102": False,
    "103": 0,
    "104": 249,
    "105": 374,
    "106": False,
}

BLITZWOLF_BWSH2_PAYLOAD = {
    "1": True,
    "3": "grade1",
    "6": "close",
    "19": "cancel",
}

BCOM_CAMERA_PAYLOAD = {
    "101": True,
    "103": False,
    "104": False,
    "106": "1",
    "108": "0",
    "109": "64GB",
    "110": 1,
    "111": False,
    "115": "",
    "117": 0,
    "136": "",
    "150": True,
    "151": "1",
    "162": False,
    "231": "",
    "232": False,
}

GX_AROMA_PAYLOAD = {
    "1": True,
    "2": "high",
    "3": "cancel",
    "4": 0,
    "5": True,
    "6": "colour",
    "8": "b9fff500ab46ff",
    "9": 0,
}

MOEBOT_PAYLOAD = {
    "6": 41,
    "101": "MOWING",
    "102": 0,
    "103": "MOWER_LEAN",
    "104": True,
    "105": 8,
    "106": 1343,
    "114": "AutoMode",
}

TOMPD63LW_SOCKET_PAYLOAD = {
    "1": 139470,
    "6": "CPQAFEkAAuk=",
    "9": 0,
    "11": False,
    "12": False,
    "13": 0,
    "16": True,
    "19": "FSE-F723C46A04FC6C",
    # "101": 275,
    # "102": 170,
    # "103": 40,
    # "104": 30,
    # "105": False,
    # "106": False,
}

GOLDAIR_GPDH340_PAYLOAD = {
    "1": True,
    "2": "2",
    "4": 60,
    "6": "2",
    "11": 0,
    "103": 20,
    "104": 72,
    "105": 40,
    "106": False,
    "107": True,
    "108": False,
    "109": False,
}

THERMEX_IF50V_PAYLOAD = {
    "101": False,
    "102": 37,
    "104": 65,
    "105": "2",
    "106": 0,
}

ZXG30_ALARM_PAYLOAD = {
    "1": "home",
    "2": 0,
    "3": 3,
    "4": True,
    "9": False,
    "10": False,
    "15": True,
    "16": 100,
    "17": True,
    "20": False,
    "21": False,
    "22": 1,
    "23": "2",
    "24": "Normal",
    "27": True,
    "28": 10,
    "29": True,
    "32": "normal",
    "34": False,
    "35": False,
    "36": "3",
    "37": "0",
    "39": "0",
    "40": "1",
}

IR_REMOTE_SENSORS_PAYLOAD = {
    "101": 200,
    "102": 80,
}

LORATAP_CURTAINSWITCH_PAYLOAD = {
    "1": "3",
}

BLE_WATERVALVE_PAYLOAD = {
    "1": True,
    "4": 0,
    "7": 50,
    "9": 3600,
    "10": "cancel",
    "12": "unknown",
    "15": 60,
}

AM25_ROLLERBLIND_PAYLOAD = {
    "1": "stop",
    "2": 0,
    "104": True,
    "105": True,
    "109": 4,
}

DUUX_BLIZZARD_PAYLOAD = {
    "1": False,
    "2": "fan",
    "3": "high",
    "4": 0,
    "6": False,
    "7": False,
    "8": 22,
    "9": 0,
    "11": 72,
    "12": True,
    "13": False,
    "14": False,
    "15": 0,
}

BLE_SMARTPLANT_PAYLOAD = {
    "3": 50,
    "5": 25,
    "9": "c",
    "14": "Low",
    "15": 20,
}
