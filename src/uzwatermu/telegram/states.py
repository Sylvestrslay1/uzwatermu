from enum import StrEnum


class State(StrEnum):
    CHOOSING_LANGUAGE = "choosing_language"
    ENTERING_ACCOUNT = "entering_account"
    VERIFYING_PHONE = "verifying_phone"
    WAITING_METER_PHOTO = "waiting_meter_photo"
