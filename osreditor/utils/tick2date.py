from datetime import datetime, timedelta

def windows_ticks_to_datetime(ticks):
    """
    Convert Windows FILETIME ticks to a Python datetime object.
    """

    epoch_diff = 11644473600
    
    seconds = (ticks / 10**7) - epoch_diff
    print(f"Seconds since Unix epoch: {seconds}")
    
    return datetime.fromtimestamp(seconds)

def dotnet_ticks_to_datetime(ticks):
    """
    Convert .NET Ticks to a Python datetime object.
    """
    epoch_diff = 62135596800
    
    seconds = (ticks / 10**7) - epoch_diff
    
    return datetime.fromtimestamp(seconds)

if __name__ == "__main__":
    ticks = 639019018433118340
    dt = dotnet_ticks_to_datetime(ticks)
    print(dt.strftime('%Y-%m-%d %H:%M:%S'))
    s = dt.strftime('%Y%m%d%H%M%S')
    print(s[2:])