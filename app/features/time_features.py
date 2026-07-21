from datetime import datetime, timezone
import pandas as pd
import math

def truncate(number, decimals=0):
    factor = 10 ** decimals
    return math.trunc(number * factor) / factor

def get_quarter_hour_slot(dt: datetime) -> int:
    return dt.hour * 4 + dt.minute // 15

def sin_cos_encoding_quarter_hour(q_hour: int) -> float:
    q_hour_mod = q_hour % 96
    hour_sin = truncate(math.sin(2 * math.pi * q_hour_mod / 96), 4)
    hour_cos = truncate(math.cos(2 * math.pi * q_hour_mod / 96), 4)
    return hour_sin, hour_cos

def get_next_3_hour_encoding() -> pd.DataFrame:
    utc_now = datetime.now(timezone.utc)
    utc_q_hour = get_quarter_hour_slot(utc_now)
    utc_encodings = [sin_cos_encoding_quarter_hour(x) for x in range(utc_q_hour, utc_q_hour + 12)]
    utc_df = pd.DataFrame(utc_encodings, columns=['time_sin', 'time_cos'])

    print(utc_df)

# Testing
if __name__ == "__main__":
    q_h_0 = get_quarter_hour_slot(datetime(2026, 7, 21, 0, 0))    # 0
    q_h_1 = get_quarter_hour_slot(datetime(2026, 7, 21, 0, 15))   # 1
    q_h_2 = get_quarter_hour_slot(datetime(2026, 7, 21, 0, 44))   # 2
    q_h_95 = get_quarter_hour_slot(datetime(2026, 7, 21, 23, 45)) # 95
    
    print(q_h_0)
    print(sin_cos_encoding_quarter_hour(q_h_0))
    print(q_h_1)
    print(sin_cos_encoding_quarter_hour(q_h_1))
    print(q_h_2)
    print(sin_cos_encoding_quarter_hour(q_h_2))
    print(q_h_95)
    print(sin_cos_encoding_quarter_hour(q_h_95))

    print(get_next_3_hour_encoding())