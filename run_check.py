import sys
from vie_alert_bot import main


if __name__ == "__main__":
    # Pass all CLI arguments to main()
    hourly = "--hourly" in sys.argv
    raise SystemExit(main(hourly=hourly))
