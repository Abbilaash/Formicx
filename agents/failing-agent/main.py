#!/usr/bin/env python3
import sys
import time

def main():
    print("Failing Agent started", flush=True)
    print("Simulating failure...", flush=True)
    time.sleep(0.3)
    sys.exit(1)

if __name__ == "__main__":
    main()
