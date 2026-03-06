COURTS = {
    "Alice Marble": {
        "location_id": "81cd2b08-8ea6-40ee-8c89-aeba92506576",
        "slug": "rec.us/alicemarble",
        "courts": {
            1: {"court_sport_id": "e53f7248-230b-4faa-843c-eebb31062228"},
            2: {"court_sport_id": "1fd32d61-fecc-4835-a4d1-5663e8e590b2"},
            3: {"court_sport_id": "5218f07c-4901-4c7c-9401-8fc9a832c67e"},
            4: {"court_sport_id": "c6be859b-aae3-4bfe-97dd-4d151be5d2a1"},
        },
    },
    "Lafayette": {
        "location_id": "c4fc2b3e-d1bc-47d9-b920-76d00d32b20b",
        "slug": "rec.us/lafayette",
        "courts": {
            1: {"court_sport_id": "f8b17c05-0d01-4372-8f09-331fd293c2b2"},
            2: {"court_sport_id": "4a72386e-7513-4c52-bc58-8d5d971c7932"},
        },
    },
    "Moscone": {
        "location_id": "fb0d16b1-5f9f-465f-8ebf-fccf5d400c47",
        "slug": "rec.us/moscone",
        "courts": {
            1: {"court_sport_id": "3c3f9466-614d-48da-8757-d06595e1201a"},
            2: {"court_sport_id": "a3f0308b-75c8-498f-9bd4-d20fc0054dac"},
            3: {"court_sport_id": "02b11dc9-eeac-40df-a195-ab97a6ca43e9"},
            4: {"court_sport_id": "6eeb43f8-3c37-4397-a270-0e19bf97961e"},
        },
    },
}

TENNIS_LOGIN_URL = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key="
TENNIS_BASE_API_URL = "https://api.rec.us/v1"
TENNIS_2FAC_SEND_URL = "https://api.rec.us/v1/users/mobile-totp/send"
TENNIS_2FAC_VERIFY_URL = "https://api.rec.us/v1/users/mobile-totp/verify"